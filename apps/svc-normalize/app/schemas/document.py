"""
LoreGuard Document Processing Schemas

Pydantic models for document processing requests and responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, HttpUrl


class DocumentFormat(str, Enum):
    """Supported document formats."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    PPTX = "pptx"
    PPT = "ppt"
    XLSX = "xlsx"
    XLS = "xls"
    HTML = "html"
    TXT = "txt"
    MD = "markdown"
    XML = "xml"
    JSON = "json"
    RTF = "rtf"
    ODT = "odt"
    ODP = "odp"
    ODS = "ods"
    EPUB = "epub"
    CSV = "csv"
    TSV = "tsv"
    # Image formats for OCR
    JPEG = "jpeg"
    PNG = "png"
    TIFF = "tiff"
    BMP = "bmp"


class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class LanguageCode(str, Enum):
    """Supported language codes."""
    EN = "en"  # English
    FR = "fr"  # French
    DE = "de"  # German
    ES = "es"  # Spanish
    RU = "ru"  # Russian
    ZH = "zh"  # Chinese
    AR = "ar"  # Arabic
    PT = "pt"  # Portuguese
    IT = "it"  # Italian
    JA = "ja"  # Japanese
    KO = "ko"  # Korean
    NL = "nl"  # Dutch
    SV = "sv"  # Swedish
    NO = "no"  # Norwegian
    DA = "da"  # Danish
    FI = "fi"  # Finnish
    PL = "pl"  # Polish
    TR = "tr"  # Turkish
    HE = "he"  # Hebrew
    TH = "th"  # Thai


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class DocumentProcessingRequest(BaseModel):
    """Request to process a document."""
    
    # Document identification
    source_uri: Optional[HttpUrl] = Field(None, description="Source URI of the document")
    source_id: Optional[str] = Field(None, description="Source system identifier")
    
    # Processing options
    extract_metadata: bool = Field(True, description="Extract document metadata")
    extract_text: bool = Field(True, description="Extract text content")
    extract_images: bool = Field(False, description="Extract embedded images")
    extract_tables: bool = Field(True, description="Extract table data")
    
    # OCR options
    enable_ocr: bool = Field(True, description="Enable OCR for image-based content")
    ocr_languages: List[LanguageCode] = Field(
        default=[LanguageCode.EN], 
        description="Languages for OCR processing"
    )
    
    # Language processing
    detect_language: bool = Field(True, description="Detect document language")
    target_language: Optional[LanguageCode] = Field(None, description="Target language for translation")
    
    # Quality settings
    min_confidence: float = Field(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")
    
    # Processing hints
    document_type: Optional[str] = Field(None, description="Document type hint (academic, news, report, etc.)")
    expected_language: Optional[LanguageCode] = Field(None, description="Expected document language")
    
    class Config:
        schema_extra = {
            "example": {
                "source_uri": "https://example.com/document.pdf",
                "source_id": "source-123",
                "extract_metadata": True,
                "extract_text": True,
                "extract_tables": True,
                "enable_ocr": True,
                "ocr_languages": ["en", "fr"],
                "detect_language": True,
                "min_confidence": 0.7,
                "document_type": "academic"
            }
        }


class BatchProcessingRequest(BaseModel):
    """Request to process multiple documents."""
    
    documents: List[DocumentProcessingRequest] = Field(
        ..., 
        min_items=1, 
        max_items=100,
        description="List of documents to process"
    )
    
    # Batch options
    parallel_processing: bool = Field(True, description="Process documents in parallel")
    max_workers: int = Field(4, ge=1, le=16, description="Maximum number of parallel workers")
    
    # Callback options
    callback_url: Optional[HttpUrl] = Field(None, description="URL to call when batch is complete")
    
    class Config:
        schema_extra = {
            "example": {
                "documents": [
                    {
                        "source_uri": "https://example.com/doc1.pdf",
                        "extract_metadata": True,
                        "extract_text": True
                    },
                    {
                        "source_uri": "https://example.com/doc2.docx",
                        "extract_metadata": True,
                        "extract_text": True
                    }
                ],
                "parallel_processing": True,
                "max_workers": 4
            }
        }


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class DocumentMetadata(BaseModel):
    """Extracted document metadata."""
    
    # Basic metadata
    title: Optional[str] = Field(None, description="Document title")
    authors: List[str] = Field(default_factory=list, description="Document authors")
    organization: Optional[str] = Field(None, description="Publishing organization")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    
    # Content metadata
    language: Optional[LanguageCode] = Field(None, description="Detected language")
    page_count: Optional[int] = Field(None, description="Number of pages")
    word_count: Optional[int] = Field(None, description="Approximate word count")
    
    # Technical metadata
    file_format: Optional[DocumentFormat] = Field(None, description="Document format")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    
    # Subject and classification
    topics: List[str] = Field(default_factory=list, description="Extracted topics/keywords")
    subjects: List[str] = Field(default_factory=list, description="Subject classifications")
    geographic_scope: List[str] = Field(default_factory=list, description="Geographic regions mentioned")
    
    # Quality metrics
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Extraction confidence")
    processing_quality: Optional[str] = Field(None, description="Processing quality assessment")
    
    # Additional metadata
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    isbn: Optional[str] = Field(None, description="ISBN for books")
    issn: Optional[str] = Field(None, description="ISSN for periodicals")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "NATO Strategic Assessment: Eastern European Defense Posture",
                "authors": ["Dr. Jane Smith", "Col. John Doe"],
                "organization": "NATO Strategic Communications Centre",
                "publication_date": "2024-01-15T00:00:00Z",
                "language": "en",
                "page_count": 45,
                "word_count": 12500,
                "file_format": "pdf",
                "topics": ["defense", "NATO", "Eastern Europe", "security"],
                "geographic_scope": ["Eastern Europe", "Baltic States"],
                "confidence_score": 0.92
            }
        }


class ExtractedContent(BaseModel):
    """Extracted document content."""
    
    # Text content
    raw_text: Optional[str] = Field(None, description="Raw extracted text")
    cleaned_text: Optional[str] = Field(None, description="Cleaned and normalized text")
    structured_content: Optional[Dict[str, Any]] = Field(None, description="Structured content elements")
    
    # Tables and data
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted tables")
    
    # Images and media
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted images")
    
    # Links and references
    links: List[str] = Field(default_factory=list, description="Extracted URLs")
    citations: List[str] = Field(default_factory=list, description="Academic citations")
    
    # Content statistics
    text_length: Optional[int] = Field(None, description="Text length in characters")
    paragraph_count: Optional[int] = Field(None, description="Number of paragraphs")
    sentence_count: Optional[int] = Field(None, description="Number of sentences")
    
    class Config:
        schema_extra = {
            "example": {
                "cleaned_text": "This document analyzes the current defense posture in Eastern Europe...",
                "text_length": 45000,
                "paragraph_count": 120,
                "sentence_count": 890,
                "tables": [
                    {
                        "title": "Defense Spending by Country",
                        "rows": 5,
                        "columns": 3,
                        "data": [["Country", "2023", "2024"], ["Poland", "2.4%", "2.8%"]]
                    }
                ],
                "links": ["https://nato.int/strategic-concept", "https://defense.gov/reports"]
            }
        }


class ProcessingResult(BaseModel):
    """Document processing result."""
    
    # Processing metadata
    processing_id: str = Field(..., description="Unique processing identifier")
    status: ProcessingStatus = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    
    # Source information
    source_uri: Optional[str] = Field(None, description="Source document URI")
    source_id: Optional[str] = Field(None, description="Source system identifier")
    
    # Processing results
    metadata: Optional[DocumentMetadata] = Field(None, description="Extracted metadata")
    content: Optional[ExtractedContent] = Field(None, description="Extracted content")
    
    # Processing statistics
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    processor_version: Optional[str] = Field(None, description="Processor version used")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    
    # Quality metrics
    overall_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall processing confidence")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Content quality score")
    
    class Config:
        schema_extra = {
            "example": {
                "processing_id": "proc_123456789",
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:32:15Z",
                "source_uri": "https://example.com/document.pdf",
                "processing_time_ms": 135000,
                "overall_confidence": 0.92,
                "quality_score": 0.88
            }
        }


class BatchProcessingResult(BaseModel):
    """Batch processing result."""
    
    batch_id: str = Field(..., description="Unique batch identifier")
    status: ProcessingStatus = Field(..., description="Batch processing status")
    created_at: datetime = Field(..., description="Batch start time")
    completed_at: Optional[datetime] = Field(None, description="Batch completion time")
    
    # Batch statistics
    total_documents: int = Field(..., description="Total number of documents")
    completed_documents: int = Field(0, description="Number of completed documents")
    failed_documents: int = Field(0, description="Number of failed documents")
    
    # Results
    results: List[ProcessingResult] = Field(default_factory=list, description="Individual processing results")
    
    # Batch metrics
    total_processing_time_ms: Optional[int] = Field(None, description="Total processing time")
    average_processing_time_ms: Optional[float] = Field(None, description="Average processing time per document")
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_987654321",
                "status": "completed",
                "created_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:15:30Z",
                "total_documents": 10,
                "completed_documents": 9,
                "failed_documents": 1,
                "total_processing_time_ms": 930000,
                "average_processing_time_ms": 93000
            }
        }


# =============================================================================
# HEALTH AND STATUS SCHEMAS
# =============================================================================

class ServiceHealth(BaseModel):
    """Service health status."""
    
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Health check timestamp")
    
    # Component health
    database_connected: bool = Field(..., description="Database connection status")
    redis_connected: bool = Field(..., description="Redis connection status")
    storage_connected: bool = Field(..., description="Object storage connection status")
    
    # Processing capabilities
    ocr_available: bool = Field(..., description="OCR capability status")
    language_detection_available: bool = Field(..., description="Language detection status")
    
    # Performance metrics
    active_processing_jobs: int = Field(0, description="Number of active processing jobs")
    queue_size: int = Field(0, description="Processing queue size")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "loreguard-normalize",
                "version": "0.1.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "database_connected": True,
                "redis_connected": True,
                "storage_connected": True,
                "ocr_available": True,
                "language_detection_available": True,
                "active_processing_jobs": 3,
                "queue_size": 12
            }
        }

