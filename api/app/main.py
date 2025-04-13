import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from fastapi.middleware.cors import CORSMiddleware

# 首先导入配置
from app.core.config import settings

# 然后配置日志
from app.core.logging import configure_logging

# 配置日志后再导入使用logger的模块
configure_logging()

# 然后导入依赖于日志配置的其他模块
from app.api.v1.router import api_router
from app.db.redis_client import redis_client

# 获取logger实例
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    处理应用程序的启动和关闭事件
    这替代了弃用的 on_event 方法
    """
    # 启动事件
    try:
        logger.info('Application starting up...')

        # 初始化存储
        try:
            await redis_client.initialize()
        except Exception as e:
            logger.error(f'Storage initialization failed: {e}')

        yield  # 应用程序运行时

        # 关闭事件
        logger.info('Application shutting down...')

        # 关闭存储连接
        try:
            await redis_client.close()
        except Exception as e:
            logger.error(f'Storage shutdown failed: {e}')
    except Exception as e:
        logger.exception(f'Unexpected error in lifespan: {e}')
        # 即使出现异常也要确保生成器继续
        yield


# 使用 lifespan 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url=f'{settings.API_PREFIX}/docs',
    openapi_url=f'{settings.API_PREFIX}/openapi.json',
    lifespan=lifespan,  # 使用 lifespan 上下文管理器
)

mcp = FastApiMCP(
    app,
    # Optional parameters
    name='Native AI API MCP',
    description='My API description',
    base_url='http://localhost:8000',
)
mcp.mount()
# 设置跨域
# 从配置中获取CORS配置
cors_origins = settings.CORS_ORIGINS
logger.info(f'Configuring CORS with origins: {cors_origins}')

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# 包含API路由
app.include_router(api_router, prefix=settings.API_PREFIX)
mcp.setup_server()
if __name__ == '__main__':
    uvicorn.run(
        'app.main:app',
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level='debug' if settings.DEBUG else 'info',
    )

