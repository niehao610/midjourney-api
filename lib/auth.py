from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
from loguru import logger

from .db_operations import user_ops


class AuthBearer(HTTPBearer):
    """自定义Bearer认证类"""
    
    def __init__(self, auto_error: bool = True):
        super(AuthBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: HTTPAuthorizationCredentials = await super(AuthBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme."
                )
            if not await self.verify_token(credentials.credentials):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token."
                )
            return credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )

    async def verify_token(self, token: str) -> bool:
        """验证token（app_key）是否有效"""
        try:
            user = await user_ops.get_user_by_app_key(token)
            return user is not None
        except Exception as e:
            logger.error(f"Token验证失败: {e}")
            return False


# 创建认证实例
auth_bearer = AuthBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(auth_bearer)) -> Dict:
    """获取当前用户信息"""
    try:
        app_key = credentials.credentials
        user = await user_ops.get_user_by_app_key(app_key)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found."
            )
        return user
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information."
        )


async def check_user_token_limit(credentials: HTTPAuthorizationCredentials = Depends(auth_bearer)) -> bool:
    """检查用户token使用限制"""
    try:
        app_key = credentials.credentials
        has_tokens = await user_ops.check_token_limit(app_key)
        if not has_tokens:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Token limit exceeded. Please contact administrator."
            )
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查token限制失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check token limit."
        )


async def consume_user_token(credentials: HTTPAuthorizationCredentials = Depends(auth_bearer)) -> bool:
    """消费用户token"""
    try:
        app_key = credentials.credentials
        success = await user_ops.update_token_usage(app_key, 1)
        if not success:
            logger.warning(f"Failed to update token usage for app_key: {app_key}")
        return success
    except Exception as e:
        logger.error(f"消费token失败: {e}")
        return False


async def consume_user_token_by_app_key(app_key: str) -> bool:
    """根据app_key直接消费用户token"""
    try:
        success = await user_ops.update_token_usage(app_key, 1)
        if not success:
            logger.warning(f"Failed to update token usage for app_key: {app_key}")
        return success
    except Exception as e:
        logger.error(f"消费token失败: {e}")
        return False 