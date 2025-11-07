"""
Database configuration and connection management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with query timeout
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    future=True,
    connect_args={
        "connect_timeout": 10,  # 10 second connection timeout
        "options": "-c statement_timeout=30000"  # 30 second query timeout
    }
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

async def create_tables():
    """Create all database tables"""
    try:
        # Import all models to ensure they are registered
        from models import artifact, source, rubric, evaluation, job, library, llm_provider
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Initialize database with default data"""
    try:
        from models.rubric import Rubric
        
        db = SessionLocal()
        
        # Check if default rubric exists
        default_rubric = db.query(Rubric).filter(Rubric.version == "v0.1").first()
        
        if not default_rubric:
            # Create default rubric based on NotionalRubricToStart.md
            default_rubric_data = {
                "version": "v0.1",
                "categories": {
                    "credibility": {
                        "weight": 0.30,
                        "guidance": "Evaluate author, org, venue, and corroboration strength.",
                        "subcriteria": [
                            "author_expertise",
                            "organization_reputation",
                            "venue_rigor",
                            "citation_corroboration"
                        ]
                    },
                    "relevance": {
                        "weight": 0.30,
                        "guidance": "Assess alignment with specified scenarios and objectives.",
                        "subcriteria": [
                            "scenario_alignment",
                            "doctrinal_relevance",
                            "operational_timeline"
                        ]
                    },
                    "rigor": {
                        "weight": 0.15,
                        "guidance": "Assess methodology transparency and data quality.",
                        "subcriteria": [
                            "method_transparency",
                            "data_quality",
                            "reasoning_soundness"
                        ]
                    },
                    "timeliness": {
                        "weight": 0.10,
                        "guidance": "Evaluate publication recency and update frequency.",
                        "subcriteria": [
                            "publication_recency",
                            "update_frequency"
                        ]
                    },
                    "novelty": {
                        "weight": 0.10,
                        "guidance": "Assess originality and unique insights.",
                        "subcriteria": [
                            "originality",
                            "unique_dataset"
                        ]
                    },
                    "coverage": {
                        "weight": 0.05,
                        "guidance": "Evaluate completeness and clarity.",
                        "subcriteria": [
                            "completeness",
                            "clarity"
                        ]
                    }
                },
                "thresholds": {
                    "signal_min": 3.8,
                    "review_min": 2.8,
                    "noise_max": 2.8
                },
                "prompts": {
                    "evaluation": "prompt_ref_eval_v0",
                    "metadata": "prompt_ref_meta_v0",
                    "clarification": "prompt_ref_clarify_v0"
                },
                "is_active": True
            }
            
            rubric = Rubric(**default_rubric_data)
            db.add(rubric)
            db.commit()
            logger.info("Default rubric v0.1 created and activated")
        else:
            # Ensure at least one rubric is active
            active_rubric = db.query(Rubric).filter(Rubric.is_active == True).first()
            if not active_rubric:
                default_rubric.is_active = True
                db.commit()
                logger.info("Default rubric v0.1 activated")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

