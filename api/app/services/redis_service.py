import json
import logging
from typing import Any, Dict, List, Optional, TypeVar, Union, Generic

from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RedisService(Generic[T]):
    """
    Redis 服务基类 - 提供更高级的 Redis 操作
    """
    
    def __init__(self, prefix: str):
        """
        初始化 Redis 服务
        
        Args:
            prefix: 键前缀，用于区分不同服务的数据
        """
        self.prefix = prefix
    
    def _get_key(self, key: str) -> str:
        """
        获取带前缀的完整键名
        """
        return f"{self.prefix}:{key}"
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取 JSON 数据
        """
        data = await redis_client.get(self._get_key(key))
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"Redis JSON decode error: {e}")
        return None
    
    async def set_json(self, key: str, value: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """
        设置 JSON 数据
        """
        try:
            json_data = json.dumps(value)
            return await redis_client.set(self._get_key(key), json_data, expire=expire)
        except (TypeError, json.JSONEncoder) as e:
            logger.error(f"Redis JSON encode error: {e}")
            return False
    
    async def get_object(self, key: str, model_class: type[T]) -> Optional[T]:
        """
        获取对象并自动转换为指定模型类
        """
        data = await self.get_json(key)
        if data:
            try:
                return model_class(**data)
            except Exception as e:
                logger.error(f"Model conversion error: {e}")
        return None
    
    async def set_object(self, key: str, obj: T, expire: Optional[int] = None) -> bool:
        """
        存储对象
        """
        if hasattr(obj, "dict"):  # Pydantic 模型支持
            return await self.set_json(key, obj.dict(), expire=expire)
        elif hasattr(obj, "__dict__"):  # 普通对象
            return await self.set_json(key, obj.__dict__, expire=expire)
        return False

class CacheService(RedisService):
    """
    缓存服务 - 用于缓存数据
    """
    
    def __init__(self):
        super().__init__("cache")
    
    async def get_cached_data(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        """
        return await self.get_json(key)
    
    async def cache_data(self, key: str, data: Any, expire_seconds: int = 3600) -> bool:
        """
        缓存数据
        """
        return await self.set_json(key, data, expire=expire_seconds)

# 实例化缓存服务供应用使用
cache_service = CacheService()
