import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# 这里假设在settings中添加了以下配置
# JWT_SECRET_KEY: str = "your-secret-key"
# JWT_ALGORITHM: str = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建 JWT 访问令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        getattr(settings, "JWT_SECRET_KEY", "fallback-secret-key"),
        algorithm=getattr(settings, "JWT_ALGORITHM", "HS256")
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    获取密码哈希值
    """
    return pwd_context.hash(password)

def generate_random_secret(length: int = 32) -> str:
    """
    生成随机密钥
    """
    return secrets.token_urlsafe(length)
