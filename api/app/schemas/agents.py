"""
智能体API模型
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageRequest(BaseModel):
    """消息请求模型"""
    content: str = Field(..., description="消息内容")
    session_id: Optional[str] = Field(None, description="会话ID，如不提供则创建新会话")
    user_id: Optional[str] = Field(None, description="用户ID")


class Message(BaseModel):
    """消息模型"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")


class MessageResponse(BaseModel):
    """消息响应模型"""
    reply: str = Field(..., description="助手回复内容")
    session_id: str = Field(..., description="会话ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class SessionInfo(BaseModel):
    """会话信息模型"""
    id: str = Field(..., description="会话ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")
    user_id: Optional[str] = Field(None, description="用户ID")
    message_count: int = Field(0, description="消息数量")


class SessionListResponse(BaseModel):
    """会话列表响应模型"""
    sessions: List[SessionInfo] = Field(default_factory=list, description="会话列表")
    total: int = Field(0, description="会话总数")


class SessionDetailResponse(BaseModel):
    """会话详情响应模型"""
    id: str = Field(..., description="会话ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")
    user_id: Optional[str] = Field(None, description="用户ID")
    messages: List[Message] = Field(default_factory=list, description="消息历史")
