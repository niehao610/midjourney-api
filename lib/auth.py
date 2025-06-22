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
        # 记录请求基本信息
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        logger.info(f"🔐 认证请求 - IP: {client_ip}, Method: {method}, URL: {url}")
        
        # 检查Authorization头
        auth_header = request.headers.get("Authorization")
        if auth_header:
            logger.info(f"🔑 收到Authorization头: {auth_header[:20]}..." if len(auth_header) > 20 else f"🔑 收到Authorization头: {auth_header}")
        else:
            logger.warning(f"❌ 缺少Authorization头 - IP: {client_ip}, URL: {url}")
        
        credentials: HTTPAuthorizationCredentials = await super(AuthBearer, self).__call__(request)
        if credentials:
            app_key = credentials.credentials
            logger.info(f"📝 提取到App Key: {app_key} (长度: {len(app_key)})")
            
            if not credentials.scheme == "Bearer":
                logger.warning(f"❌ 无效的认证方案: {credentials.scheme} - App Key: {app_key}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme."
                )
            
            if not await self.verify_token(credentials.credentials):
                logger.warning(f"❌ Token验证失败 - App Key: {app_key}, IP: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token."
                )
            
            logger.info(f"✅ 认证成功 - App Key: {app_key}, IP: {client_ip}")
            return credentials
        else:
            logger.warning(f"❌ 无效的授权代码 - IP: {client_ip}, URL: {url}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )

    async def verify_token(self, token: str) -> bool:
        """验证token（app_key）是否有效"""
        try:
            logger.info(f"🔍 开始验证App Key: {token}")
            user = await user_ops.get_user_by_app_key(token)
            
            if user is not None:
                logger.info(f"✅ App Key验证成功 - 用户: {user.get('user_name')}, ID: {user.get('id')}, Token余额: {user.get('token_total', 0) - user.get('token_use', 0)}")
                return True
            else:
                logger.warning(f"❌ App Key不存在于数据库 - App Key: {token}")
                return False
        except Exception as e:
            logger.error(f"❌ Token验证异常 - App Key: {token}, 错误: {e}")
            return False


# 创建认证实例
auth_bearer = AuthBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(auth_bearer)) -> Dict:
    """获取当前用户信息"""
    try:
        app_key = credentials.credentials
        logger.info(f"👤 获取用户信息 - App Key: {app_key}")
        
        user = await user_ops.get_user_by_app_key(app_key)
        if not user:
            logger.warning(f"❌ 用户不存在 - App Key: {app_key}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found."
            )
        
        logger.info(f"✅ 用户信息获取成功 - 用户: {user.get('user_name')}, Token: {user.get('token_use')}/{user.get('token_total')}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取用户信息异常 - App Key: {app_key}, 错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information."
        )


async def check_user_token_limit(credentials: HTTPAuthorizationCredentials = Depends(auth_bearer)) -> bool:
    """检查用户token使用限制"""
    try:
        app_key = credentials.credentials
        logger.info(f"🔋 检查Token限制 - App Key: {app_key}")
        
        has_tokens = await user_ops.check_token_limit(app_key)
        if not has_tokens:
            # 获取详细的token信息用于日志
            user = await user_ops.get_user_by_app_key(app_key)
            if user:
                logger.warning(f"❌ Token余额不足 - 用户: {user.get('user_name')}, 已用/总计: {user.get('token_use', 0)}/{user.get('token_total', 0)}")
            else:
                logger.warning(f"❌ Token余额不足 - App Key: {app_key} (用户信息获取失败)")
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Token limit exceeded. Please contact administrator."
            )
        
        logger.info(f"✅ Token检查通过 - App Key: {app_key}")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 检查token限制异常 - App Key: {app_key}, 错误: {e}")
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
        logger.info(f"💰 开始消费Token - App Key: {app_key}")
        
        # 获取消费前的用户信息
        user_before = await user_ops.get_user_by_app_key(app_key)
        if user_before:
            logger.info(f"📊 消费前Token状态 - 用户: {user_before.get('user_name')}, 已用/总计: {user_before.get('token_use', 0)}/{user_before.get('token_total', 0)}")
        
        success = await user_ops.update_token_usage(app_key, 1)
        
        if success:
            # 获取消费后的用户信息
            user_after = await user_ops.get_user_by_app_key(app_key)
            if user_after:
                logger.info(f"✅ Token消费成功 - 用户: {user_after.get('user_name')}, 已用/总计: {user_after.get('token_use', 0)}/{user_after.get('token_total', 0)}")
            else:
                logger.info(f"✅ Token消费成功 - App Key: {app_key}")
        else:
            logger.warning(f"❌ Token消费失败 - App Key: {app_key}")
        
        return success
    except Exception as e:
        logger.error(f"❌ 消费token异常 - App Key: {app_key}, 错误: {e}")
        return False 