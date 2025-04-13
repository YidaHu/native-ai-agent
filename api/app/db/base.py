import logging
from typing import Generator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# 这里假设环境变量或配置中有DATABASE_URI
SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///./nativeai.db"

# 创建异步引擎
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# 创建异步会话
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)

# 声明基类
Base = declarative_base()

async def get_db() -> Generator:
    """获取数据库会话的依赖函数"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception(f"Database session error: {e}")
        raise
    finally:
        await session.close()
