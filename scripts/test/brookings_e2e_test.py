#!/usr/bin/env python3
"""
LoreGuard E2E Test - Brookings China Source

Tests the complete pipeline with Brookings China page:
1. Create Brookings source configuration
2. Trigger web crawl
3. Monitor ingestion job
4. Wait for artifact normalization
5. Trigger LLM evaluation
6. Display Signal/Review/Noise results

Usage:
    python scripts/test/brookings_e2e_test.py [--api-url <url>] [--max-artifacts <num>]
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
    api_url = os.getenv('LOREGUARD_API_URL', 'http://localhost:8000')
    # Use detected IP if available
    host_ip = os.getenv('LOREGUARD_HOST_IP')
    if host_ip and host_ip != 'localhost':
        api_url = f"http://{host_ip}:8000"
    return api_url

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

def verify_active_rubric(api_url: str) -> Optional[Dict[str, Any]]:
    """Verify active rubric exists"""
    try:
        response = requests.get(f"{api_url}/api/v1/rubrics/active", timeout=5)
        if response.status_code == 200:
            rubric = response.json()
            version = rubric.get('version', 'unknown')
            categories = rubric.get('categories', {})
            category_count = len(categories) if isinstance(categories, dict) else len(categories) if isinstance(categories, list) else 0
            print_success(f"Active rubric: {version} ({category_count} categories)")
            
            # Display thresholds
            thresholds = rubric.get('thresholds', {})
            print_info(f"  Signal threshold: {thresholds.get('signal_min', 'N/A')}")
            print_info(f"  Review threshold: {thresholds.get('review_min', 'N/A')}")
            return rubric
        else:
            print_error(f"No active rubric found: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Failed to check active rubric: {e}")
        return None

def verify_active_provider(api_url: str) -> Optional[Dict[str, Any]]:
    """Verify active LLM provider exists"""
    try:
        response = requests.get(f"{api_url}/api/v1/llm-providers/default/active", timeout=5)
        if response.status_code == 200:
            provider = response.json()
            print_success(f"Active LLM provider: {provider.get('name', 'unknown')}")
            print_info(f"  Provider type: {provider.get('provider', 'unknown')}")
            print_info(f"  Model: {provider.get('model', 'unknown')}")
            print_info(f"  Status: {provider.get('status', 'unknown')}")
            return provider
        else:
            print_error(f"No active LLM provider found: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Failed to check active provider: {e}")
        return None

def create_brookings_source(api_url: str, max_artifacts: int = 10) -> Optional[str]:
    """Create Brookings China source"""
    source_config = {
        "name": "Brookings Institution - China & Asia-Pacific",
        "type": "web",
        "status": "active",
        "config": {
            "start_urls": ["https://www.brookings.edu/regions/asia-the-pacific/china"],
            "crawl_scope": {
                "max_depth": 2,
                "max_artifacts": max_artifacts,
                "max_pages_per_domain": 50,
                "max_crawl_time_minutes": 10
            },
            "filtering": {
                "allowed_domains": ["brookings.edu", "www.brookings.edu"],
                "allowed_file_types": ["text/html", "application/pdf"],
                "max_file_size_mb": 50
            },
            "politeness": {
                "download_delay": 2.0,
                "concurrent_requests_per_domain": 1,
                "autothrottle_enabled": True
            },
            "compliance": {
                "obey_robots_txt": True
            }
        }
    }
    
    print_info("Creating Brookings China source with configuration:")
    print_info(f"  URL: {source_config['config']['start_urls'][0]}")
    print_info(f"  Max artifacts: {max_artifacts}")
    print_info(f"  Max depth: {source_config['config']['crawl_scope']['max_depth']}")
    
    try:
        response = requests.post(
            f"{api_url}/api/v1/sources/",
            json=source_config,
            timeout=10
        )
        if response.status_code == 200:
            source = response.json()
            source_id = source.get('id')
            print_success(f"Created source: {source.get('name')}")
            print_success(f"Source ID: {source_id}")
            return source_id
        else:
            print_error(f"Failed to create source: {response.status_code}")
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
            timeout=10
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
            print_error(f"Failed to trigger crawl: {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return None
    except Exception as e:
        print_error(f"Error triggering crawl: {e}")
        return None

def monitor_job(api_url: str, job_id: str, timeout: int = 600) -> bool:
    """Monitor job until completion"""
    print_info(f"Monitoring job (timeout: {timeout}s)...")
    start_time = time.time()
    last_status = None
    check_count = 0
    
    while time.time() - start_time < timeout:
        check_count += 1
        try:
            response = requests.get(
                f"{api_url}/api/v1/jobs/{job_id}?include_process_info=true",
                timeout=5
            )
            if response.status_code == 200:
                job = response.json()
                status = job.get('status', 'unknown')
                
                # Only print if status changed
                if status != last_status:
                    elapsed = time.time() - start_time
                    print_info(f"[{elapsed:.1f}s] Job status: {status}")
                    last_status = status
                
                # Show process info if available
                if job.get('process_running'):
                    process_info = job.get('process_info', {})
                    if check_count % 6 == 0:  # Show process info every 30 seconds
                        print_info(f"  Process status: CPU {process_info.get('cpu_percent', 0):.1f}%, Memory {process_info.get('memory_mb', 0):.1f}MB")
                
                # Check for hanging
                if job.get('is_hanging'):
                    print_warning(f"Job is hanging: {job.get('hanging_reason', 'Unknown reason')}")
                
                # Check terminal statuses
                if status in ['completed', 'failed', 'cancelled', 'timeout']:
                    if status == 'completed':
                        duration = time.time() - start_time
                        print_success(f"Job completed successfully in {duration:.1f}s!")
                        
                        # Show timeline
                        timeline = job.get('timeline', [])
                        if timeline:
                            print_info("Job timeline:")
                            for entry in timeline[-5:]:  # Last 5 entries
                                print_info(f"  {entry.get('status')}: {entry.get('message', 'No message')}")
                        
                        return True
                    else:
                        print_error(f"Job ended with status: {status}")
                        if job.get('error'):
                            print_error(f"Error: {job.get('error')}")
                        return False
            else:
                print_warning(f"Failed to get job status: {response.status_code}")
        except Exception as e:
            print_warning(f"Error checking job status: {e}")
        
        time.sleep(5)
    
    print_error(f"Job monitoring timed out after {timeout}s")
    return False

def get_source_artifacts(api_url: str, source_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get artifacts from a specific source"""
    try:
        # Fetch all artifacts and filter by source
        url = f"{api_url}/api/v1/artifacts/?limit={limit}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            all_artifacts = data.get('items', [])
            
            # Filter by source_id
            artifacts = [a for a in all_artifacts if str(a.get('source_id', '')) == str(source_id)]
            
            if artifacts:
                print_success(f"Found {len(artifacts)} artifacts from source")
                for i, artifact in enumerate(artifacts[:5], 1):  # Show first 5
                    print_info(f"  {i}. {artifact.get('uri', 'No URI')[:80]}")
                if len(artifacts) > 5:
                    print_info(f"  ... and {len(artifacts) - 5} more")
            else:
                print_warning(f"No artifacts found for source {source_id}")
            
            return artifacts
        else:
            print_error(f"Failed to get artifacts: {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return []
    except Exception as e:
        print_error(f"Error getting artifacts: {e}")
        return []

def wait_for_normalization(api_url: str, artifacts: List[Dict[str, Any]], timeout: int = 600) -> List[Dict[str, Any]]:
    """Wait for artifacts to be normalized"""
    print_info(f"Waiting for normalization (timeout: {timeout}s)...")
    start_time = time.time()
    normalized = []
    
    artifact_ids = [a.get('id') for a in artifacts]
    total = len(artifact_ids)
    
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
                        print_success(f"Artifact {artifact_id[:8]}... normalized ({len(normalized)}/{total})")
                        
                        # Show metadata if available
                        metadata = artifact.get('document_metadata')
                        if metadata:
                            title = metadata.get('title', 'No title')
                            print_info(f"  Title: {title[:60]}")
            except Exception as e:
                pass
        
        if len(normalized) < total:
            time.sleep(10)  # Check every 10 seconds
    
    elapsed = time.time() - start_time
    if len(normalized) == total:
        print_success(f"All {len(normalized)} artifacts normalized in {elapsed:.1f}s!")
    else:
        print_warning(f"Only {len(normalized)}/{total} artifacts normalized after {elapsed:.1f}s")
    
    return normalized

def trigger_evaluation(api_url: str, artifact_id: str) -> Optional[Dict[str, Any]]:
    """Trigger evaluation for an artifact"""
    try:
        response = requests.post(
            f"{api_url}/api/v1/artifacts/{artifact_id}/evaluate",
            timeout=120  # LLM calls can take time
        )
        if response.status_code == 200:
            return response.json()
        else:
            error_text = response.text[:500] if hasattr(response, 'text') else "No error details"
            print_error(f"Evaluation failed (HTTP {response.status_code}): {error_text}")
            return None
    except requests.exceptions.Timeout:
        print_error(f"Evaluation timed out for artifact {artifact_id[:8]}...")
        return None
    except Exception as e:
        print_error(f"Error triggering evaluation: {e}")
        return None

def display_results(evaluations: List[Dict[str, Any]], artifacts: List[Dict[str, Any]]):
    """Display evaluation results"""
    print_header("EVALUATION RESULTS")
    
    signal_count = sum(1 for e in evaluations if e.get('label') == 'Signal')
    review_count = sum(1 for e in evaluations if e.get('label') == 'Review')
    noise_count = sum(1 for e in evaluations if e.get('label') == 'Noise')
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  Total Evaluated: {len(evaluations)}")
    print(f"  {Colors.OKGREEN}Signal: {signal_count} ({signal_count/len(evaluations)*100:.1f}%){Colors.ENDC}")
    print(f"  {Colors.WARNING}Review: {review_count} ({review_count/len(evaluations)*100:.1f}%){Colors.ENDC}")
    print(f"  {Colors.FAIL}Noise: {noise_count} ({noise_count/len(evaluations)*100:.1f}%){Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.ENDC}\n")
    
    # Create artifact lookup
    artifact_map = {a.get('id'): a for a in artifacts}
    
    for eval_result in evaluations:
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
        
        if label == 'Signal':
            color = Colors.OKGREEN
            icon = "🔔"
        elif label == 'Review':
            color = Colors.WARNING
            icon = "📋"
        else:
            color = Colors.FAIL
            icon = "🔇"
        
        print(f"{color}{Colors.BOLD}{icon} {label}{Colors.ENDC}")
        print(f"  Title: {title[:60]}")
        print(f"  URI: {uri[:80]}")
        print(f"  Total Score: {total_score:.2f}/5.0")
        print(f"  Confidence: {float(confidence)*100:.1f}%" if confidence else "  Confidence: N/A")
        print(f"  Model: {model_used}")
        print(f"  Rubric: {rubric_version}")
        
        scores = eval_result.get('scores', {})
        if scores:
            print(f"  Category Scores:")
            for category, score_data in scores.items():
                if isinstance(score_data, dict):
                    score = score_data.get('score', 0)
                    reasoning = score_data.get('reasoning', '')
                    print(f"    • {category}: {score:.2f}")
                    if reasoning:
                        print(f"      └─ {reasoning[:80]}")
                else:
                    print(f"    • {category}: {score_data:.2f}")
        
        print()

def check_database_content(api_url: str):
    """Check database content"""
    print_step("DB Check", "Checking Database Content")
    
    try:
        # Check sources
        response = requests.get(f"{api_url}/api/v1/sources/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Sources in database: {data.get('total', 0)}")
        
        # Check artifacts
        response = requests.get(f"{api_url}/api/v1/artifacts/?limit=1", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Artifacts in database: {data.get('total', 0)}")
        
        # Check evaluations
        response = requests.get(f"{api_url}/api/v1/evaluations/?limit=1", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Evaluations in database: {data.get('total', 0)}")
    except Exception as e:
        print_warning(f"Error checking database: {e}")

def main():
    parser = argparse.ArgumentParser(description='LoreGuard E2E Test - Brookings China')
    parser.add_argument('--api-url', help='API base URL', default=None)
    parser.add_argument('--max-artifacts', type=int, default=10, help='Maximum artifacts to crawl')
    parser.add_argument('--skip-crawl', action='store_true', help='Skip crawl, use existing artifacts')
    parser.add_argument('--source-id', help='Use existing source ID')
    args = parser.parse_args()
    
    api_url = args.api_url or get_api_url()
    
    print_header("LOREGUARD E2E TEST - BROOKINGS CHINA")
    print_info(f"API URL: {api_url}")
    print_info(f"Max Artifacts: {args.max_artifacts}")
    print_info(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Pre-test: Check database
    check_database_content(api_url)
    
    # Step 1: Health check
    print_step(1, "Checking API Health")
    if not check_health(api_url):
        print_error("API health check failed. Please ensure services are running.")
        print_info("Try running: bash scripts/dev/start-services.sh")
        sys.exit(1)
    
    # Step 2: Verify active rubric
    print_step(2, "Verifying Active Rubric")
    rubric = verify_active_rubric(api_url)
    if not rubric:
        print_error("No active rubric found.")
        print_info("Run: bash scripts/dev/init-databases.sh to create default rubric")
        sys.exit(1)
    
    # Step 3: Verify active provider
    print_step(3, "Verifying Active LLM Provider")
    provider = verify_active_provider(api_url)
    if not provider:
        print_error("No active LLM provider found.")
        print_info("Configure a provider via the frontend Settings page or API")
        sys.exit(1)
    
    # Step 4: Create or use source
    source_id = args.source_id
    if not source_id:
        print_step(4, "Creating Brookings China Source")
        source_id = create_brookings_source(api_url, args.max_artifacts)
        if not source_id:
            print_error("Failed to create source")
            sys.exit(1)
    else:
        print_step(4, f"Using Existing Source: {source_id}")
    
    # Step 5: Trigger crawl (unless skipped)
    job_id = None
    if not args.skip_crawl:
        print_step(5, "Triggering Web Crawl")
        job_id = trigger_crawl(api_url, source_id)
        if not job_id:
            print_error("Failed to trigger crawl")
            sys.exit(1)
        
        # Step 6: Monitor job
        print_step(6, "Monitoring Crawl Job")
        if not monitor_job(api_url, job_id, timeout=600):
            print_error("Crawl job failed or timed out")
            print_info(f"You can check job status at: {api_url}/api/v1/jobs/{job_id}")
            sys.exit(1)
    else:
        print_step(5, "Skipping crawl (using existing artifacts)")
    
    # Step 7: Get artifacts
    print_step(7, "Retrieving Artifacts")
    time.sleep(3)  # Give a moment for DB writes
    artifacts = get_source_artifacts(api_url, source_id, limit=args.max_artifacts)
    if not artifacts:
        print_error("No artifacts found")
        print_info("The crawl may have completed but found no suitable content.")
        print_info("Try checking the job logs or artifacts list manually.")
        sys.exit(1)
    
    # Step 8: Wait for normalization
    print_step(8, "Waiting for Artifact Normalization")
    normalized_artifacts = wait_for_normalization(api_url, artifacts, timeout=600)
    if not normalized_artifacts:
        print_error("No artifacts were normalized")
        print_info("Check normalize service logs for errors")
        sys.exit(1)
    
    # Step 9: Trigger evaluations
    print_step(9, "Triggering LLM Evaluations")
    evaluations = []
    for i, artifact in enumerate(normalized_artifacts, 1):
        artifact_id = artifact.get('id')
        print_info(f"[{i}/{len(normalized_artifacts)}] Evaluating artifact {artifact_id[:8]}...")
        eval_result = trigger_evaluation(api_url, artifact_id)
        if eval_result:
            evaluations.append(eval_result)
            label = eval_result.get('label', 'Unknown')
            score = eval_result.get('total_score', 0)
            print_success(f"  Result: {label} (score: {score:.2f})")
        else:
            print_warning(f"  Evaluation failed for artifact {artifact_id[:8]}...")
        
        # Small delay between evaluations
        if i < len(normalized_artifacts):
            time.sleep(2)
    
    if not evaluations:
        print_error("No evaluations completed")
        sys.exit(1)
    
    # Step 10: Display results
    print_step(10, "Displaying Results")
    display_results(evaluations, normalized_artifacts)
    
    # Final summary
    print_header("E2E TEST COMPLETE")
    print_success("Full pipeline test completed successfully!")
    print_info(f"\nTest Summary:")
    print_info(f"  Source ID: {source_id}")
    if job_id:
        print_info(f"  Job ID: {job_id}")
    print_info(f"  Artifacts Crawled: {len(artifacts)}")
    print_info(f"  Artifacts Normalized: {len(normalized_artifacts)}")
    print_info(f"  Artifacts Evaluated: {len(evaluations)}")
    print_info(f"  Signal Artifacts: {sum(1 for e in evaluations if e.get('label') == 'Signal')}")
    print_info(f"\nView results in frontend: http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:6060")

if __name__ == "__main__":
    main()

