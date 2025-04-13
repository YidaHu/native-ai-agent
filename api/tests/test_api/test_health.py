from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.db.redis_client import redis_client

# 同步测试
def test_health_check(client: TestClient):
    """测试健康检查端点"""
    with patch.object(redis_client, "set", return_value=AsyncMock(return_value=True)), \
         patch.object(redis_client, "get", return_value=AsyncMock(return_value="ok")):
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data
        assert data["redis_connected"] == True

# 异步测试
@pytest.mark.asyncio
async def test_health_check_async():
    """异步测试健康检查端点"""
    with patch.object(redis_client, "set", return_value=AsyncMock(return_value=True)), \
         patch.object(redis_client, "get", return_value=AsyncMock(return_value="ok")):
        async with AsyncClient(base_url="http://test") as ac:
            response = await ac.get("/api/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
