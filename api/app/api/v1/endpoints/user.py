import logging
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()

class UserResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    user_id: str

@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="获取用户信息",
    description="获取当前用户的基本信息",
    operation_id="get_user_info"
)
async def read_user(user_id: str):
    """获取用户信息"""
    logger.info("User info requested")
    
    return UserResponse(
        status="ok",
        user_id=user_id,
    )
