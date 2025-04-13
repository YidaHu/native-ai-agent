"""
运费险智能体使用的工具模块
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

def ask_for_good(tool_input: Optional[Dict[str, Any]] = None) -> str:
    """向用户索要商品信息。用于当用户只询问商品运费险但未提供具体商品时。"""
    logger.info('调用ask_for_good')
    return '请您提供想要查询的商品信息，例如商品ID、名称或链接，这样我可以为您查询该商品的运费险情况。'


def ask_for_order(tool_input: Optional[Dict[str, Any]] = None) -> str:
    """向用户索要订单信息。用于当用户只询问订单运费险但未提供订单号时。"""
    logger.info('调用ask_for_order')
    return '请您提供订单号，这样我可以为您查询该订单的运费险情况。'


def query_good_support(tool_input: Optional[Dict[str, Any]] = None) -> str:
    """查询商品是否支持运费险。当用户提供商品信息后调用。"""
    logger.info('调用query_good_support')
    tool_input = tool_input or {}
    
    # 模拟商品信息查询
    good_id = tool_input.get('good_id', '未知')
    good_name = tool_input.get('good_name', '食品')

    # 模拟不同的商品返回不同结果
    if '食品' in good_name or good_id == '123':
        return f'商品"{good_name}"(ID:{good_id})支持运费险。运费险政策：退货时运费可获得最高20元赔付，换货免运费。'
    else:
        return f'商品"{good_name}"(ID:{good_id})不支持运费险。'


def query_aftersales_by_order(tool_input: Optional[Dict[str, Any]] = None) -> str:
    """查询订单对应的售后单列表。当用户提供订单号后调用。"""
    logger.info('调用query_aftersales_by_order')
    tool_input = tool_input or {}
    
    # 模拟订单信息查询
    order_id = tool_input.get('order_id', '123456789')

    # 根据订单号模拟不同结果
    if order_id == '123456789':
        return f'订单{order_id}有2个售后单：\n1. 售后单号AS001：退货申请\n2. 售后单号AS002：换货申请\n请问您想查询哪个售后单的运费险状态？'
    elif order_id.startswith('12'):
        return f'订单{order_id}有1个售后单：售后单号AS003：退货申请。该售后单支持运费险，可获得12元运费补偿。'
    else:
        return f'订单{order_id}目前没有售后单记录。订单支持运费险，如需申请售后可享受运费保障。'


def select_aftersale(tool_input: Optional[Dict[str, Any]] = None) -> str:
    """选择特定售后单查询运费险状态"""
    logger.info('调用select_aftersale')
    tool_input = tool_input or {}
    
    aftersale_id = tool_input.get('aftersale_id', '')

    if aftersale_id == 'AS001':
        return f'售后单{aftersale_id}为退货类型，支持运费险。您可获得最高15元运费补偿。'
    elif aftersale_id == 'AS002':
        return f'售后单{aftersale_id}为换货类型，支持运费险。换货过程中产生的运费将由商家承担。'
    else:
        return f'售后单{aftersale_id}符合运费险条件，可获得运费补偿。'

# 导出所有工具函数
SHIPPING_FEE_TOOLS = [
    query_good_support,
    query_aftersales_by_order,
    ask_for_good, 
    ask_for_order, 
    select_aftersale
]
