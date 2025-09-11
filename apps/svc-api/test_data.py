#!/usr/bin/env python3
"""
Create test data for LoreGuard API testing
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from db.database import SessionLocal
from models.source import Source
from models.artifact import Artifact, DocumentMetadata
import uuid
from datetime import datetime

def create_test_data():
    """Create test data in the database"""
    db = SessionLocal()
    
    try:
        # Create a test source
        source = Source(
            id=str(uuid.uuid4()),
            name='NATO Strategic Communications Centre',
            url='https://stratcomcoe.org',
            source_type='rss',
            schedule='0 */4 * * *',
            is_active=True
        )
        db.add(source)
        db.flush()
        
        # Create a test artifact
        artifact = Artifact(
            id=str(uuid.uuid4()),
            source_id=source.id,
            uri='https://stratcomcoe.org/publications/nato-strategic-assessment',
            content_hash='abc123def456',
            mime_type='text/html'
        )
        db.add(artifact)
        db.flush()
        
        # Create test metadata
        metadata = DocumentMetadata(
            id=str(uuid.uuid4()),
            artifact_id=artifact.id,
            title='NATO Strategic Assessment: Eastern European Defense Posture',
            authors='NATO Strategic Communications Centre',
            organization='NATO',
            pub_date=datetime.now()
        )
        db.add(metadata)
        
        db.commit()
        print('✅ Test data created successfully!')
        print(f'   Source ID: {source.id}')
        print(f'   Artifact ID: {artifact.id}')
        print(f'   Metadata ID: {metadata.id}')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()

