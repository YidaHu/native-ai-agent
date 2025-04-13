from fastapi import APIRouter

from app.api.v1.endpoints import agents, config, health, llm, user

# 创建APIRouter实例
api_router = APIRouter()

# 包含各个端点模块的路由
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(config.router, prefix="/config", tags=["Config"])
api_router.include_router(
    agents.router, prefix='/agents', tags=['Agents']
)  # 包含智能体API：运费险助手和火车票取消订单助手
api_router.include_router(llm.router, prefix='/llm', tags=['LLM'])  # 包含大模型问答API

# 这里可以继续添加其他API端点的路由
# 例如：api_router.include_router(users.router, prefix="/users", tags=["Users"])

# 这里可以继续添加其他API端点的路由
# 例如：api_router.include_router(users.router, prefix="/users", tags=["Users"])

# 这里可以继续添加其他API端点的路由
# 例如：api_router.include_router(users.router, prefix="/users", tags=["Users"])

# 这里可以继续添加其他API端点的路由
# 例如：api_router.include_router(users.router, prefix="/users", tags=["Users"])
