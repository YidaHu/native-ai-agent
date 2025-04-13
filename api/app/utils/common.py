import hashlib
import json
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from app.core.logging import get_logger

logger = get_logger(__name__)

def generate_uuid() -> str:
    """生成UUID"""
    return str(uuid.uuid4())

def get_timestamp() -> int:
    """获取当前时间戳"""
    return int(datetime.now().timestamp())

def get_formatted_datetime(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取格式化的日期时间字符串
    
    Args:
        dt: 日期时间对象，默认为当前时间
        fmt: 格式化字符串
    
    Returns:
        格式化后的日期时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)

def md5(text: str) -> str:
    """
    计算字符串的MD5哈希值
    
    Args:
        text: 要计算哈希的字符串
    
    Returns:
        MD5哈希值的十六进制字符串
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def is_valid_email(email: str) -> bool:
    """
    验证邮箱格式是否有效
    
    Args:
        email: 邮箱地址
    
    Returns:
        是否为有效的邮箱格式
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串到指定长度
    
    Args:
        text: 输入字符串
        max_length: 最大长度
        suffix: 截断后添加的后缀
    
    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def safe_json_dumps(obj: Any) -> str:
    """
    安全的JSON序列化，处理日期时间等特殊类型
    
    Args:
        obj: 要序列化的对象
    
    Returns:
        JSON字符串
    """
    def json_serial(obj: Any) -> Union[str, Dict[str, Any]]:
        """JSON序列化器"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    try:
        return json.dumps(obj, default=json_serial, ensure_ascii=False)
    except Exception as e:
        logger.error(f"JSON serialization error: {e}")
        return "{}"

def safe_json_loads(json_str: str) -> Any:
    """
    安全的JSON反序列化
    
    Args:
        json_str: JSON字符串
    
    Returns:
        反序列化后的对象，失败则返回None
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"JSON deserialization error: {e}")
        return None
