import logging
import threading
import time
from typing import Optional, Dict, Any, Protocol
import asyncio
import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import settings

# 使用普通的logging而不是可能未正确配置的structlog
logger = logging.getLogger(__name__)


class StorageClientProtocol(Protocol):
    """存储客户端协议，定义存储接口"""
    async def initialize(self) -> None:
        """初始化存储"""
        ...
    
    async def close(self) -> None:
        """关闭存储"""
        ...
    
    async def get(self, key: str) -> Optional[str]:
        """获取键值"""
        ...
    
    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """设置键值"""
        ...
    
    async def delete(self, key: str) -> bool:
        """删除键"""
        ...
    
    async def ping(self) -> bool:
        """测试连接"""
        ...


class MemoryStorageClient:
    """基于内存的存储客户端，模拟Redis功能"""

    def __init__(self) -> None:
        self._storage: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}  # 存储过期时间
        self._initialized = False
        self._cleanup_task = None

    async def initialize(self) -> None:
        """初始化内存存储"""
        try:
            self._initialized = True
            self._storage = {}
            self._expiry = {}
            logger.info('Memory storage initialized successfully')
            
            # 启动定期清理过期键的任务
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_keys())
        except Exception as e:
            logger.error(f'Failed to initialize memory storage: {e}')
            self._initialized = False
            raise

    async def _cleanup_expired_keys(self) -> None:
        """定期清理过期的键"""
        while True:
            try:
                current_time = time.time()
                expired_keys = [k for k, v in self._expiry.items() if v <= current_time]
                
                for key in expired_keys:
                    del self._storage[key]
                    del self._expiry[key]
                
                if expired_keys:
                    logger.debug(f'Cleaned up {len(expired_keys)} expired keys')
            except Exception as e:
                logger.error(f'Error during cleanup: {e}')
            
            await asyncio.sleep(60)  # 每分钟检查一次

    async def close(self) -> None:
        """关闭存储客户端"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self._storage = {}
        self._expiry = {}
        self._initialized = False
        logger.info('Memory storage closed')

    async def get(self, key: str) -> Optional[str]:
        """获取键值"""
        if not self._initialized:
            return None
        
        # 检查是否过期
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._storage[key]
            del self._expiry[key]
            return None
        
        return self._storage.get(key)

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """设置键值"""
        if not self._initialized:
            return False
        
        try:
            self._storage[key] = value
            
            # 设置过期时间
            if expire is not None:
                self._expiry[key] = time.time() + expire
            elif key in self._expiry:
                del self._expiry[key]  # 如果没有指定过期时间，移除之前的过期设置
            
            return True
        except Exception as e:
            logger.error(f'Memory storage set error: {e}')
            return False

    async def delete(self, key: str) -> bool:
        """删除键"""
        if not self._initialized:
            return False
        
        try:
            if key in self._storage:
                del self._storage[key]
            
            if key in self._expiry:
                del self._expiry[key]
            
            return True
        except Exception as e:
            logger.error(f'Memory storage delete error: {e}')
            return False

    async def ping(self) -> bool:
        """测试连接"""
        return self._initialized


class RetryableRedisMixin:
    """为Redis客户端添加自动重试功能的Mixin"""

    async def execute_command(self, *args, **options):
        """执行Redis命令并在失败时自动重试"""
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                return await super().execute_command(*args, **options)
            except (ConnectionError, TimeoutError) as e:
                last_error = e
                if attempt == max_retries - 1:
                    logger.error(f'Redis operation failed after {max_retries} attempts: {e}')
                    raise
                logger.warning(f'Redis operation failed, attempt {attempt + 1}/{max_retries}: {e}')
                await asyncio.sleep(1)  # 短暂等待后重试

        raise last_error


class RetryableRedis(RetryableRedisMixin, redis.Redis):
    """带有自动重试功能的Redis客户端"""
    pass


class RedisClient:
    """Redis客户端封装类"""

    def __init__(self) -> None:
        self._redis: Optional[redis.Redis] = None
        self._keep_alive_thread = None

    async def initialize(self) -> None:
        """初始化Redis连接"""
        try:
            # 使用本地配置
            host = settings.REDIS_HOST
            port = settings.REDIS_PORT
            password = settings.REDIS_PASSWORD
            db = settings.REDIS_DB

            # 使用RetryableRedis替代标准Redis
            self._redis = RetryableRedis(
                host=host,
                port=port,
                password=password or None,
                db=db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30,
                retry_on_timeout=True,
            )

            # 测试连接
            await self._redis.ping()
            logger.info(f'Redis connection established successfully to {host}:{port}')

            # 启动保活线程
            # self._start_keep_alive()

        except RedisError as e:
            logger.error(f'Failed to initialize Redis connection: {e}')
            self._redis = None
            raise

    async def close(self) -> None:
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            logger.info('Redis connection closed')

        if self._keep_alive_thread and self._keep_alive_thread.is_alive():
            # 在实际代码中，我们无法直接停止守护线程
            # 这里只是记录日志，线程会随着程序退出而终止
            logger.info('Redis keep-alive thread will terminate with application')

    async def get(self, key: str) -> Optional[str]:
        """获取键值"""
        if not self._redis:
            return None
        try:
            return await self._redis.get(key)
        except RedisError as e:
            logger.error(f'Redis get error: {e}')
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """设置键值"""
        if not self._redis:
            return False
        try:
            await self._redis.set(key, value, ex=expire)
            return True
        except RedisError as e:
            logger.error(f'Redis set error: {e}')
            return False

    async def delete(self, key: str) -> bool:
        """删除键"""
        if not self._redis:
            return False
        try:
            await self._redis.delete(key)
            return True
        except RedisError as e:
            logger.error(f'Redis delete error: {e}')
            return False

    async def ping(self) -> bool:
        """测试连接"""
        if not self._redis:
            return False
        try:
            return await self._redis.ping()
        except RedisError as e:
            logger.error(f'Redis ping error: {e}')
            return False

    def _start_keep_alive(self, interval: int = 60) -> None:
        """启动Redis连接保活线程"""
        if self._keep_alive_thread and self._keep_alive_thread.is_alive():
            logger.debug('Keep-alive thread already running')
            return

        async def _ping_redis():
            while self._redis:
                try:
                    await self._redis.ping()
                    await asyncio.sleep(interval)
                except Exception as e:
                    # 使用安全的日志记录方式
                    print(f"Redis keep-alive ping failed: {e}")
                    logging.error(f"Redis keep-alive ping failed: {e}")
                    await asyncio.sleep(5)  # 失败后短暂等待再重试

        def _run_ping_loop():
            import asyncio

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_ping_redis())
            except Exception as e:
                print(f"Error in Redis ping loop: {e}")
                logging.error(f"Error in Redis ping loop: {e}")

        self._keep_alive_thread = threading.Thread(target=_run_ping_loop, daemon=True)
        self._keep_alive_thread.start()
        logger.debug('Redis keep-alive thread started')


# 根据环境变量USE_MEMORY_STORAGE决定使用哪种存储客户端
use_memory = settings.get_config('USE_MEMORY_STORAGE', True)

if use_memory:
    logger.info("Using in-memory storage client")
    redis_client = MemoryStorageClient()
else:
    logger.info("Using Redis storage client")
    redis_client = RedisClient()
