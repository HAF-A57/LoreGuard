"""
Database models for LoreGuard
"""

# Import all models to ensure they are registered with SQLAlchemy
from .source import Source
from .artifact import Artifact, DocumentMetadata, Clarification
from .rubric import Rubric
from .evaluation import Evaluation
from .job import Job
from .library import LibraryItem
from .llm_provider import LLMProvider
from .prompt_template import PromptTemplate

__all__ = [
    "Source",
    "Artifact", 
    "DocumentMetadata",
    "Clarification",
    "Rubric",
    "Evaluation",
    "Job",
    "LibraryItem",
    "LLMProvider",
    "PromptTemplate"
]

