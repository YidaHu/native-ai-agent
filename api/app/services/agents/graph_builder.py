"""
LangGraph图构建器模块
"""
import logging
from typing import Any, Callable, Dict, List, Type

import langgraph.graph as graph
from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)


def build_graph(
    main_node_func: Callable,
    state_class: Type,
    main_node_name: str = "主节点",
    tool_handlers: Dict[str, Callable] = None,
    tools: List[Callable] = None,
) -> graph.Graph:
    """
    构建LangGraph任务图
    
    Args:
        main_node_func: 主节点函数，处理工具选择逻辑
        state_class: 状态类定义
        main_node_name: 主节点名称
        tool_handlers: 工具处理函数字典，键为工具名称，值为处理函数
        tools: 可用工具函数列表
        
    Returns:
        构建好的图对象
    """
    # 创建工作流图，指定状态类型
    workflow = graph.StateGraph(state_class)
    
    # 添加主节点
    workflow.add_node(main_node_name, main_node_func)
    
    # 设置主节点为入口节点
    workflow.set_entry_point(main_node_name)
    
    # 如果没有提供工具处理函数，使用工具列表自动创建
    if not tool_handlers and tools:
        tool_handlers = {}
        for tool in tools:
            def create_handler(tool_func):
                def handler(state):
                    # 从状态获取工具参数
                    tool_args = state.get('tool_args', {})
                    # 调用工具函数
                    result = tool_func(tool_input=tool_args)
                    # 将结果添加到消息列表
                    from langchain_core.messages import AIMessage
                    return {
                        'messages': state['messages'] + [AIMessage(content=result)],
                        'tool': '',
                        'tool_args': {},
                    }
                return handler
            
            # 使用工具名称创建处理函数
            tool_name = tool.__name__
            tool_handlers[tool_name] = create_handler(tool)
    
    # 添加所有工具节点
    if tool_handlers:
        for tool_name, handler in tool_handlers.items():
            node_name = f"{tool_name}_node"
            workflow.add_node(node_name, handler)
    
    # 添加条件路由
    def router(state):
        # 获取主节点选择的工具
        tool_name = state.get('tool', '')
        
        # 如果没有选择工具，结束流程
        if not tool_name:
            return END
        
        # 找到对应的工具节点
        return f"{tool_name}_node"
    
    # 从主节点连接到工具节点或结束
    workflow.add_conditional_edges(main_node_name, router)
    
    # 从工具节点连回主节点
    if tool_handlers:
        for tool_name in tool_handlers.keys():
            node_name = f"{tool_name}_node"
            workflow.add_edge(node_name, main_node_name)
    
    # 编译工作流
    app = workflow.compile()
    
    return app
