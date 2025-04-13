import logging
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel


logger = logging.getLogger(__name__)

router = APIRouter()

class ConfigResponse(BaseModel):
    """配置响应模型"""
    key: str
    value: Any
    source: str = "config_center"

class ConfigsResponse(BaseModel):
    """所有配置响应模型"""
    configs: Dict[str, Any]
    version: str
    source: str = "config_center"
