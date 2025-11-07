#!/usr/bin/env python3
"""
Quick Pipeline Test - Uses existing Brookings artifacts

Tests normalization and evaluation on existing artifacts without waiting for crawl.
"""

import requests
import json
import time
import sys

class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {msg}")

def print_error(msg):
    print(f"{Colors.FAIL}✗{Colors.ENDC} {msg}")

def print_info(msg):
    print(f"  {msg}")

print(f"{Colors.BOLD}Quick Pipeline Test - Existing Brookings Artifacts{Colors.ENDC}\n")

# Get existing Brookings artifacts
print("Step 1: Finding existing Brookings artifacts...")
response = requests.get("http://localhost:8000/api/v1/artifacts/?limit=100", timeout=5)
if response.status_code != 200:
    print_error("Failed to get artifacts")
    sys.exit(1)

artifacts = response.json().get('items', [])
brookings = [a for a in artifacts if 'brookings' in a.get('uri', '').lower()]
print_success(f"Found {len(brookings)} Brookings artifacts")

# Select up to 3 for testing
test_artifacts = brookings[:3]
print_info(f"Testing with {len(test_artifacts)} artifacts")

# Step 2: Normalize artifacts
print("\nStep 2: Normalizing artifacts...")
normalized = []
for i, artifact in enumerate(test_artifacts, 1):
    art_id = artifact.get('id')
    uri = artifact.get('uri', '')[:60]
    
    print(f"  [{i}/{len(test_artifacts)}] {uri}...")
    
    # Check if already normalized
    if artifact.get('normalized_ref'):
        print_success(f"    Already normalized")
        normalized.append(artifact)
        continue
    
    # Trigger normalization
    try:
        response = requests.post(
            "http://localhost:8001/api/v1/documents/process",
            json={"artifact_id": art_id},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"    Normalized ({result.get('text_length', 0):,} chars)")
            # Refetch artifact to get updated data
            art_response = requests.get(f"http://localhost:8000/api/v1/artifacts/{art_id}", timeout=5)
            if art_response.status_code == 200:
                normalized.append(art_response.json())
        else:
            print_error(f"    Failed: {response.text[:100]}")
    except Exception as e:
        print_error(f"    Error: {str(e)[:100]}")

print(f"\n✓ Normalized: {len(normalized)}/{len(test_artifacts)} artifacts")

if not normalized:
    print_error("No artifacts normalized")
    sys.exit(1)

# Step 3: Evaluate artifacts
print("\nStep 3: Evaluating artifacts...")
evaluations = []
for i, artifact in enumerate(normalized, 1):
    art_id = artifact.get('id')
    uri = artifact.get('uri', '')[:60]
    
    print(f"  [{i}/{len(normalized)}] {uri}...")
    
    try:
        response = requests.post(
            f"http://localhost:8000/api/v1/artifacts/{art_id}/evaluate",
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            label = result.get('label', 'Unknown')
            score = result.get('total_score', 0)
            
            if label == 'Signal':
                color = Colors.OKGREEN
                icon = "🔔"
            elif label == 'Review':
                color = Colors.WARNING
                icon = "📋"
            else:
                color = Colors.FAIL
                icon = "🔇"
            
            print_success(f"    {color}{icon} {label}{Colors.ENDC} (score: {score:.2f}/5.0)")
            evaluations.append(result)
        else:
            print_error(f"    Failed: {response.text[:100]}")
    except Exception as e:
        print_error(f"    Error: {str(e)[:100]}")
    
    time.sleep(2)  # Small delay between evaluations

print(f"\n✓ Evaluated: {len(evaluations)}/{len(normalized)} artifacts")

if not evaluations:
    print_error("No evaluations completed")
    sys.exit(1)

# Step 4: Show results
print(f"\n{Colors.BOLD}RESULTS:{Colors.ENDC}")
signal_count = sum(1 for e in evaluations if e.get('label') == 'Signal')
review_count = sum(1 for e in evaluations if e.get('label') == 'Review')
noise_count = sum(1 for e in evaluations if e.get('label') == 'Noise')

print(f"  Total: {len(evaluations)}")
print(f"  {Colors.OKGREEN}Signal: {signal_count}{Colors.ENDC}")
print(f"  {Colors.WARNING}Review: {review_count}{Colors.ENDC}")
print(f"  {Colors.FAIL}Noise: {noise_count}{Colors.ENDC}")

print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ PIPELINE TEST COMPLETE!{Colors.ENDC}")
print("\nThe pipeline is working:")
print("  ✓ Normalization: Extracting text and metadata")
print("  ✓ Evaluation: LLM scoring with rubric")
print("  ✓ Classification: Signal/Review/Noise labels assigned")

