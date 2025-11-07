"""
Chat API Schemas

Pydantic models for chat API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class ChatMessageCreate(BaseModel):
    """Schema for creating a new chat message"""
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    session_id: Optional[str] = Field(None, description="Existing session ID (create new if None)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "What rubrics do I have configured?",
                "session_id": None
            }
        }


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: str
    session_id: str
    role: str
    content: str
    token_count: Optional[int] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_results: Optional[List[Dict[str, Any]]] = None
    model_used: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatSessionSummary(BaseModel):
    """Schema for chat session summary (list view)"""
    id: str
    user_id: str
    title: Optional[str] = None
    message_count: int
    total_tokens: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None  # Preview of last user message
    
    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """Schema for full chat session with messages"""
    id: str
    user_id: str
    title: Optional[str] = None
    message_count: int
    total_tokens: int
    is_active: bool
    context_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    messages: List[ChatMessageResponse]
    
    class Config:
        from_attributes = True


class ChatCompletionRequest(BaseModel):
    """Schema for chat completion request"""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    use_tools: bool = Field(default=True, description="Enable tool/function calling")
    include_context: bool = Field(default=True, description="Include user context (rubrics, artifacts, etc.)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Override default temperature")
    max_tokens: Optional[int] = Field(None, description="Override default max tokens")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Show me my active rubric details",
                "session_id": None,
                "use_tools": True,
                "include_context": True
            }
        }


class ChatCompletionResponse(BaseModel):
    """Schema for chat completion response"""
    session_id: str
    message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    context_used: Dict[str, Any] = Field(default_factory=dict, description="Context information used")
    tokens_used: Dict[str, int] = Field(default_factory=dict, description="Token usage breakdown")
    tools_used: List[str] = Field(default_factory=list, description="Tools/functions called")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123",
                "message": {
                    "role": "user",
                    "content": "Show me my active rubric"
                },
                "assistant_message": {
                    "role": "assistant",
                    "content": "Your active rubric is version v0.1..."
                },
                "context_used": {
                    "rubrics_count": 3,
                    "artifacts_count": 42,
                    "sources_count": 9
                },
                "tokens_used": {
                    "prompt": 1500,
                    "completion": 350,
                    "total": 1850
                }
            }
        }


class ChatSessionListResponse(BaseModel):
    """Schema for paginated session list"""
    items: List[ChatSessionSummary]
    total: int
    skip: int
    limit: int


class SystemContextResponse(BaseModel):
    """Schema for system context information"""
    rubrics: List[Dict[str, Any]]
    artifacts_count: int
    sources_count: int
    active_jobs_count: int
    recent_evaluations: List[Dict[str, Any]]
    llm_providers: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "rubrics": [{"version": "v0.1", "is_active": True}],
                "artifacts_count": 42,
                "sources_count": 9,
                "active_jobs_count": 2,
                "recent_evaluations": [],
                "llm_providers": [{"name": "GPT-4", "status": "active"}]
            }
        }

