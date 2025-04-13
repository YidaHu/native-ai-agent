"""
大模型问答API端点
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.agents import MessageRole
from app.services.llm_service import get_llm_response
from app.services.session_service import session_service

logger = logging.getLogger(__name__)

router = APIRouter()


# 大模型问答请求模型
class LLMQuestionRequest(BaseModel):
    session_id: Optional[str] = None
    question: str = Field(..., description='用户问题')
    user_id: Optional[str] = None
    model_params: Optional[Dict[str, Any]] = Field(None, description='模型参数，可包含api_key, base_url, model_name等')
    include_history: bool = Field(True, description='是否包含对话历史')
    max_history_turns: int = Field(10, description='最大历史回合数', ge=0, le=20)


# 大模型问答响应模型
class LLMQuestionResponse(BaseModel):
    reply: str = Field(..., description='模型回答')
    session_id: str = Field(..., description='会话ID')
    created_at: datetime = Field(default_factory=datetime.now, description='创建时间')


@router.post(
    '/question',
    response_model=LLMQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary='大模型问答',
    description='向大模型提问并获取回答',
)
async def ask_llm_question(request: LLMQuestionRequest):
    """
    向大模型提问并获取回答

    接收用户问题，调用OpenAI API获取回答，并保存到会话历史中
    """
    try:
        session_id = request.session_id
        conversation_history = []

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

                # 如果需要包含历史对话，从会话中提取
                if request.include_history and 'messages' in session_data:
                    # 提取对话历史
                    messages = session_data.get('messages', [])
                    # 限制历史消息数量，避免超出token限制
                    max_turns = min(request.max_history_turns * 2, len(messages))
                    recent_messages = messages[-max_turns:] if max_turns > 0 else []

                    # 转换为LLM API所需的格式
                    for msg in recent_messages:
                        role = msg.get('role', '').lower()
                        # 仅包含用户和助手的消息
                        if role in ['user', 'assistant']:
                            conversation_history.append({'role': role, 'content': msg.get('content', '')})

        # 获取模型参数
        model_params = request.model_params or {}

        # 调用大模型获取回答，传入对话历史
        answer = await get_llm_response(request.question, model_params, conversation_history)

        # 将用户问题保存到会话历史
        await session_service.add_message(
            session_id,
            {'role': MessageRole.USER, 'content': request.question},
            state,  # 更新状态
        )

        # 保存模型回答
        await session_service.add_message(
            session_id,
            {'role': MessageRole.ASSISTANT, 'content': answer},
            state,  # 更新状态
        )

        # 更新会话状态
        await session_service.update_session(
            session_id=session_id,
            data={
                'updated_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
            },
        )

        return LLMQuestionResponse(
            reply=answer,
            session_id=session_id,
            created_at=datetime.now(),
        )
    except Exception as e:
        # 记录错误并返回适当的错误消息
        logger.error(f'Error in LLM question: {str(e)}')
        raise HTTPException(status_code=500, detail=f'处理问题时发生错误: {str(e)}')
