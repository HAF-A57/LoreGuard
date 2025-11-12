#!/usr/bin/env python
"""
Test script for Celery workers
Tests task queue functionality for normalization and evaluation
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_celery_connection():
    """Test Celery app connection to Redis"""
    try:
        from apps.shared.tasks.celery_app import celery_app
        
        # Test broker connection
        inspect = celery_app.control.inspect()
        active_queues = inspect.active_queues()
        
        if active_queues:
            logger.info("✅ Celery workers are connected!")
            for worker, queues in active_queues.items():
                logger.info(f"  Worker: {worker}")
                for queue in queues:
                    logger.info(f"    Queue: {queue['name']}")
            return True
        else:
            logger.warning("⚠️  No active workers found. Start workers with:")
            logger.warning("  celery -A apps.shared.tasks.celery_app worker --queue=normalize_queue --concurrency=5")
            logger.warning("  celery -A apps.shared.tasks.celery_app worker --queue=evaluate_queue --concurrency=3")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to Celery: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    try:
        import redis
        from apps.shared.tasks.celery_app import REDIS_URL
        
        # Parse Redis URL
        if REDIS_URL.startswith('redis://'):
            # Extract password if present
            if '@' in REDIS_URL:
                parts = REDIS_URL.split('@')
                auth_part = parts[0].replace('redis://', '').replace(':', '')
                if auth_part:
                    password = auth_part
                else:
                    password = None
                host_part = parts[1].split('/')[0]
            else:
                password = None
                host_part = REDIS_URL.replace('redis://', '').split('/')[0]
            
            host, port = host_part.split(':')
            
            r = redis.Redis(
                host=host,
                port=int(port),
                password=password if password else None,
                decode_responses=True
            )
            r.ping()
            logger.info("✅ Redis connection successful!")
            return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.error(f"   REDIS_URL: {REDIS_URL}")
        return False

def test_task_enqueue():
    """Test enqueueing a task"""
    try:
        from apps.shared.tasks.normalize_tasks import normalize_artifact
        
        # Enqueue a test task (will fail but tests queue)
        logger.info("Testing task enqueueing...")
        task = normalize_artifact.delay("test-artifact-id-12345")
        logger.info(f"✅ Task enqueued! Task ID: {task.id}")
        logger.info(f"   Task state: {task.state}")
        return task.id
    except Exception as e:
        logger.error(f"❌ Failed to enqueue task: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_queue_stats():
    """Check queue statistics"""
    try:
        from apps.shared.tasks.celery_app import celery_app
        
        inspect = celery_app.control.inspect()
        
        # Get active tasks
        active = inspect.active()
        reserved = inspect.reserved()
        stats = inspect.stats()
        
        logger.info("\n📊 Queue Statistics:")
        
        if active:
            total_active = sum(len(tasks) for tasks in active.values())
            logger.info(f"  Active tasks: {total_active}")
            for worker, tasks in active.items():
                if tasks:
                    logger.info(f"    {worker}: {len(tasks)} tasks")
        
        if reserved:
            total_reserved = sum(len(tasks) for tasks in reserved.values())
            logger.info(f"  Reserved tasks: {total_reserved}")
            for worker, tasks in reserved.items():
                if tasks:
                    logger.info(f"    {worker}: {len(tasks)} tasks")
        
        if stats:
            for worker, stat in stats.items():
                logger.info(f"  {worker}:")
                logger.info(f"    Pool: {stat.get('pool', {}).get('implementation', 'N/A')}")
                logger.info(f"    Processes: {stat.get('pool', {}).get('processes', [])}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to get queue stats: {e}")
        return False

def test_with_real_artifact(artifact_id: str):
    """Test with a real artifact ID from database"""
    try:
        from apps.shared.tasks.normalize_tasks import normalize_artifact
        
        logger.info(f"\n🧪 Testing normalization with real artifact: {artifact_id}")
        task = normalize_artifact.delay(artifact_id)
        
        logger.info(f"   Task ID: {task.id}")
        logger.info(f"   Waiting for completion (max 60s)...")
        
        # Wait for result with timeout
        try:
            result = task.get(timeout=60)
            logger.info(f"✅ Normalization completed!")
            logger.info(f"   Result: {result}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Task not completed yet: {e}")
            logger.info(f"   Task state: {task.state}")
            logger.info(f"   Check worker logs for details")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to test normalization: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("Celery Workers Test Suite")
    logger.info("=" * 60)
    
    # Test 1: Redis connection
    logger.info("\n1️⃣  Testing Redis connection...")
    if not test_redis_connection():
        logger.error("❌ Redis connection failed. Make sure Redis is running.")
        logger.error("   Start with: docker-compose up -d redis")
        return 1
    
    # Test 2: Celery connection
    logger.info("\n2️⃣  Testing Celery worker connection...")
    workers_connected = test_celery_connection()
    
    if not workers_connected:
        logger.warning("\n⚠️  Workers not running. To start workers:")
        logger.warning("   Terminal 1: celery -A apps.shared.tasks.celery_app worker --queue=normalize_queue --concurrency=5 --loglevel=info")
        logger.warning("   Terminal 2: celery -A apps.shared.tasks.celery_app worker --queue=evaluate_queue --concurrency=3 --loglevel=info")
        logger.warning("\n   Or use the worker scripts:")
        logger.warning("   python apps/shared/tasks/workers/normalize_worker.py")
        logger.warning("   python apps/shared/tasks/workers/evaluate_worker.py")
        return 1
    
    # Test 3: Queue stats
    logger.info("\n3️⃣  Checking queue statistics...")
    check_queue_stats()
    
    # Test 4: Task enqueueing
    logger.info("\n4️⃣  Testing task enqueueing...")
    task_id = test_task_enqueue()
    
    if task_id:
        logger.info(f"\n✅ Basic tests passed!")
        logger.info(f"\n💡 To test with a real artifact:")
        logger.info(f"   python test_celery_workers.py --artifact-id <artifact-uuid>")
        
        # Check if artifact ID provided
        if len(sys.argv) > 1 and sys.argv[1] == '--artifact-id' and len(sys.argv) > 2:
            artifact_id = sys.argv[2]
            test_with_real_artifact(artifact_id)
    
    logger.info("\n" + "=" * 60)
    logger.info("Test suite completed!")
    logger.info("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

