"""
Chat API Endpoints

API endpoints for AI assistant chat functionality.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List
import sys
from pathlib import Path

from app.core.database import get_db

# Import LLMProvider from svc-api using container path
import sys
from pathlib import Path

# Try container path first, then local dev path
possible_paths = [
    Path('/app/svc-api-app'),  # Container path
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent / 'svc-api' / 'app',  # Local dev
]

models_path = None
for path in possible_paths:
    models_dir = path / 'models'
    if models_dir.exists():
        models_path = path
        if str(models_path) not in sys.path:
            sys.path.insert(0, str(models_path))
        break

if models_path:
    # Import Base from assistant's database module first (this sets up db.database.Base)
    from app.core.database import Base as AssistantBase
    
    # Ensure db.database.Base is set
    if 'db.database' in sys.modules:
        sys.modules['db.database'].Base = AssistantBase
    
    # Import LLMProvider - db.database.Base is already set up
    from models.llm_provider import LLMProvider
else:
    raise ImportError("Could not find svc-api models directory")

from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatSessionResponse,
    ChatSessionSummary,
    ChatSessionListResponse,
    ChatMessageResponse,
    SystemContextResponse
)
from app.services.llm_client import LLMClient
from app.services.chat_manager import ChatSessionManager
from app.services.context_service import ContextRetrievalService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_user_llm_config(db: Session) -> dict:
    """Get user's configured LLM provider"""
    # Get default provider
    provider = db.query(LLMProvider).filter(
        LLMProvider.is_default == True,
        LLMProvider.status == "active"
    ).first()
    
    if not provider:
        # Fallback to first active provider
        provider = db.query(LLMProvider).filter(
            LLMProvider.status == "active"
        ).first()
    
    if provider:
        return {
            "provider": provider.provider,
            "api_key": provider.api_key,
            "model": provider.model,
            "base_url": provider.base_url,
            "temperature": provider.temperature,
            "max_tokens": provider.max_tokens
        }
    
    return None


@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest = Body(...),
    user_id: str = Query("default_user", description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Create a chat completion
    
    Processes user message, maintains conversation context, executes tools if needed,
    and returns assistant response.
    """
    try:
        # Get user's LLM configuration
        llm_config = get_user_llm_config(db)
        
        if not llm_config:
            raise HTTPException(
                status_code=400,
                detail="No active LLM provider configured. Please configure an LLM provider in Settings."
            )
        
        # Initialize services
        llm_client = LLMClient(llm_config)
        chat_manager = ChatSessionManager(db, llm_client)
        context_service = ContextRetrievalService(db)
        
        # Get or create session
        if request.session_id:
            session = chat_manager.get_session(request.session_id, user_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            session = chat_manager.create_session(user_id)
        
        # Process message
        result = await chat_manager.process_user_message(
            session=session,
            user_message=request.message,
            use_tools=request.use_tools,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Get context used
        context_used = {}
        if request.include_context:
            context = context_service.get_full_context(user_id, include_details=False)
            context_used = {
                "rubrics_count": context["rubrics"]["count"],
                "artifacts_count": context["artifacts"]["total_count"],
                "sources_count": context["sources"]["total_count"],
                "active_jobs_count": context["jobs"]["running"]
            }
        
        # Cleanup
        await chat_manager.cleanup()
        
        # Build response (convert UUIDs to strings)
        return ChatCompletionResponse(
            session_id=str(session.id),
            message=ChatMessageResponse(
                id=str(result["user_message"].id),
                session_id=str(session.id),
                role=result["user_message"].role,
                content=result["user_message"].content,
                token_count=result["user_message"].token_count,
                created_at=result["user_message"].created_at
            ),
            assistant_message=ChatMessageResponse(
                id=str(result["assistant_message"].id),
                session_id=str(session.id),
                role=result["assistant_message"].role,
                content=result["assistant_message"].content,
                token_count=result["assistant_message"].token_count,
                tool_calls=result["assistant_message"].tool_calls,
                model_used=result["assistant_message"].model_used,
                created_at=result["assistant_message"].created_at
            ),
            context_used=context_used,
            tokens_used=result["usage"],
            tools_used=result.get("tools_used", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat completion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    user_id: str = Query("default_user", description="User identifier"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(False, description="Only show active sessions"),
    db: Session = Depends(get_db)
):
    """
    List user's chat sessions
    
    Returns paginated list of chat sessions ordered by most recent activity.
    """
    try:
        # Get LLM client for session manager
        llm_config = get_user_llm_config(db) or {}
        llm_client = LLMClient(llm_config)
        chat_manager = ChatSessionManager(db, llm_client)
        
        sessions, total = chat_manager.list_user_sessions(
            user_id=user_id,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        # Convert to response format
        items = []
        for session in sessions:
            # Get last user message for preview
            last_user_msg = next(
                (msg for msg in reversed(session.messages) if msg.role == "user"),
                None
            )
            
            items.append(ChatSessionSummary(
                id=str(session.id),
                user_id=session.user_id,
                title=session.title,
                message_count=session.message_count or 0,
                total_tokens=session.total_tokens or 0,
                is_active=session.is_active,
                created_at=session.created_at,
                updated_at=session.updated_at,
                last_message_at=session.last_message_at,
                last_message_preview=last_user_msg.content[:100] if last_user_msg else None
            ))
        
        return ChatSessionListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    user_id: str = Query("default_user", description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Get a specific chat session with all messages
    
    Returns full conversation history for the session.
    """
    try:
        # Get LLM client
        llm_config = get_user_llm_config(db) or {}
        llm_client = LLMClient(llm_config)
        chat_manager = ChatSessionManager(db, llm_client)
        
        session = chat_manager.get_session_with_messages(session_id, user_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert messages (convert UUIDs to strings)
        messages = [
            ChatMessageResponse(
                id=str(msg.id),
                session_id=str(msg.session_id),
                role=msg.role,
                content=msg.content,
                token_count=msg.token_count,
                tool_calls=msg.tool_calls,
                tool_call_results=msg.tool_call_results,
                model_used=msg.model_used,
                created_at=msg.created_at
            )
            for msg in session.messages
        ]
        
        return ChatSessionResponse(
            id=str(session.id),
            user_id=session.user_id,
            title=session.title,
            message_count=session.message_count or 0,
            total_tokens=session.total_tokens or 0,
            is_active=session.is_active,
            context_summary=session.context_summary,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_message_at=session.last_message_at,
            messages=messages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    user_id: str = Query("default_user", description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Delete a chat session
    
    Permanently removes the session and all its messages.
    """
    try:
        llm_config = get_user_llm_config(db) or {}
        llm_client = LLMClient(llm_config)
        chat_manager = ChatSessionManager(db, llm_client)
        
        success = chat_manager.delete_session(session_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.post("/sessions/{session_id}/archive")
async def archive_chat_session(
    session_id: str,
    user_id: str = Query("default_user", description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Archive a chat session
    
    Marks session as inactive but keeps the data.
    """
    try:
        llm_config = get_user_llm_config(db) or {}
        llm_client = LLMClient(llm_config)
        chat_manager = ChatSessionManager(db, llm_client)
        
        success = chat_manager.archive_session(session_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session archived successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to archive session: {str(e)}")


@router.get("/context", response_model=SystemContextResponse)
async def get_system_context(
    user_id: str = Query("default_user", description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Get user's LoreGuard environment context
    
    Returns information about rubrics, artifacts, sources, jobs, and providers.
    """
    try:
        context_service = ContextRetrievalService(db)
        context = context_service.get_full_context(user_id, include_details=True)
        
        # Extract specific fields for response
        return SystemContextResponse(
            rubrics=context["rubrics"].get("all_rubrics", []),
            artifacts_count=context["artifacts"]["total_count"],
            sources_count=context["sources"]["total_count"],
            active_jobs_count=context["jobs"]["running"],
            recent_evaluations=context["evaluations"].get("recent", []),
            llm_providers=context["llm_providers"]["providers"]
        )
        
    except Exception as e:
        logger.error(f"Error getting context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")

