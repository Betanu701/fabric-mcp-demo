"""
Pydantic models for chat and conversation.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message."""
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    message: str = Field(..., description="User message", min_length=1)
    agent_id: Optional[str] = Field(default=None, description="Specific agent ID to use")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    stream: bool = Field(default=False, description="Stream response")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    message: str = Field(..., description="Assistant response")
    agent_id: str = Field(..., description="Agent that handled the request")
    conversation_id: str = Field(..., description="Conversation ID")
    sources_used: List[str] = Field(default_factory=list, description="Data sources queried")
    tokens_used: int = Field(default=0, description="Tokens consumed")
    latency_ms: int = Field(default=0, description="Response latency")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """Conversation history."""
    id: str = Field(..., description="Conversation ID")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationHistoryResponse(BaseModel):
    """Response for conversation history."""
    conversations: List[Conversation]
    total: int
    tenant_id: str
