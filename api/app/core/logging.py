import logging
import sys
from typing import Optional

import structlog

from app.core.config import settings

def configure_logging() -> None:
    """配置日志系统"""
    
    # 设置基本日志级别
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # 配置Python标准库日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,  # 强制重新配置，避免重复配置的问题
    )
    
    # 确保所有日志处理器都有正确的级别
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        if logger.level == logging.NOTSET:
            logger.setLevel(log_level)
    
    # 配置structlog
    structlog.configure(
        processors=[
            # 添加日志级别名称
            structlog.stdlib.add_log_level,
            # 添加调用者信息
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            # 按日志级别过滤 - 使用stdlib中的过滤器
            structlog.stdlib.filter_by_level,
            # 添加时间戳
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            # 以JSON格式或漂亮格式渲染日志
            structlog.processors.JSONRenderer() if not settings.DEBUG else structlog.dev.ConsoleRenderer(),
        ],
        # 将structlog与标准库日志集成
        logger_factory=structlog.stdlib.LoggerFactory(),
        # 缓存logger实例
        cache_logger_on_first_use=True,
        # 包装标准库的logger
        wrapper_class=structlog.stdlib.BoundLogger,
        # 确保传递日志级别
        context_class=dict,
    )
    
    # 设置第三方库的日志级别
    if log_level > logging.INFO:
        # 提高一些啰嗦的库的日志级别
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)
