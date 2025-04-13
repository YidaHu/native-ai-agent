"""
运费险智能体模块
"""

import json
import logging
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages

from app.core.config import settings
from app.services.agents.graph_builder import build_graph
from app.services.agents.prompts import (
    SHIPPING_FEE_RESPONSE_PROMPT,
    SHIPPING_FEE_SYSTEM_PROMPT,
)
from app.services.agents.tools import SHIPPING_FEE_TOOLS

logger = logging.getLogger(__name__)


# 定义状态类型
class ShippingFeeState(TypedDict):
    """运费险助手状态"""

    tool: str  # 当前选择的工具
    tool_args: Dict[str, Any]  # 工具参数
    last_tool: Optional[str]  # 上一次使用的工具
    messages: Annotated[List, add_messages]  # 消息历史


class ShippingFeeAgent:
    """运费险智能体"""

    def __init__(self):
        """初始化运费险代理"""
        self.tools = SHIPPING_FEE_TOOLS
        self.llm = self._create_llm()
        self.graph = self._build_graph()

    def _create_llm(self) -> ChatOpenAI:
        """创建语言模型实例"""
        # 从配置中获取API密钥和URL
        api_key = settings.get_config('LLM_API_KEY', 'Your API Key')
        base_url = settings.get_config('LLM_API_BASE', 'Your Base URL')
        model_name = settings.get_config('LLM_MODEL_NAME', 'Your Model Name')

        return ChatOpenAI(openai_api_key=api_key, openai_api_base=base_url, model_name=model_name, temperature=0)

    def _build_graph(self):
        """构建任务图"""
        return build_graph(
            main_node_func=self._apply_agent_node,
            state_class=ShippingFeeState,
            main_node_name='运费险助手节点',
            tools=self.tools,
        )

    def _apply_agent_node(self, state: ShippingFeeState) -> Dict[str, Any]:
        """主节点函数：决定使用哪个工具或直接回复"""
        logger.info('运费险助手节点正在思考，准备调用工具')

        # 构建上下文信息
        context_info = {
            'conversation_turns': len([m for m in state['messages'] if isinstance(m, HumanMessage)]),
            'last_tool_used': state.get('last_tool', None),
            'available_tools': [t.__name__ for t in self.tools],
        }

        context_prompt = f"""
当前对话信息:
- 对话轮数: {context_info['conversation_turns']}
- 上次使用的工具: {context_info['last_tool_used'] or '无'}
- 可用工具: {', '.join(context_info['available_tools'])}

请基于上下文决定是调用工具还是直接回复用户。如果决定调用工具，请选择最合适的工具。
""".strip()

        # 为模型提供增强的系统提示
        enhanced_system = SHIPPING_FEE_SYSTEM_PROMPT + '\n\n' + context_prompt

        # 绑定工具并调用模型
        llm_with_tools = self.llm.bind_tools(self.tools)
        resp = llm_with_tools.invoke([SystemMessage(content=enhanced_system)] + state['messages'])

        if resp.tool_calls and len(resp.tool_calls) > 0:
            tool_call = resp.tool_calls[0]
            # 输出工具调用结构以便调试
            logger.info(f'工具调用结构: {json.dumps(tool_call)}')

            # 获取函数名称
            function_name = tool_call['name']

            # 提取工具参数
            arguments = self._extract_tool_arguments(tool_call)
            logger.info(f'主节点思考完成，准备调用：{function_name}，参数：{arguments}')

            # 返回决策，包括工具信息
            return {
                'messages': state['messages'],
                'tool': function_name,
                'tool_args': arguments,
                'last_tool': function_name,
            }
        else:
            # 模型决定直接回复
            logger.info('模型决定直接回复而不是调用工具')
            reply = self.generate_natural_response(state['messages'])
            return {
                'messages': state['messages'] + [reply],
                'tool': '',
                'tool_args': {},
                'last_tool': state.get('last_tool'),
            }

    def _extract_tool_arguments(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """从工具调用中提取参数"""
        arguments = {}
        possible_arg_keys = ['arguments', 'args', 'argument', 'arg', 'tool_input']

        for key in possible_arg_keys:
            if key in tool_call:
                arg_value = tool_call[key]
                if isinstance(arg_value, dict):
                    arguments = arg_value
                    break
                elif isinstance(arg_value, str):
                    try:
                        parsed_args = json.loads(arg_value)
                        if isinstance(parsed_args, dict):
                            arguments = parsed_args
                            break
                    except json.JSONDecodeError:
                        pass

        # 如果参数在args.tool_input中
        if 'args' in tool_call and isinstance(tool_call['args'], dict):
            if 'tool_input' in tool_call['args']:
                tool_input = tool_call['args']['tool_input']
                if isinstance(tool_input, dict):
                    arguments = tool_input

        return arguments

    def generate_natural_response(self, messages: List) -> AIMessage:
        """生成自然语言回复"""
        # 构建请求上下文
        context_messages = [SystemMessage(content=SHIPPING_FEE_RESPONSE_PROMPT)]

        # 添加用户对话历史，最多保留最近10条消息
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        context_messages.extend(recent_messages)

        # 生成回复
        response = self.llm.invoke(context_messages)
        return response

    def process_message(self, message: str, session_id: str = None, state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理用户消息，返回回复和更新后的状态

        Args:
            message: 用户消息内容
            session_id: 会话ID，用于状态管理
            state: 当前会话状态，如果为None则创建新状态

        Returns:
            包含回复内容和更新后状态的字典
        """
        # 如果没有提供状态，创建新状态
        if state is None:
            state = {'messages': [], 'tool': '', 'tool_args': {}, 'last_tool': None}

        # 添加用户消息到状态
        user_message = HumanMessage(content=message)
        state['messages'].append(user_message)

        # 调用图执行流程
        result = self.graph.invoke(state)

        # 查找最后一条AI消息
        last_ai_message = next((msg for msg in reversed(result['messages']) if isinstance(msg, AIMessage)), None)

        # 如果图执行后没有AI消息，生成新回复
        if not last_ai_message or last_ai_message in state['messages']:
            response = self.generate_natural_response(result['messages'])
            result['messages'].append(response)
            last_ai_message = response

        # 提取回复内容
        reply_content = self._format_message(last_ai_message)

        return {'reply': reply_content, 'state': result}

    def _format_message(self, message) -> str:
        """格式化消息，只显示内容部分"""
        if hasattr(message, 'content'):
            return message.content
        elif isinstance(message, dict) and 'content' in message:
            return message['content']
        else:
            return str(message)


# 创建全局智能体实例
shipping_fee_agent = ShippingFeeAgent()
