import logging
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    version: str
    timestamp: str
    redis_connected: bool

@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="系统健康检查",
    description="检查API系统状态和关键依赖服务的连接状态",
)
async def health_check():
    """
    系统健康检查端点:
    - 检查API本身是否正常运行
    - 检查Redis连接状态
    """
    logger.info("Health check requested")
    
    # 检查Redis连接
    redis_status = False
    try:
        await redis_client.set("health_check", "ok", expire=10)
        redis_value = await redis_client.get("health_check")
        redis_status = redis_value == "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    return HealthResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.now().isoformat(),
        redis_connected=redis_status,
    )
