"""
会话管理服务
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

class SessionEncoder(json.JSONEncoder):
    """用于序列化会话数据的JSON编码器"""
    def default(self, obj):
        # 处理常见的LangChain消息类型
        if hasattr(obj, "content") and hasattr(obj, "type"):
            # 处理LangChain消息对象(如HumanMessage, AIMessage等)
            return {
                "content": obj.content,
                "type": obj.type,
                "_type": obj.__class__.__name__
            }
        # 其他类型的处理
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)

class SessionService:
    """会话管理服务"""
    
    def __init__(self):
        """初始化会话服务"""
        self.session_prefix = "nativeai:session:"
        self.session_ttl = int(settings.get_config("SESSION_TTL_SECONDS", 3600 * 24))  # 默认24小时
    
    async def create_session(self, user_id: str = None) -> str:
        """
        创建新的会话
        
        Args:
            user_id: 可选的用户ID
            
        Returns:
            新创建的会话ID
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "user_id": user_id,
            "messages": [],
            "state": {"messages": [], "tool": "", "tool_args": {}, "last_tool": None}
        }
        
        # 存储会话数据
        key = f"{self.session_prefix}{session_id}"
        await redis_client.set(key, json.dumps(session_data, ensure_ascii=False), expire=self.session_ttl)
        logger.info(f"Created new session: {session_id}")
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据字典，不存在则返回None
        """
        key = f"{self.session_prefix}{session_id}"
        data = await redis_client.get(key)
        
        if not data:
            logger.warning(f"Session not found: {session_id}")
            return None
        
        try:
            session_data = json.loads(data)
            # 刷新会话有效期
            await redis_client.set(key, data, expire=self.session_ttl)
            
            # 适应性处理可能的序列化对象
            # 这里我们不需要将字典转回LangChain对象，因为客户端代码只需要访问内容
            # 但我们需要确保session_data的格式与客户端期望的一致
            if "state" in session_data and "messages" in session_data["state"]:
                # 检查messages列表中的对象是否为序列化后的LangChain消息
                for i, msg in enumerate(session_data["state"]["messages"]):
                    if isinstance(msg, dict) and "_type" in msg:
                        # 我们保留这些消息的字典形式，确保它们的结构符合代码需求
                        pass
            
            return session_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode session data: {e}")
            return None
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        更新会话数据
        
        Args:
            session_id: 会话ID
            data: 要更新的会话数据
            
        Returns:
            是否更新成功
        """
        key = f"{self.session_prefix}{session_id}"
        session_data = await self.get_session(session_id)
        
        if not session_data:
            return False
        
        # 更新会话数据
        data = self._convert_non_serializable(data)  # 确保数据可序列化
        session_data.update(data)
        session_data["updated_at"] = datetime.now().isoformat()
        
        # 存储更新后的会话数据
        try:
            # 使用自定义JSON编码器进行序列化
            json_data = json.dumps(session_data, cls=SessionEncoder, ensure_ascii=False)
            success = await redis_client.set(key, json_data, expire=self.session_ttl)
            return success
        except TypeError as e:
            logger.error(f"JSON序列化错误: {e}")
            # 尝试更强的序列化处理
            safe_data = self._convert_non_serializable(session_data)
            json_data = json.dumps(safe_data, ensure_ascii=False)
            success = await redis_client.set(key, json_data, expire=self.session_ttl)
            return success
    
    def _convert_non_serializable(self, data: Any) -> Any:
        """
        递归地将不可序列化的对象转换为可序列化的字典
        
        Args:
            data: 需要转换的数据
            
        Returns:
            转换后的可序列化数据
        """
        if hasattr(data, "content") and hasattr(data, "type"):
            # 处理LangChain消息对象
            return {
                "content": data.content,
                "type": data.type,
                "_type": data.__class__.__name__
            }
        elif isinstance(data, dict):
            return {k: self._convert_non_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_non_serializable(item) for item in data]
        return data
    
    async def add_message(self, session_id: str, message: Dict[str, Any], state: Dict[str, Any] = None) -> bool:
        """
        添加消息到会话历史
        
        Args:
            session_id: 会话ID
            message: 消息数据
            state: 可选的状态更新数据
            
        Returns:
            是否添加成功
        """
        session_data = await self.get_session(session_id)
        
        if not session_data:
            return False
        
        # 确保存在messages字段
        if "messages" not in session_data:
            session_data["messages"] = []
        
        # 添加消息
        message["timestamp"] = datetime.now().isoformat()
        session_data["messages"].append(message)
        
        # 更新状态
        if state:
            # 转换状态中不可序列化的对象
            state = self._convert_non_serializable(state)
            session_data["state"] = state
        
        # 存储更新后的会话数据
        key = f"{self.session_prefix}{session_id}"
        try:
            # 使用自定义JSON编码器进行序列化
            json_data = json.dumps(session_data, cls=SessionEncoder, ensure_ascii=False)
            success = await redis_client.set(key, json_data, expire=self.session_ttl)
            return success
        except TypeError as e:
            logger.error(f"JSON序列化错误: {e}")
            # 尝试更强的序列化处理
            safe_data = self._convert_non_serializable(session_data)
            json_data = json.dumps(safe_data, ensure_ascii=False)
            success = await redis_client.set(key, json_data, expire=self.session_ttl)
            return success
    
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        key = f"{self.session_prefix}{session_id}"
        success = await redis_client.delete(key)
        return success


# 创建全局会话服务实例
session_service = SessionService()
