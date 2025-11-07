"""
LLM Provider model for managing LLM API configurations
"""

from sqlalchemy import Column, String, DateTime, JSON, Boolean, Text
from sqlalchemy.sql import func
import uuid

from db.database import Base


class LLMProvider(Base):
    """
    LLM Provider model for storing API configurations
    """
    __tablename__ = "llm_providers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)  # e.g., "GPT-4", "Claude-3"
    provider = Column(String(100), nullable=False, index=True)  # e.g., "openai", "anthropic"
    api_key = Column(Text, nullable=False)  # Encrypted API key
    base_url = Column(String(500))  # API base URL (optional, defaults to provider's URL)
    model = Column(String(100), nullable=False)  # Model identifier (e.g., "gpt-4", "claude-3-opus")
    status = Column(String(50), default="inactive", index=True)  # active, backup, inactive
    priority = Column(String(20), default="normal")  # primary, backup, normal
    
    # Configuration
    config = Column(JSON, default=dict)  # Provider-specific configuration
    max_tokens = Column(String(20))  # Max tokens per request
    temperature = Column(String(10))  # Default temperature
    timeout = Column(String(10))  # Request timeout in seconds
    
    # Usage tracking
    usage_count = Column(String(20), default="0")  # Number of requests made
    cost_per_token = Column(String(20))  # Cost tracking
    avg_response_time = Column(String(20))  # Average response time in seconds
    
    # Metadata
    description = Column(Text)  # Provider description/notes
    is_default = Column(Boolean, default=False, index=True)  # Default provider flag
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<LLMProvider(name='{self.name}', provider='{self.provider}', status='{self.status}')>"
    
    def get_decrypted_api_key(self) -> str:
        """Get decrypted API key (placeholder for encryption implementation)"""
        # TODO: Implement encryption/decryption
        return self.api_key
    
    def set_encrypted_api_key(self, api_key: str):
        """Set encrypted API key (placeholder for encryption implementation)"""
        # TODO: Implement encryption
        self.api_key = api_key

