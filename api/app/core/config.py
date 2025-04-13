from typing import Any, Dict, List, Optional
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_PREFIX: str = '/nativeai'
    PROJECT_NAME: str = 'NativeAI Python'
    PROJECT_DESCRIPTION: str = 'FastAPI Backend Service'
    PROJECT_VERSION: str = '0.1.0'
    DEBUG: bool = False

    # 服务器配置
    SERVER_HOST: str = '0.0.0.0'
    SERVER_PORT: int = 8000

    # 日志配置
    LOG_LEVEL: str = 'INFO'

    # CORS配置 - 使用简单的字符串而非复杂类型
    CORS_ORIGINS_STR: str = 'http://localhost:3000,http://localhost:8080'

    # 存储配置
    USE_MEMORY_STORAGE: bool = True  # 默认使用内存存储

    # Redis配置 (仅在USE_MEMORY_STORAGE=False时使用)
    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # 添加LLM配置
    LLM_API_KEY: Optional[str] = None
    LLM_API_BASE: Optional[str] = ''
    LLM_MODEL_NAME: str = ''

    # 会话配置
    SESSION_TTL_SECONDS: int = 3600 * 24  # 默认会话保存24小时

    class Config:
        case_sensitive = True
        env_file = '.env'
        env_file_encoding = 'utf-8'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 确保_dynamic_configs被初始化为实例属性
        self._dynamic_configs = {}

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """将逗号分隔的字符串转换为列表"""
        if not self.CORS_ORIGINS_STR:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(',') if origin.strip()]

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，包括环境变量、动态配置

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值或默认值
        """
        # 首先检查环境变量
        env_key = key.upper()
        env_value = os.environ.get(env_key)
        if env_value is not None:
            # 处理布尔值
            if env_value.lower() in ('true', 'yes', '1'):
                return True
            if env_value.lower() in ('false', 'no', '0'):
                return False
            return env_value
                
        # 检查常规属性
        if hasattr(self, key) and getattr(self, key) is not None:
            return getattr(self, key)

        # 检查大写属性
        if hasattr(self, env_key) and getattr(self, env_key) is not None:
            return getattr(self, env_key)

        # 确保_dynamic_configs存在，防止递归
        dynamic_configs = getattr(self, '_dynamic_configs', {})

        # 检查动态配置
        if key in dynamic_configs:
            return dynamic_configs[key]

        # 返回默认值
        return default

    def __getattr__(self, name: str) -> Any:
        """
        重写__getattr__以支持动态访问配置

        Args:
            name: 属性名

        Returns:
            属性值

        Raises:
            AttributeError: 属性不存在
        """
        # 特殊处理_dynamic_configs，避免递归
        if name == '_dynamic_configs':
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        # 安全获取_dynamic_configs
        dynamic_configs = getattr(self, '_dynamic_configs', {})

        # 检查动态配置
        if name in dynamic_configs:
            return dynamic_configs[name]

        # 检查大写键
        if name.upper() in dynamic_configs:
            return dynamic_configs[name.upper()]

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def get_all_configs(self) -> Dict[str, Any]:
        """
        获取所有配置，包括预定义和动态配置

        Returns:
            所有配置的字典
        """
        # 收集预定义的属性，排除私有属性和方法
        result = {}
        for key in self.__class__.__fields__:
            if not key.startswith('_'):
                result[key] = getattr(self, key)

        # 添加动态配置，确保_dynamic_configs存在
        dynamic_configs = getattr(self, '_dynamic_configs', {})
        result.update(dynamic_configs)

        return result


# 创建全局设置实例
settings = Settings()
