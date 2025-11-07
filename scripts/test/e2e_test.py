#!/usr/bin/env python3
"""
LoreGuard End-to-End Test Script

Tests the complete workflow:
1. Create/configure a test source
2. Trigger ingestion job
3. Monitor job status
4. Wait for artifacts to be normalized
5. Trigger LLM evaluation
6. Display results (Signal/Review/Noise classification)
7. Show scoring breakdown

Usage:
    python scripts/test/e2e_test.py [--source-id <id>] [--skip-ingestion] [--api-url <url>]
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
    print(f"{Colors.OKCYAN}[Step {step_num}]{Colors.ENDC} {message}")

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
            print_success(f"API service is healthy: {data}")
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
            print_success(f"Found active rubric: {rubric.get('version', 'unknown')}")
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
            print_success(f"Found active LLM provider: {provider.get('name', 'unknown')} ({provider.get('provider', 'unknown')})")
            return provider
        else:
            print_error(f"No active LLM provider found: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Failed to check active provider: {e}")
        return None

def create_test_source(api_url: str) -> Optional[str]:
    """Create a test source"""
    source_config = {
        "name": "E2E Test Source - Books to Scrape",
        "type": "web",
        "status": "active",
        "config": {
            "start_urls": ["http://books.toscrape.com"],
            "crawl_scope": {
                "max_depth": 2,
                "max_artifacts": 10
            },
            "filtering": {
                "allowed_domains": ["books.toscrape.com"]
            },
            "politeness": {
                "download_delay": 1.0,
                "concurrent_requests_per_domain": 1
            }
        }
    }
    
    try:
        response = requests.post(
            f"{api_url}/api/v1/sources/",
            json=source_config,
            timeout=10
        )
        if response.status_code == 200:
            source = response.json()
            source_id = source.get('id')
            print_success(f"Created test source: {source.get('name')} (ID: {source_id})")
            return source_id
        else:
            print_error(f"Failed to create source: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Error creating source: {e}")
        return None

def trigger_crawl(api_url: str, source_id: str) -> Optional[str]:
    """Trigger crawl for a source"""
    try:
        response = requests.post(
            f"{api_url}/api/v1/sources/{source_id}/trigger",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            job_id = data.get('job_id')
            print_success(f"Triggered crawl job: {job_id}")
            print_info(f"Spider: {data.get('spider_name', 'unknown')}")
            print_info(f"Process ID: {data.get('process_id', 'unknown')}")
            return job_id
        else:
            print_error(f"Failed to trigger crawl: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Error triggering crawl: {e}")
        return None

def monitor_job(api_url: str, job_id: str, timeout: int = 600) -> bool:
    """Monitor job until completion"""
    print_info(f"Monitoring job {job_id} (timeout: {timeout}s)")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"{api_url}/api/v1/jobs/{job_id}?include_process_info=true",
                timeout=5
            )
            if response.status_code == 200:
                job = response.json()
                status = job.get('status', 'unknown')
                print_info(f"Job status: {status}")
                
                # Check payload for progress
                payload = job.get('payload', {})
                if 'items_processed' in payload and 'total_items' in payload:
                    processed = payload['items_processed']
                    total = payload['total_items']
                    if total > 0:
                        progress = int((processed / total) * 100)
                        print_info(f"Progress: {progress}% ({processed}/{total} items)")
                
                if status in ['completed', 'failed', 'cancelled', 'timeout']:
                    if status == 'completed':
                        duration = time.time() - start_time
                        print_success(f"Job completed successfully!")
                        print_info(f"Duration: {duration:.1f}s")
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

def get_artifacts(api_url: str, source_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get artifacts from a source"""
    try:
        # Get all artifacts and filter by source_id client-side
        # (due to UUID/string type mismatch in API)
        url = f"{api_url}/api/v1/artifacts/?limit=100"
        print_info(f"Fetching artifacts from: {url}")
        response = requests.get(url, timeout=10)
        print_info(f"Received response: status={response.status_code}, content_length={len(response.content) if hasattr(response, 'content') else 0}")
        
        if response.status_code == 200:
            data = response.json()
            all_artifacts = data.get('items', [])
            # Filter by source_id (handle both UUID and string formats)
            artifacts = [a for a in all_artifacts if str(a.get('source_id', '')) == str(source_id)]
            artifacts = artifacts[:limit]  # Limit results
            if artifacts:
                print_success(f"Found {len(artifacts)} artifacts from source (total available: {len(all_artifacts)})")
            else:
                print_warning(f"No artifacts found for source {source_id} (total available: {len(all_artifacts)})")
            return artifacts
        else:
            error_text = response.text[:500] if hasattr(response, 'text') and response.text else "No error details"
            print_error(f"Failed to get artifacts: HTTP {response.status_code}")
            if error_text and error_text != "No error details":
                print_error(f"Error: {error_text}")
            return []
    except requests.exceptions.RequestException as e:
        print_error(f"Network error getting artifacts: {e}")
        return []
    except json.JSONDecodeError as e:
        print_error(f"Failed to parse JSON response: {e}")
        if hasattr(response, 'text'):
            print_error(f"Response: {response.text[:300]}")
        return []
    except Exception as e:
        print_error(f"Unexpected error getting artifacts: {e}")
        import traceback
        traceback.print_exc()
        return []

def wait_for_normalization(api_url: str, artifacts: List[Dict[str, Any]], timeout: int = 300) -> List[Dict[str, Any]]:
    """Wait for artifacts to be normalized"""
    print_info(f"Waiting for normalization (timeout: {timeout}s)")
    start_time = time.time()
    normalized = []
    
    artifact_ids = [a.get('id') for a in artifacts]
    
    while time.time() - start_time < timeout and len(normalized) < len(artifact_ids):
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
                        print_success(f"Artifact {artifact_id[:8]}... normalized")
            except Exception as e:
                pass
        
        if len(normalized) < len(artifact_ids):
            time.sleep(5)
            remaining = len(artifact_ids) - len(normalized)
            print_info(f"Waiting... {remaining} artifacts remaining")
    
    if len(normalized) == len(artifact_ids):
        print_success(f"All {len(normalized)} artifacts normalized!")
    else:
        print_warning(f"Only {len(normalized)}/{len(artifact_ids)} artifacts normalized")
    
    return normalized

def trigger_evaluation(api_url: str, artifact_id: str) -> Optional[Dict[str, Any]]:
    """Trigger evaluation for an artifact"""
    try:
        response = requests.post(
            f"{api_url}/api/v1/artifacts/{artifact_id}/evaluate",
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Evaluation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Error triggering evaluation: {e}")
        return None

def display_results(evaluations: List[Dict[str, Any]]):
    """Display evaluation results"""
    print_header("EVALUATION RESULTS")
    
    signal_count = sum(1 for e in evaluations if e.get('label') == 'Signal')
    review_count = sum(1 for e in evaluations if e.get('label') == 'Review')
    noise_count = sum(1 for e in evaluations if e.get('label') == 'Noise')
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  Total Evaluated: {len(evaluations)}")
    print(f"  {Colors.OKGREEN}Signal: {signal_count}{Colors.ENDC}")
    print(f"  {Colors.WARNING}Review: {review_count}{Colors.ENDC}")
    print(f"  {Colors.FAIL}Noise: {noise_count}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.ENDC}\n")
    
    for eval_result in evaluations:
        label = eval_result.get('label', 'Unknown')
        total_score = eval_result.get('total_score', 0)
        confidence = eval_result.get('confidence', 0)
        artifact_id = eval_result.get('artifact_id', 'unknown')
        
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
        print(f"  Artifact: {artifact_id[:8]}...")
        print(f"  Total Score: {total_score:.2f}")
        print(f"  Confidence: {confidence:.2f}" if confidence else "  Confidence: N/A")
        
        scores = eval_result.get('scores', {})
        if scores:
            print(f"  Category Scores:")
            for category, score_data in scores.items():
                score = score_data.get('score', 0) if isinstance(score_data, dict) else score_data
                print(f"    - {category}: {score:.2f}")
        
        print()

def main():
    parser = argparse.ArgumentParser(description='LoreGuard E2E Test')
    parser.add_argument('--source-id', help='Use existing source ID')
    parser.add_argument('--skip-ingestion', action='store_true', help='Skip ingestion step')
    parser.add_argument('--api-url', help='API base URL', default=None)
    args = parser.parse_args()
    
    api_url = args.api_url or get_api_url()
    
    print_header("LOREGUARD END-TO-END TEST")
    print_info(f"API URL: {api_url}\n")
    
    # Step 1: Health check
    print_step(1, "Checking API Health")
    if not check_health(api_url):
        print_error("API health check failed. Please ensure services are running.")
        sys.exit(1)
    
    # Step 2: Verify active rubric
    print_step(2, "Verifying Active Rubric")
    rubric = verify_active_rubric(api_url)
    if not rubric:
        print_error("No active rubric found. Please activate a rubric first.")
        sys.exit(1)
    
    # Step 3: Verify active provider
    print_step(3, "Verifying Active LLM Provider")
    provider = verify_active_provider(api_url)
    if not provider:
        print_error("No active LLM provider found. Please configure a provider in Settings.")
        sys.exit(1)
    
    # Step 4: Create or use source
    source_id = args.source_id
    if not args.skip_ingestion and not source_id:
        print_step(4, "Creating Test Source")
        source_id = create_test_source(api_url)
        if not source_id:
            print_error("Failed to create test source")
            sys.exit(1)
    elif source_id:
        print_step(4, f"Using Existing Source: {source_id}")
        print_info(f"Source ID: {source_id}")
    
    # Step 5: Trigger crawl (if not skipping)
    job_id = None
    if not args.skip_ingestion:
        print_step(5, "Triggering Source Crawl")
        job_id = trigger_crawl(api_url, source_id)
        if not job_id:
            print_error("Failed to trigger crawl")
            sys.exit(1)
        
        # Step 6: Monitor job
        print_step(6, "Monitoring Crawl Job")
        if not monitor_job(api_url, job_id):
            print_error("Crawl job failed or timed out")
            sys.exit(1)
    
    # Step 7: Get artifacts
    print_step(7, "Retrieving Artifacts")
    artifacts = get_artifacts(api_url, source_id, limit=5)
    if not artifacts:
        print_error("No artifacts found")
        sys.exit(1)
    
    # Step 8: Wait for normalization
    print_step(8, "Waiting for Artifact Normalization")
    normalized_artifacts = wait_for_normalization(api_url, artifacts)
    if not normalized_artifacts:
        print_error("No artifacts were normalized")
        sys.exit(1)
    
    # Step 9: Trigger evaluations
    print_step(9, "Triggering LLM Evaluations")
    evaluations = []
    for artifact in normalized_artifacts:
        artifact_id = artifact.get('id')
        print_info(f"Evaluating artifact {artifact_id[:8]}...")
        eval_result = trigger_evaluation(api_url, artifact_id)
        if eval_result:
            evaluations.append(eval_result)
            time.sleep(2)  # Small delay between evaluations
    
    if not evaluations:
        print_error("No evaluations completed")
        sys.exit(1)
    
    # Step 10: Display results
    print_step(10, "Displaying Results")
    display_results(evaluations)
    
    print_success("E2E test completed successfully!")
    print_header("TEST COMPLETE")

if __name__ == "__main__":
    main()

