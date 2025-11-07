#!/usr/bin/env python3
"""
LoreGuard E2E Test - Brookings China Source
Enhanced version with comprehensive monitoring and debugging

Tests complete pipeline:
1. Create Brookings China source
2. Trigger web crawl (limit: 10 artifacts)
3. Monitor ingestion job with detailed process info
4. Wait for artifact normalization
5. Trigger LLM evaluation
6. Display Signal/Review/Noise results with full breakdown

Usage:
    python scripts/test/brookings_china_e2e.py [--api-url <url>] [--skip-crawl] [--source-id <id>]
"""

import os
import sys
import json
import time
import argparse
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Color output for terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_step(step_num: int, message: str):
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}[Step {step_num}]{Colors.ENDC} {Colors.BOLD}{message}{Colors.ENDC}")

def print_success(message: str):
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {message}")

def print_error(message: str):
    print(f"{Colors.FAIL}✗{Colors.ENDC} {message}")

def print_warning(message: str):
    print(f"{Colors.WARNING}⚠{Colors.ENDC} {message}")

def print_info(message: str):
    print(f"{Colors.OKBLUE}ℹ{Colors.ENDC} {message}")

def get_api_url() -> str:
    """Get API URL from environment or use default"""
    host_ip = os.getenv('LOREGUARD_HOST_IP', 'localhost')
    return f"http://{host_ip}:8000"

def check_health(api_url: str) -> bool:
    """Check API health"""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"API service is healthy: {data.get('service', 'unknown')}")
            return True
        else:
            print_error(f"API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to connect to API: {e}")
        return False

def verify_prerequisites(api_url: str) -> tuple[Optional[Dict], Optional[Dict]]:
    """Verify active rubric and LLM provider exist"""
    
    # Check rubric
    print_info("Checking for active rubric...")
    try:
        response = requests.get(f"{api_url}/api/v1/rubrics/active", timeout=5)
        if response.status_code == 200:
            rubric = response.json()
            version = rubric.get('version', 'unknown')
            categories = rubric.get('categories', {})
            category_count = len(categories) if isinstance(categories, dict) else len(categories)
            print_success(f"Active rubric: {version} ({category_count} categories)")
            
            thresholds = rubric.get('thresholds', {})
            print_info(f"  Signal threshold: ≥ {thresholds.get('signal_min', 'N/A')}")
            print_info(f"  Review threshold: ≥ {thresholds.get('review_min', 'N/A')}")
        else:
            print_error(f"No active rubric found")
            return None, None
    except Exception as e:
        print_error(f"Failed to check rubric: {e}")
        return None, None
    
    # Check LLM provider
    print_info("Checking for active LLM provider...")
    try:
        response = requests.get(f"{api_url}/api/v1/llm-providers/default/active", timeout=5)
        if response.status_code == 200:
            provider = response.json()
            print_success(f"Active LLM provider: {provider.get('name', 'unknown')}")
            print_info(f"  Provider: {provider.get('provider', 'unknown')}")
            print_info(f"  Model: {provider.get('model', 'unknown')}")
            print_info(f"  Status: {provider.get('status', 'unknown')}")
        else:
            print_error(f"No active LLM provider found")
            return rubric, None
    except Exception as e:
        print_error(f"Failed to check provider: {e}")
        return rubric, None
    
    return rubric, provider

def create_brookings_source(api_url: str, max_artifacts: int = 10) -> Optional[str]:
    """Create Brookings China source with proper configuration"""
    source_config = {
        "name": "Brookings Institution - China & Asia-Pacific (E2E Test)",
        "type": "web",
        "status": "active",
        "config": {
            "start_urls": ["https://www.brookings.edu/regions/asia-the-pacific/china"],
            "crawl_scope": {
                "max_depth": 2,
                "max_artifacts": max_artifacts,
                "max_pages_per_domain": 50,
                "max_crawl_time_minutes": 15
            },
            "filtering": {
                "allowed_domains": ["brookings.edu", "www.brookings.edu"],
                "allowed_file_types": ["text/html", "application/pdf"],
                "max_file_size_mb": 50
            },
            "politeness": {
                "download_delay": 2.0,
                "concurrent_requests_per_domain": 1,
                "autothrottle_enabled": True,
                "autothrottle_start_delay": 1.0
            },
            "compliance": {
                "obey_robots_txt": True
            },
            "extraction": {
                "extract_pdfs": True,
                "extract_metadata": True,
                "min_content_length": 100
            }
        }
    }
    
    print_info("Creating Brookings China source...")
    print_info(f"  URL: {source_config['config']['start_urls'][0]}")
    print_info(f"  Max artifacts: {max_artifacts}")
    print_info(f"  Max depth: {source_config['config']['crawl_scope']['max_depth']}")
    print_info(f"  Download delay: {source_config['config']['politeness']['download_delay']}s")
    
    try:
        response = requests.post(
            f"{api_url}/api/v1/sources/",
            json=source_config,
            timeout=10
        )
        if response.status_code == 200:
            source = response.json()
            source_id = source.get('id')
            print_success(f"Source created: {source_id}")
            return source_id
        else:
            print_error(f"Failed to create source: HTTP {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return None
    except Exception as e:
        print_error(f"Error creating source: {e}")
        return None

def trigger_crawl(api_url: str, source_id: str) -> Optional[str]:
    """Trigger crawl for a source"""
    try:
        print_info(f"Triggering crawl for source {source_id}...")
        response = requests.post(
            f"{api_url}/api/v1/sources/{source_id}/trigger",
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            job_id = data.get('job_id')
            print_success(f"Crawl job started: {job_id}")
            print_info(f"  Spider: {data.get('spider_name', 'unknown')}")
            print_info(f"  Process ID: {data.get('process_id', 'unknown')}")
            print_info(f"  Status: {data.get('status', 'unknown')}")
            return job_id
        else:
            print_error(f"Failed to trigger crawl: HTTP {response.status_code}")
            print_error(f"Response: {response.text[:800]}")
            return None
    except Exception as e:
        print_error(f"Error triggering crawl: {e}")
        import traceback
        traceback.print_exc()
        return None

def monitor_job(api_url: str, job_id: str, timeout: int = 900) -> bool:
    """Monitor job with enhanced process monitoring"""
    print_info(f"Monitoring job {job_id[:8]}... (timeout: {timeout}s)")
    start_time = time.time()
    last_status = None
    check_count = 0
    
    while time.time() - start_time < timeout:
        check_count += 1
        elapsed = time.time() - start_time
        
        try:
            response = requests.get(
                f"{api_url}/api/v1/jobs/{job_id}?include_process_info=true",
                timeout=5
            )
            if response.status_code == 200:
                job = response.json()
                status = job.get('status', 'unknown')
                
                # Print status changes
                if status != last_status:
                    print_info(f"[{elapsed:.1f}s] Status: {status}")
                    last_status = status
                
                # Show process info every 30 seconds
                if check_count % 6 == 0 and job.get('process_running'):
                    process_info = job.get('process_info', {})
                    print_info(f"  Process: CPU {process_info.get('cpu_percent', 0):.1f}%, "
                             f"Memory {process_info.get('memory_mb', 0):.1f}MB, "
                             f"Runtime {process_info.get('runtime_seconds', 0):.0f}s")
                
                # Check for warnings
                if job.get('is_hanging'):
                    print_warning(f"Job hanging: {job.get('hanging_reason', 'Unknown')}")
                
                # Check terminal statuses
                if status in ['completed', 'failed', 'cancelled', 'timeout', 'hanging']:
                    if status == 'completed':
                        duration = time.time() - start_time
                        print_success(f"Job completed in {duration:.1f}s!")
                        
                        # Show timeline
                        timeline = job.get('timeline', [])
                        if timeline and len(timeline) > 1:
                            print_info("Job timeline:")
                            for entry in timeline[-5:]:
                                msg = entry.get('message', 'No message')
                                print_info(f"  • {entry.get('status')}: {msg}")
                        
                        return True
                    else:
                        print_error(f"Job ended with status: {status}")
                        if job.get('error'):
                            print_error(f"Error: {job.get('error')}")
                        
                        # Show timeline for debugging
                        timeline = job.get('timeline', [])
                        if timeline:
                            print_info("Job timeline (last 5 entries):")
                            for entry in timeline[-5:]:
                                print_info(f"  • {entry.get('status')}: {entry.get('message', 'No message')}")
                        
                        return False
            else:
                if check_count % 12 == 0:  # Every minute
                    print_warning(f"Failed to get job status: HTTP {response.status_code}")
        except Exception as e:
            if check_count % 12 == 0:  # Every minute
                print_warning(f"Error checking job: {e}")
        
        time.sleep(5)
    
    print_error(f"Job monitoring timed out after {timeout}s")
    return False

def get_source_artifacts(api_url: str, source_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get artifacts from a specific source"""
    try:
        url = f"{api_url}/api/v1/artifacts/?limit={limit}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            all_artifacts = data.get('items', [])
            
            # Filter by source_id
            artifacts = [a for a in all_artifacts if str(a.get('source_id', '')) == str(source_id)]
            
            if artifacts:
                print_success(f"Found {len(artifacts)} artifacts from source")
                
                # Show sample artifacts
                for i, artifact in enumerate(artifacts[:3], 1):
                    uri = artifact.get('uri', 'No URI')
                    print_info(f"  {i}. {uri[:75]}")
                
                if len(artifacts) > 3:
                    print_info(f"  ... and {len(artifacts) - 3} more")
            else:
                print_warning(f"No artifacts found for source {source_id}")
            
            return artifacts
        else:
            print_error(f"Failed to get artifacts: HTTP {response.status_code}")
            return []
    except Exception as e:
        print_error(f"Error getting artifacts: {e}")
        return []

def wait_for_normalization(api_url: str, artifacts: List[Dict[str, Any]], timeout: int = 900) -> List[Dict[str, Any]]:
    """Wait for artifacts to be normalized with progress tracking"""
    print_info(f"Waiting for normalization (timeout: {timeout}s)...")
    start_time = time.time()
    normalized = []
    
    artifact_ids = [a.get('id') for a in artifacts]
    total = len(artifact_ids)
    last_count = 0
    
    while time.time() - start_time < timeout and len(normalized) < total:
        for artifact_id in artifact_ids:
            if artifact_id in [a.get('id') for a in normalized]:
                continue
            
            try:
                response = requests.get(
                    f"{api_url}/api/v1/artifacts/{artifact_id}",
                    timeout=5
                )
                if response.status_code == 200:
                    artifact = response.json()
                    if artifact.get('normalized_ref'):
                        normalized.append(artifact)
                        
                        # Show progress
                        print_success(f"[{len(normalized)}/{total}] Artifact {artifact_id[:8]}... normalized")
                        
                        # Show metadata if available
                        metadata = artifact.get('document_metadata')
                        if metadata and metadata.get('title'):
                            title = metadata.get('title', '')[:60]
                            print_info(f"       Title: {title}")
            except Exception:
                pass
        
        # Progress update every 30 seconds if no new normalizations
        if len(normalized) < total:
            if len(normalized) != last_count:
                last_count = len(normalized)
            else:
                elapsed = time.time() - start_time
                if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                    remaining = total - len(normalized)
                    print_info(f"[{elapsed:.0f}s] Waiting... {remaining} artifacts remaining")
            
            time.sleep(10)
    
    elapsed = time.time() - start_time
    if len(normalized) == total:
        print_success(f"All {len(normalized)} artifacts normalized in {elapsed:.1f}s!")
    else:
        print_warning(f"Only {len(normalized)}/{total} artifacts normalized after {elapsed:.1f}s")
    
    return normalized

def trigger_evaluation(api_url: str, artifact_id: str, artifact_uri: str = "unknown") -> Optional[Dict[str, Any]]:
    """Trigger evaluation for an artifact"""
    try:
        response = requests.post(
            f"{api_url}/api/v1/artifacts/{artifact_id}/evaluate",
            timeout=180  # 3 minutes for LLM evaluation
        )
        if response.status_code == 200:
            return response.json()
        else:
            error_text = response.text[:500] if hasattr(response, 'text') else "No error"
            print_error(f"Evaluation failed (HTTP {response.status_code})")
            print_error(f"  Artifact: {artifact_uri[:60]}")
            print_error(f"  Error: {error_text}")
            return None
    except requests.exceptions.Timeout:
        print_error(f"Evaluation timed out (artifact: {artifact_uri[:60]})")
        return None
    except Exception as e:
        print_error(f"Error triggering evaluation: {e}")
        return None

def display_results(evaluations: List[Dict[str, Any]], artifacts: List[Dict[str, Any]]):
    """Display comprehensive evaluation results"""
    print_header("EVALUATION RESULTS")
    
    if not evaluations:
        print_error("No evaluation results to display")
        return
    
    signal_count = sum(1 for e in evaluations if e.get('label') == 'Signal')
    review_count = sum(1 for e in evaluations if e.get('label') == 'Review')
    noise_count = sum(1 for e in evaluations if e.get('label') == 'Noise')
    
    # Calculate average scores
    avg_score = sum(e.get('total_score', 0) for e in evaluations) / len(evaluations)
    avg_confidence = sum(float(e.get('confidence', 0)) for e in evaluations) / len(evaluations)
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  Total Evaluated: {len(evaluations)}")
    print(f"  {Colors.OKGREEN}Signal: {signal_count} ({signal_count/len(evaluations)*100:.1f}%){Colors.ENDC}")
    print(f"  {Colors.WARNING}Review: {review_count} ({review_count/len(evaluations)*100:.1f}%){Colors.ENDC}")
    print(f"  {Colors.FAIL}Noise: {noise_count} ({noise_count/len(evaluations)*100:.1f}%){Colors.ENDC}")
    print(f"  Average Score: {avg_score:.2f}/5.0")
    print(f"  Average Confidence: {avg_confidence*100:.1f}%")
    
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.ENDC}\n")
    
    # Create artifact lookup
    artifact_map = {a.get('id'): a for a in artifacts}
    
    # Sort by score descending
    sorted_evals = sorted(evaluations, key=lambda e: e.get('total_score', 0), reverse=True)
    
    for i, eval_result in enumerate(sorted_evals, 1):
        label = eval_result.get('label', 'Unknown')
        total_score = eval_result.get('total_score', 0)
        confidence = eval_result.get('confidence', 0)
        artifact_id = eval_result.get('artifact_id', 'unknown')
        model_used = eval_result.get('model_used', 'unknown')
        rubric_version = eval_result.get('rubric_version', 'unknown')
        
        # Get artifact details
        artifact = artifact_map.get(artifact_id, {})
        uri = artifact.get('uri', 'Unknown URI')
        metadata = artifact.get('document_metadata', {})
        title = metadata.get('title', 'No title') if metadata else 'No title'
        authors = metadata.get('authors', []) if metadata else []
        organization = metadata.get('organization', 'Unknown') if metadata else 'Unknown'
        
        # Color and icon based on label
        if label == 'Signal':
            color = Colors.OKGREEN
            icon = "🔔"
        elif label == 'Review':
            color = Colors.WARNING
            icon = "📋"
        else:
            color = Colors.FAIL
            icon = "🔇"
        
        print(f"{color}{Colors.BOLD}[{i}] {icon} {label}{Colors.ENDC}")
        print(f"  Title: {title[:70]}")
        if authors and len(authors) > 0:
            print(f"  Authors: {', '.join(authors[:2])}")
        print(f"  Organization: {organization}")
        print(f"  URI: {uri[:75]}")
        print(f"  {Colors.BOLD}Total Score: {total_score:.2f}/5.0{Colors.ENDC}")
        if confidence:
            print(f"  Confidence: {float(confidence)*100:.1f}%")
        print(f"  Model: {model_used}")
        print(f"  Rubric: {rubric_version}")
        
        # Show category scores
        scores = eval_result.get('scores', {})
        if scores:
            print(f"  Category Scores:")
            for category, score_data in sorted(scores.items()):
                if isinstance(score_data, dict):
                    score = score_data.get('score', 0)
                    reasoning = score_data.get('reasoning', '')
                    print(f"    • {category}: {score:.2f}/5.0")
                    if reasoning:
                        # Truncate reasoning
                        reasoning_short = reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
                        print(f"      └─ {reasoning_short}")
                else:
                    print(f"    • {category}: {score_data:.2f}/5.0")
        
        print()

def check_services(api_url: str):
    """Check individual service health"""
    print_info("Checking service health...")
    
    # Check normalize service
    try:
        host_ip = os.getenv('LOREGUARD_HOST_IP', 'localhost')
        normalize_url = f"http://{host_ip}:8001/health"
        response = requests.get(normalize_url, timeout=5)
        if response.status_code in [200, 503]:
            print_success(f"Normalize service responding (HTTP {response.status_code})")
        else:
            print_warning(f"Normalize service returned HTTP {response.status_code}")
    except Exception as e:
        print_warning(f"Normalize service check failed: {e}")

def main():
    parser = argparse.ArgumentParser(description='LoreGuard E2E Test - Brookings China')
    parser.add_argument('--api-url', help='API base URL', default=None)
    parser.add_argument('--max-artifacts', type=int, default=10, help='Maximum artifacts to crawl')
    parser.add_argument('--skip-crawl', action='store_true', help='Skip crawl, use existing artifacts')
    parser.add_argument('--source-id', help='Use existing source ID instead of creating new one')
    args = parser.parse_args()
    
    api_url = args.api_url or get_api_url()
    
    print_header("LOREGUARD E2E TEST - BROOKINGS CHINA & ASIA-PACIFIC")
    print_info(f"API URL: {api_url}")
    print_info(f"Max Artifacts: {args.max_artifacts}")
    print_info(f"Test Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 0: Check services
    check_services(api_url)
    
    # Step 1: Health check
    print_step(1, "API Health Check")
    if not check_health(api_url):
        print_error("❌ API health check failed")
        print_info("Run: bash scripts/dev/start-services.sh")
        sys.exit(1)
    
    # Step 2: Verify prerequisites
    print_step(2, "Verifying Prerequisites")
    rubric, provider = verify_prerequisites(api_url)
    if not rubric:
        print_error("❌ No active rubric found")
        print_info("Run: bash scripts/dev/init-databases.sh")
        sys.exit(1)
    if not provider:
        print_error("❌ No active LLM provider found")
        print_info("Configure provider via frontend Settings or API")
        sys.exit(1)
    
    # Step 3: Create or use source
    source_id = args.source_id
    if not source_id:
        print_step(3, "Creating Brookings China Source")
        source_id = create_brookings_source(api_url, args.max_artifacts)
        if not source_id:
            print_error("❌ Failed to create source")
            sys.exit(1)
    else:
        print_step(3, f"Using Existing Source: {source_id}")
        print_success(f"Source ID: {source_id}")
    
    # Step 4: Trigger crawl (unless skipped)
    job_id = None
    if not args.skip_crawl:
        print_step(4, "Triggering Web Crawl")
        job_id = trigger_crawl(api_url, source_id)
        if not job_id:
            print_error("❌ Failed to trigger crawl")
            sys.exit(1)
        
        # Step 5: Monitor job
        print_step(5, "Monitoring Crawl Job")
        if not monitor_job(api_url, job_id, timeout=900):
            print_error("❌ Crawl job failed or timed out")
            print_info(f"Check job: curl {api_url}/api/v1/jobs/{job_id}")
            print_info("Check logs: tail -f logs/api.log")
            sys.exit(1)
        
        # Wait a moment for final DB commits
        print_info("Waiting for final database writes...")
        time.sleep(5)
    else:
        print_step(4, "Skipping Crawl (using existing artifacts)")
    
    # Step 6: Get artifacts
    print_step(6, "Retrieving Artifacts")
    artifacts = get_source_artifacts(api_url, source_id, limit=args.max_artifacts)
    if not artifacts:
        print_error("❌ No artifacts found")
        print_info("The crawl completed but found no artifacts.")
        print_info("This could be due to:")
        print_info("  • Robots.txt restrictions")
        print_info("  • Content filtering (min length, file type)")
        print_info("  • Network issues")
        print_info("  • Source configuration issues")
        sys.exit(1)
    
    # Step 7: Wait for normalization
    print_step(7, "Waiting for Artifact Normalization")
    normalized_artifacts = wait_for_normalization(api_url, artifacts, timeout=900)
    if not normalized_artifacts:
        print_error("❌ No artifacts were normalized")
        print_info("Check normalize service:")
        print_info(f"  • curl http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:8001/health")
        print_info("  • tail -f logs/normalize.log")
        sys.exit(1)
    
    # Step 8: Trigger evaluations
    print_step(8, "Triggering LLM Evaluations")
    evaluations = []
    failed_count = 0
    
    for i, artifact in enumerate(normalized_artifacts, 1):
        artifact_id = artifact.get('id')
        uri = artifact.get('uri', 'unknown')
        
        print_info(f"[{i}/{len(normalized_artifacts)}] Evaluating {artifact_id[:8]}...")
        print_info(f"       URI: {uri[:60]}")
        
        eval_result = trigger_evaluation(api_url, artifact_id, uri)
        if eval_result:
            evaluations.append(eval_result)
            label = eval_result.get('label', 'Unknown')
            score = eval_result.get('total_score', 0)
            
            # Color-code result
            if label == 'Signal':
                color = Colors.OKGREEN
            elif label == 'Review':
                color = Colors.WARNING
            else:
                color = Colors.FAIL
            
            print_success(f"{color}  Result: {label} (score: {score:.2f}/5.0){Colors.ENDC}")
        else:
            failed_count += 1
            print_warning(f"  Evaluation failed")
        
        # Delay between evaluations
        if i < len(normalized_artifacts):
            time.sleep(3)
    
    if not evaluations:
        print_error("❌ No evaluations completed")
        print_info(f"All {failed_count} evaluation attempts failed")
        print_info("Check:")
        print_info("  • LLM provider API key is valid")
        print_info("  • LLM provider has sufficient quota")
        print_info("  • Network connectivity to LLM API")
        sys.exit(1)
    
    if failed_count > 0:
        print_warning(f"⚠ {failed_count} evaluations failed")
    
    # Step 9: Display results
    print_step(9, "Displaying Results")
    display_results(evaluations, normalized_artifacts)
    
    # Final summary
    print_header("E2E TEST COMPLETE ✅")
    
    print(f"{Colors.BOLD}Test Summary:{Colors.ENDC}")
    print(f"  Source: Brookings China & Asia-Pacific")
    print(f"  Source ID: {source_id}")
    if job_id:
        print(f"  Job ID: {job_id}")
    print(f"  Artifacts Crawled: {len(artifacts)}")
    print(f"  Artifacts Normalized: {len(normalized_artifacts)}")
    print(f"  Artifacts Evaluated: {len(evaluations)}")
    
    signal_count = sum(1 for e in evaluations if e.get('label') == 'Signal')
    print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}✓ Signal: {signal_count}{Colors.ENDC}")
    print(f"  {Colors.WARNING}✓ Review: {sum(1 for e in evaluations if e.get('label') == 'Review')}{Colors.ENDC}")
    print(f"  {Colors.FAIL}✓ Noise: {sum(1 for e in evaluations if e.get('label') == 'Noise')}{Colors.ENDC}")
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ FULL PIPELINE TEST SUCCESSFUL!{Colors.ENDC}")
    print(f"\n{Colors.OKBLUE}View results in frontend:{Colors.ENDC}")
    print(f"  http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:6060")
    print(f"\n{Colors.OKBLUE}API Endpoints:{Colors.ENDC}")
    print(f"  Artifacts: {api_url}/api/v1/artifacts/")
    print(f"  Evaluations: {api_url}/api/v1/evaluations/")
    print(f"  Library (Signal): {api_url}/api/v1/library/")

if __name__ == "__main__":
    main()

