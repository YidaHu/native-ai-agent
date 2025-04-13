"""
智能体API端点
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.schemas.agents import (
    Message,
    MessageRequest,
    MessageResponse,
    MessageRole,
    SessionDetailResponse,
    SessionInfo,
    SessionListResponse,
)
from app.services.agents.shipping_fee_agent import shipping_fee_agent
from app.services.session_service import session_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    '/shipping-fee/chat',
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary='运费险助手对话',
    description='向运费险助手发送消息并获取回复',
)
async def chat_with_shipping_fee_agent(request: MessageRequest):
    """
    与运费险助手对话，发送消息并获取回复
    """
    session_id = request.session_id

    # 如果没有提供会话ID，创建新会话
    if not session_id:
        session_id = await session_service.create_session(request.user_id)
        state = None
    else:
        # 获取现有会话数据
        session_data = await session_service.get_session(session_id)
        if not session_data:
            session_id = await session_service.create_session(request.user_id)
            state = None
        else:
            state = session_data.get('state', None)

    # 处理用户消息
    result = shipping_fee_agent.process_message(request.content, session_id, state)

    # 将用户消息和助手回复保存到会话历史
    await session_service.add_message(
        session_id,
        {'role': MessageRole.USER, 'content': request.content},
        result['state'],  # 更新状态
    )

    # 保存助手回复
    await session_service.add_message(
        session_id,
        {'role': MessageRole.ASSISTANT, 'content': result['reply']},
        result['state'],  # 更新状态
    )

    return MessageResponse(reply=result['reply'], session_id=session_id, created_at=datetime.now())


@router.get(
    '/sessions',
    response_model=SessionListResponse,
    status_code=status.HTTP_200_OK,
    summary='获取会话列表',
    description='获取用户的会话列表',
)
async def list_sessions(
    user_id: Optional[str] = Query(None, description='用户ID，不提供则获取所有会话'),
    limit: int = Query(10, ge=1, le=50, description='每页数量'),
    skip: int = Query(0, ge=0, description='跳过数量'),
):
    """获取会话列表"""
    # 这里需要实现从Redis中获取会话列表的逻辑
    # 简化实现，实际应用需要根据Redis的存储结构进行查询

    # 示例返回
    return SessionListResponse(
        sessions=[
            # 示例数据，实际应用需要从Redis获取
            SessionInfo(
                id='session-1',
                created_at=datetime.now(),
                updated_at=datetime.now(),
                user_id=user_id or 'anonymous',
                message_count=5,
            )
        ],
        total=1,
    )


@router.get(
    '/sessions/{session_id}',
    response_model=SessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary='获取会话详情',
    description='获取特定会话的详细信息和消息历史',
)
async def get_session_detail(session_id: str):
    """获取会话详情"""
    session_data = await session_service.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='会话不存在')

    # 转换为API响应模型
    messages = []
    for msg in session_data.get('messages', []):
        role = msg.get('role')
        content = msg.get('content')
        timestamp_str = msg.get('timestamp')

        try:
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        except ValueError:
            timestamp = datetime.now()

        messages.append(Message(role=role, content=content, timestamp=timestamp))

    return SessionDetailResponse(
        id=session_id,
        created_at=datetime.fromisoformat(session_data.get('created_at', datetime.now().isoformat())),
        updated_at=datetime.fromisoformat(session_data.get('updated_at', datetime.now().isoformat()))
        if 'updated_at' in session_data
        else None,
        user_id=session_data.get('user_id'),
        messages=messages,
    )


@router.delete(
    '/sessions/{session_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='删除会话',
    description='删除特定会话及其所有消息历史',
)
async def delete_session(session_id: str):
    """删除会话"""
    success = await session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='会话不存在或删除失败')
    return None
