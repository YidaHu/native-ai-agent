"""
LLM服务模块 - 负责与大模型API交互
"""

from typing import Any, Dict, List, Optional
from app.core.config import settings

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_llm_response(
    question: str,
    model_params: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    调用OpenAI API获取大模型回答

    Args:
        question: 用户提问
        model_params: 模型参数，可包含api_key, base_url, model_name等
        conversation_history: 对话历史消息列表，格式为[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    Returns:
        模型的回答文本
    """
    # 合并配置和请求参数
    api_key = settings.get_config('LLM_API_KEY', 'Your API Key')
    base_url = settings.get_config('LLM_API_BASE', 'Your Base URL')
    model_name = settings.get_config('LLM_MODEL_NAME', 'Your Model Name')
    temperature = model_params.get('temperature', 0.7)
    max_tokens = model_params.get('max_tokens', 1024)

    if not api_key:
        logger.error('未提供API密钥')
        return '抱歉，服务未正确配置，无法回答您的问题。请联系管理员。'

    # 构造请求URL
    url = f"{base_url.rstrip('/')}/chat/completions"

    # 构造请求头
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}

    # 构建消息列表
    messages = [{'role': 'system', 'content': '你是一个有帮助的助手，请简洁、准确地回答用户问题。'}]

    # 如果有对话历史，添加到消息列表中
    if conversation_history:
        messages.extend(conversation_history)

    # 添加当前问题
    messages.append({'role': 'user', 'content': question})

    # 构造请求体
    payload = {
        'model': model_name,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }

    try:
        # 记录请求信息
        logger.info(f'发送请求到LLM API: {url}, 模型: {model_name}, 消息数: {len(messages)}')

        # 发送请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            # 检查响应状态
            response.raise_for_status()

            # 解析响应
            result = response.json()

            # 提取回答
            if 'choices' in result and len(result['choices']) > 0:
                answer = result['choices'][0]['message']['content'].strip()
                return answer
            else:
                logger.error(f'无效的API响应: {result}')
                return '抱歉，无法获取有效回答，请稍后再试。'

    except httpx.HTTPStatusError as e:
        logger.error(f'HTTP错误: {e.response.status_code} - {e.response.text}')
        return f'抱歉，请求出错 (HTTP {e.response.status_code})，请稍后再试。'

    except httpx.RequestError as e:
        logger.error(f'请求错误: {e}')
        return '抱歉，连接服务时出现问题，请稍后再试。'

    except Exception as e:
        logger.error(f'获取LLM回答时出错: {e}')
        return '抱歉，处理您的问题时出现错误，请稍后再试。'
