#!/usr/bin/env python3
"""
Test LLM Evaluation Only

Creates artifact with pre-normalized content and tests LLM evaluation.
Skips normalization service entirely.
"""

import os
import sys
import json
import hashlib
import requests
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'apps' / 'svc-api' / 'app'))

API_URL = "http://localhost:8000"

# Sample content (pre-normalized)
normalized_text = """
NATO Strategic Assessment: Eastern European Defense Posture

Executive Summary:
This document provides a comprehensive analysis of NATO's defensive capabilities 
and strategic positioning in Eastern Europe, focusing on force readiness, 
logistical considerations, and regional security dynamics.

Key Findings:
- Enhanced forward presence in Baltic states demonstrates commitment to Article 5 collective defense
- Rapid reaction forces maintain 48-hour deployment capability across the region
- Strategic communication initiatives effectively counter disinformation campaigns  
- Interoperability exercises significantly improve coalition effectiveness

Recommendations:
1. Continue rotational deployments to maintain readiness and deterrence posture
2. Strengthen cyber defense capabilities across all member states
3. Enhance intelligence sharing mechanisms between allied forces
4. Invest in logistics infrastructure along the Eastern flank

Author: NATO Strategic Communications Centre of Excellence
Date: September 15, 2024
Classification: Unclassified / Public Release
Geographic Scope: Eastern Europe, Baltic States
Topics: Defense Strategy, NATO Operations, Regional Security, Military Readiness
"""

print("="*80)
print(" LoreGuard LLM Evaluation Test".center(80))
print("="*80)
print()

# Step 1: Create artifact with normalized content
print("[Step 1] Creating artifact with pre-normalized content...")

try:
    from db.database import SessionLocal
    from models.artifact import Artifact, DocumentMetadata
    import boto3
    
    content_hash = hashlib.sha256(normalized_text.encode()).hexdigest()
    print(f"  Content hash: {content_hash[:16]}...")
    
    db = SessionLocal()
    
    # Check for existing
    artifact = db.query(Artifact).filter(Artifact.content_hash == content_hash).first()
    
    if not artifact:
        # Create source first
        response = requests.post(f"{API_URL}/api/v1/sources/", json={
            "name": "Eval Test Source",
            "type": "web",
            "config": {"start_urls": ["https://test.com"]},
            "status": "active"
        })
        source_id = response.json()['id']
        
        # Create artifact
        artifact = Artifact(
            source_id=source_id,
            uri="https://stratcomcoe.org/test",
            content_hash=content_hash,
            mime_type="text/plain"
        )
        
        # Store normalized content in MinIO
        normalized_hash = content_hash
        normalized_key = f"normalized/{normalized_hash[:2]}/{normalized_hash[2:4]}/{normalized_hash}.txt"
        
        s3 = boto3.client('s3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id='loreguard',
            aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'b3Vv1KUuPQq8ME6Ha2yIOBEY6'))
        
        s3.put_object(
            Bucket='loreguard-artifacts',
            Key=normalized_key,
            Body=normalized_text.encode(),
            ContentType='text/plain'
        )
        
        artifact.normalized_ref = normalized_key
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        # Add metadata
        metadata = DocumentMetadata(
            artifact_id=artifact.id,
            title="NATO Strategic Assessment: Eastern European Defense Posture",
            authors='["NATO Strategic Communications Centre"]',
            organization="NATO",
            pub_date=datetime(2024, 9, 15),
            topics='["Defense", "NATO", "Eastern Europe"]',
            language="en"
        )
        db.add(metadata)
        db.commit()
        
        print(f"✓ Artifact created: {artifact.id}")
        print(f"✓ Normalized content stored: {normalized_key}")
    else:
        print(f"  Artifact already exists: {artifact.id}")
        if not artifact.normalized_ref:
            # Add normalized ref
            normalized_hash = content_hash
            normalized_key = f"normalized/{normalized_hash[:2]}/{normalized_hash[2:4]}/{normalized_hash}.txt"
            
            s3 = boto3.client('s3',
                endpoint_url='http://localhost:9000',
                aws_access_key_id='loreguard',
                aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'b3Vv1KUuPQq8ME6Ha2yIOBEY6'))
            
            s3.put_object(
                Bucket='loreguard-artifacts',
                Key=normalized_key,
                Body=normalized_text.encode(),
                ContentType='text/plain'
            )
            
            artifact.normalized_ref = normalized_key
            db.commit()
            print(f"✓ Added normalized_ref: {normalized_key}")
    
    artifact_id = str(artifact.id)
    db.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Step 2: Trigger evaluation
print("[Step 2] Triggering LLM evaluation...")
try:
    response = requests.post(
        f"{API_URL}/api/v1/artifacts/{artifact_id}/evaluate",
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Evaluation completed!")
        print()
        print(f"  Label: {result.get('label')}")
        print(f"  Confidence: {result.get('confidence', 0):.2%}")
        print(f"  Total Score: {result.get('total_score', 0):.2f}/5.0")
        print()
        print("  Category Scores:")
        for cat, score_data in (result.get('scores') or {}).items():
            score = score_data.get('score', 0) if isinstance(score_data, dict) else score_data
            print(f"    - {cat}: {score:.2f}/5.0")
        print()
        print("="*80)
        print(" SUCCESS! ".center(80, "="))
        print("="*80)
        print()
        print(f"Artifact ID: {artifact_id}")
        print(f"View in frontend: http://localhost:6060")
        print()
    else:
        print(f"✗ Evaluation failed: {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

