"""
Document processing endpoints.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.services.document_processing_service import DocumentProcessingService

router = APIRouter()


class ProcessDocumentRequest(BaseModel):
    """Request model for document processing"""
    artifact_id: str = Field(..., description="Artifact ID to process")
    processing_options: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional processing configuration"
    )


@router.post("/process")
async def process_document(request: ProcessDocumentRequest = Body(...)):
    """
    Process a document artifact.
    
    Fetches artifact content from storage, extracts text and metadata,
    stores normalized content, and updates the artifact record.
    
    Args:
        request: ProcessDocumentRequest with artifact_id and optional processing_options
        
    Returns:
        Processing results with normalized_ref and metadata
    """
    service = DocumentProcessingService()
    
    try:
        result = await service.process_artifact(
            artifact_id=request.artifact_id,
            processing_options=request.processing_options
        )
        
        return {
            "message": "Document processed successfully",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error processing document: {str(e)}"
        )

