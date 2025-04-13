"""
智能体API测试
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.services.agents.shipping_fee_agent import shipping_fee_agent
from app.services.session_service import session_service


@pytest.fixture
def mock_session_service():
    """模拟会话服务"""
    with patch.object(
        session_service, 'create_session', return_value=AsyncMock(return_value='test-session-id')
    ), patch.object(
        session_service,
        'get_session',
        return_value=AsyncMock(
            return_value={
                'id': 'test-session-id',
                'created_at': '2023-01-01T00:00:00',
                'user_id': 'test-user',
                'messages': [],
                'state': {'messages': [], 'tool': '', 'tool_args': {}, 'last_tool': None},
            }
        ),
    ), patch.object(session_service, 'add_message', return_value=AsyncMock(return_value=True)), patch.object(
        session_service, 'update_session', return_value=AsyncMock(return_value=True)
    ), patch.object(session_service, 'delete_session', return_value=AsyncMock(return_value=True)):
        yield


@pytest.fixture
def mock_shipping_fee_agent():
    """模拟运费险助手"""
    with patch.object(
        shipping_fee_agent,
        'process_message',
        return_value={
            'reply': '这是助手的测试回复',
            'state': {'messages': [], 'tool': '', 'tool_args': {}, 'last_tool': None},
        },
    ):
        yield


def test_chat_with_shipping_fee_agent_new_session(client: TestClient, mock_session_service, mock_shipping_fee_agent):
    """测试创建新会话并发送消息"""
    response = client.post('/nativeai/agents/shipping-fee/chat', json={'content': '我想了解运费险'})

    assert response.status_code == 200
    data = response.json()
    assert 'reply' in data
    assert data['reply'] == '这是助手的测试回复'
    assert 'session_id' in data
    assert data['session_id'] == 'test-session-id'


def test_chat_with_shipping_fee_agent_existing_session(
    client: TestClient, mock_session_service, mock_shipping_fee_agent
):
    """测试使用现有会话发送消息"""
    response = client.post(
        '/nativeai/agents/shipping-fee/chat', json={'content': '我想了解运费险', 'session_id': 'test-session-id'}
    )

    assert response.status_code == 200
    data = response.json()
    assert 'reply' in data
    assert data['reply'] == '这是助手的测试回复'
    assert 'session_id' in data
    assert data['session_id'] == 'test-session-id'


def test_get_session_detail(client: TestClient, mock_session_service):
    """测试获取会话详情"""
    # 模拟session_service.get_session返回更丰富的数据
    with patch.object(
        session_service,
        'get_session',
        return_value=AsyncMock(
            return_value={
                'id': 'test-session-id',
                'created_at': '2023-01-01T00:00:00',
                'updated_at': '2023-01-01T01:00:00',
                'user_id': 'test-user',
                'messages': [
                    {'role': 'user', 'content': '你好', 'timestamp': '2023-01-01T00:30:00'},
                    {
                        'role': 'assistant',
                        'content': '您好，有什么可以帮助您的吗？',
                        'timestamp': '2023-01-01T00:30:05',
                    },
                ],
                'state': {'messages': [], 'tool': '', 'tool_args': {}, 'last_tool': None},
            }
        ),
    ):
        response = client.get('/nativeai/agents/sessions/test-session-id')

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 'test-session-id'
        assert len(data['messages']) == 2
        assert data['messages'][0]['role'] == 'user'
        assert data['messages'][0]['content'] == '你好'


def test_delete_session(client: TestClient, mock_session_service):
    """测试删除会话"""
    response = client.delete('/nativeai/agents/sessions/test-session-id')
    assert response.status_code == 204
