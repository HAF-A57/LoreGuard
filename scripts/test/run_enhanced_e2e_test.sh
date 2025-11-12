#!/bin/bash
# Enhanced E2E Test Runner
# 1. Apply v1 prompt templates
# 2. Apply v0.2 rubric
# 3. Activate new rubric
# 4. Run Brookings China E2E test with 40 artifacts
# 5. Analyze results

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get host IP
if [ -f ".env" ]; then
    source .env
fi

HOST_IP=${LOREGUARD_HOST_IP:-localhost}
API_URL="http://${HOST_IP}:8000"

echo -e "${CYAN}${BOLD}========================================${NC}"
echo -e "${CYAN}${BOLD}  LoreGuard Enhanced E2E Test Suite${NC}"
echo -e "${CYAN}${BOLD}========================================${NC}"
echo ""
echo -e "${BLUE}API URL:${NC} $API_URL"
echo -e "${BLUE}Test Artifacts:${NC} 40 documents from Brookings China"
echo -e "${BLUE}Enhancements:${NC} v1 prompts + v0.2 rubric"
echo ""

# Step 1: Check prerequisites
echo -e "${BOLD}[Step 1]${NC} Checking prerequisites..."

# Check if API is running
if ! curl -s -f "${API_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} API is not responding at ${API_URL}"
    echo -e "${YELLOW}Run: make quick-start${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} API is healthy"

# Check PostgreSQL connection
if ! psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Cannot connect to PostgreSQL"
    echo -e "${YELLOW}Check database status: docker ps | grep postgres${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} PostgreSQL is accessible"

echo ""

# Step 2: Apply v1 prompt templates
echo -e "${BOLD}[Step 2]${NC} Applying enhanced v1 prompt templates..."

PGPASSWORD=loreguard psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard \
    -f scripts/dev/init-prompt-templates-v1.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} v1 prompt templates applied"
    
    # Verify templates exist
    TEMPLATE_COUNT=$(PGPASSWORD=loreguard psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard \
        -t -c "SELECT COUNT(*) FROM prompt_templates WHERE version = 'v1';" 2>/dev/null | tr -d ' ')
    
    echo -e "  ${BLUE}ℹ${NC} Found ${TEMPLATE_COUNT} v1 templates"
else
    echo -e "${RED}✗${NC} Failed to apply v1 templates"
    exit 1
fi

echo ""

# Step 3: Apply v0.2 rubric
echo -e "${BOLD}[Step 3]${NC} Applying enhanced v0.2 rubric..."

PGPASSWORD=loreguard psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard \
    -f scripts/dev/init-rubric-v0.2.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} v0.2 rubric applied"
else
    echo -e "${RED}✗${NC} Failed to apply v0.2 rubric"
    exit 1
fi

echo ""

# Step 4: Activate v0.2 rubric
echo -e "${BOLD}[Step 4]${NC} Activating v0.2 rubric..."

# Get rubric ID
RUBRIC_ID=$(PGPASSWORD=loreguard psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard \
    -t -c "SELECT id FROM rubrics WHERE version = 'v0.2';" 2>/dev/null | tr -d ' ')

if [ -z "$RUBRIC_ID" ] || [ "$RUBRIC_ID" == "" ]; then
    echo -e "${RED}✗${NC} Could not find rubric v0.2"
    exit 1
fi

# Activate via API
ACTIVATE_RESPONSE=$(curl -s -X PUT "${API_URL}/api/v1/rubrics/${RUBRIC_ID}/activate")
ACTIVE_VERSION=$(echo $ACTIVATE_RESPONSE | jq -r '.version' 2>/dev/null)

if [ "$ACTIVE_VERSION" == "v0.2" ]; then
    echo -e "${GREEN}✓${NC} Rubric v0.2 activated"
    echo -e "  ${BLUE}ℹ${NC} Rubric ID: ${RUBRIC_ID}"
else
    echo -e "${RED}✗${NC} Failed to activate rubric v0.2"
    echo -e "${YELLOW}Response: ${ACTIVATE_RESPONSE}${NC}"
    exit 1
fi

echo ""

# Step 5: Verify configuration
echo -e "${BOLD}[Step 5]${NC} Verifying configuration..."

# Check active rubric
ACTIVE_RUBRIC=$(curl -s "${API_URL}/api/v1/rubrics/active" | jq -r '.version' 2>/dev/null)
if [ "$ACTIVE_RUBRIC" == "v0.2" ]; then
    echo -e "${GREEN}✓${NC} Active rubric: v0.2"
else
    echo -e "${RED}✗${NC} Active rubric is not v0.2 (found: ${ACTIVE_RUBRIC})"
    exit 1
fi

# Check LLM provider
PROVIDER_STATUS=$(curl -s "${API_URL}/api/v1/llm-providers/default/active" | jq -r '.status' 2>/dev/null)
PROVIDER_NAME=$(curl -s "${API_URL}/api/v1/llm-providers/default/active" | jq -r '.name' 2>/dev/null)

if [ "$PROVIDER_STATUS" == "active" ]; then
    echo -e "${GREEN}✓${NC} LLM provider active: ${PROVIDER_NAME}"
else
    echo -e "${RED}✗${NC} No active LLM provider found"
    echo -e "${YELLOW}Configure via frontend Settings page${NC}"
    exit 1
fi

# Check prompt templates
EVAL_PROMPT=$(PGPASSWORD=loreguard psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard \
    -t -c "SELECT reference_id FROM prompt_templates WHERE reference_id = 'prompt_ref_eval_v1' AND is_active = true;" 2>/dev/null | tr -d ' ')

if [ "$EVAL_PROMPT" == "prompt_ref_eval_v1" ]; then
    echo -e "${GREEN}✓${NC} Evaluation prompt v1 is active"
else
    echo -e "${RED}✗${NC} Evaluation prompt v1 is not active"
    exit 1
fi

echo ""

# Step 6: Display rubric details
echo -e "${BOLD}[Step 6]${NC} Rubric v0.2 Configuration:"
echo ""
echo -e "${BLUE}Categories:${NC}"
echo -e "  • Credibility (30%): Author expertise, org reputation, venue rigor, corroboration"
echo -e "  • Relevance (30%): Wargaming utility, doctrinal alignment, scenario fit, perspective value"
echo -e "  • Rigor (15%): Methodology, evidence quality, transparency, analytical depth"
echo -e "  • Timeliness (10%): Recency, currency, update frequency, temporal decay"
echo -e "  • Novelty (10%): Originality, unique perspective, info advantage, intellectual value"
echo -e "  • Coverage (5%): Completeness, clarity, usability, structure"
echo ""
echo -e "${BLUE}Thresholds:${NC}"
echo -e "  • Signal: ≥ 3.8 (auto-promote to Library)"
echo -e "  • Review: 2.8 - 3.8 (human analyst review)"
echo -e "  • Noise: < 2.8 (filter out)"
echo ""
echo -e "${BLUE}Enhancements:${NC}"
echo -e "  ✓ Explicit subcriteria for each category"
echo -e "  ✓ Few-shot examples in evaluation prompt"
echo -e "  ✓ Edge case handling (propaganda, opinion pieces, technical docs)"
echo -e "  ✓ Confidence calibration guidance"
echo -e "  ✓ Adversary perspective assessment"
echo -e "  ✓ Think tank credibility verification"
echo ""

# Step 7: Run E2E test
echo -e "${BOLD}[Step 7]${NC} Running E2E test with 40 artifacts..."
echo ""
echo -e "${YELLOW}This will take approximately 15-20 minutes:${NC}"
echo -e "  • Crawling: ~5 minutes"
echo -e "  • Normalization: ~3 minutes"
echo -e "  • Evaluation: ~10-12 minutes (40 artifacts × 15-20 sec each)"
echo ""
echo -e "${BOLD}Press Enter to continue or Ctrl+C to cancel...${NC}"
read

# Run Python E2E test
python3 scripts/test/brookings_china_e2e.py --max-artifacts 40

# Capture exit code
TEST_EXIT_CODE=$?

echo ""

# Step 8: Post-test analysis
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${CYAN}${BOLD}========================================${NC}"
    echo -e "${CYAN}${BOLD}  Post-Test Analysis${NC}"
    echo -e "${CYAN}${BOLD}========================================${NC}"
    echo ""
    
    # Get evaluation statistics
    echo -e "${BOLD}Evaluation Statistics:${NC}"
    echo ""
    
    SIGNAL_COUNT=$(PGPASSWORD=loreguard psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard \
        -t -c "SELECT COUNT(*) FROM evaluations WHERE label = 'Signal' AND rubric_version = 'v0.2';" 2>/dev/null | tr -d ' ')
    
    REVIEW_COUNT=$(PGPASSWORD=loreguard psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard \
        -t -c "SELECT COUNT(*) FROM evaluations WHERE label = 'Review' AND rubric_version = 'v0.2';" 2>/dev/null | tr -d ' ')
    
    NOISE_COUNT=$(PGPASSWORD=loreguard psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard \
        -t -c "SELECT COUNT(*) FROM evaluations WHERE label = 'Noise' AND rubric_version = 'v0.2';" 2>/dev/null | tr -d ' ')
    
    TOTAL_EVALS=$((SIGNAL_COUNT + REVIEW_COUNT + NOISE_COUNT))
    
    if [ $TOTAL_EVALS -gt 0 ]; then
        SIGNAL_PCT=$((SIGNAL_COUNT * 100 / TOTAL_EVALS))
        REVIEW_PCT=$((REVIEW_COUNT * 100 / TOTAL_EVALS))
        NOISE_PCT=$((NOISE_COUNT * 100 / TOTAL_EVALS))
        
        echo -e "${GREEN}Signal:${NC} ${SIGNAL_COUNT} documents (${SIGNAL_PCT}%)"
        echo -e "${YELLOW}Review:${NC} ${REVIEW_COUNT} documents (${REVIEW_PCT}%)"
        echo -e "${RED}Noise:${NC} ${NOISE_COUNT} documents (${NOISE_PCT}%)"
        echo -e "${BLUE}Total:${NC} ${TOTAL_EVALS} evaluations"
        echo ""
        
        # Get average scores
        AVG_TOTAL=$(PGPASSWORD=loreguard psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard \
            -t -c "SELECT ROUND(AVG((scores->>'total_score')::numeric), 2) FROM evaluations WHERE rubric_version = 'v0.2';" 2>/dev/null | tr -d ' ')
        
        AVG_CONFIDENCE=$(PGPASSWORD=loreguard psql -h ${HOST_IP} -p 5432 -U loreguard -d loreguard \
            -t -c "SELECT ROUND(AVG(confidence::numeric), 2) FROM evaluations WHERE rubric_version = 'v0.2';" 2>/dev/null | tr -d ' ')
        
        echo -e "${BOLD}Quality Metrics:${NC}"
        echo -e "${BLUE}Average Score:${NC} ${AVG_TOTAL}/5.0"
        echo -e "${BLUE}Average Confidence:${NC} ${AVG_CONFIDENCE}"
        echo ""
    fi
    
    echo -e "${GREEN}${BOLD}✅ E2E TEST COMPLETED SUCCESSFULLY${NC}"
    echo ""
    echo -e "${BOLD}Next Steps:${NC}"
    echo -e "  1. Review evaluation results in frontend: http://${HOST_IP}:6060"
    echo -e "  2. Check category scoring distribution in Evaluations page"
    echo -e "  3. Verify justifications are detailed and specific"
    echo -e "  4. Review Signal artifacts in Library page"
    echo ""
else
    echo -e "${RED}${BOLD}✗ E2E TEST FAILED${NC}"
    echo -e "${YELLOW}Check logs for details${NC}"
    exit $TEST_EXIT_CODE
fi

