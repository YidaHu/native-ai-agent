import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base, get_db
from app.main import app

# 测试数据库URL - 使用内存数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试用的异步引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

# 创建测试会话
TestAsyncSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest.fixture(scope="session")
def event_loop():
    """创建一个会话范围的事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_database():
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # 清理 - 删除所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session) -> Generator[TestClient, None, None]:
    """
    创建测试客户端
    """
    # 创建依赖覆盖
    async def override_get_db():
        yield db_session
    
    # 应用依赖覆盖
    app.dependency_overrides[get_db] = override_get_db
    
    # 使用 with 语句确保关闭客户端连接
    with TestClient(app) as client:
        yield client
    
    # 清理
    app.dependency_overrides = {}
