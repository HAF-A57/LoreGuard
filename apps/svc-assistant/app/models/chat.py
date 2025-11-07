"""
Chat Session and Message Models

Database models for storing chat sessions and messages with context tracking.
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid
import sys
from pathlib import Path

# Import Base from assistant's database module (which handles the svc-api import)
from app.core.database import Base


class ChatSession(Base):
    """
    Chat session model representing a conversation thread
    """
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)  # User identifier (email or ID)
    title = Column(String(500))  # Auto-generated or user-defined title
    
    # Context tracking
    total_tokens = Column(Integer, default=0)  # Running token count
    message_count = Column(Integer, default=0)  # Number of messages
    context_summary = Column(Text)  # Summarized context for older messages
    
    # Metadata
    is_active = Column(Boolean, default=True, index=True)  # Active conversation
    session_metadata = Column(JSON, default=dict)  # Additional session metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True))
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    
    def __repr__(self):
        return f"<ChatSession(id='{self.id}', user='{self.user_id}', messages={self.message_count})>"
    
    def add_message_tokens(self, tokens: int):
        """Add tokens to the running count"""
        self.total_tokens = (self.total_tokens or 0) + tokens
    
    def update_activity(self):
        """Update last message timestamp"""
        self.last_message_at = datetime.now(timezone.utc)
        self.message_count = (self.message_count or 0) + 1


class ChatMessage(Base):
    """
    Chat message model representing individual messages in a conversation
    """
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    
    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)  # Message content
    
    # Token tracking
    token_count = Column(Integer)  # Token count for this message
    
    # Tool/function calling
    tool_calls = Column(JSON)  # Function/tool calls made by assistant
    tool_call_results = Column(JSON)  # Results from tool executions
    function_name = Column(String(255))  # Name of function called (if applicable)
    
    # Metadata
    model_used = Column(String(100))  # LLM model that generated this message
    message_metadata = Column(JSON, default=dict)  # Additional message metadata
    
    # Context management flags
    is_summarized = Column(Boolean, default=False)  # Whether this message has been summarized
    is_included_in_context = Column(Boolean, default=True)  # Whether to include in context window
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id='{self.id}', role='{self.role}', session='{self.session_id}')>"
    
    def to_llm_format(self) -> dict:
        """Convert message to LLM API format"""
        msg = {
            "role": self.role,
            "content": self.content
        }
        
        # Add tool calls if present (for assistant messages)
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        
        # Add tool_call_id if this is a tool response message
        if self.role == "tool":
            if self.message_metadata and "tool_call_id" in self.message_metadata:
                msg["tool_call_id"] = self.message_metadata["tool_call_id"]
            elif self.tool_call_results and len(self.tool_call_results) > 0:
                msg["tool_call_id"] = self.tool_call_results[0].get("tool_call_id")
        
        return msg

