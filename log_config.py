#!/usr/bin/env python3
"""
日志配置模块
统一管理日志格式和级别
"""

import sys
from loguru import logger
from pathlib import Path


def setup_logger(log_level: str = "INFO", log_file: str = None):
    """
    配置日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径 (可选)
    """
    
    # 移除默认的日志处理器
    logger.remove()
    
    # 定义日志格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 如果指定了日志文件，添加文件输出
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=log_format,
            level=log_level,
            rotation="100 MB",  # 文件大小达到100MB时轮转
            retention="30 days",  # 保留30天的日志
            compression="zip",  # 压缩旧日志文件
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )
        
        logger.info(f"📝 日志文件已配置: {log_file}")
    
    logger.info(f"🚀 日志系统初始化完成 - 级别: {log_level}")


def setup_api_logger():
    """为API服务配置日志"""
    import os
    
    # 从环境变量获取配置，或使用默认值
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "log/midjourney_api.log")
    
    setup_logger(log_level, log_file)


def setup_debug_logger():
    """为调试配置详细日志"""
    setup_logger("DEBUG", "log/debug.log")


# 认证相关的专用日志函数
def log_auth_request(client_ip: str, method: str, url: str):
    """记录认证请求"""
    logger.info(f"🔐 认证请求 - IP: {client_ip}, Method: {method}, URL: {url}")


def log_auth_success(app_key: str, user_name: str, client_ip: str):
    """记录认证成功"""
    logger.info(f"✅ 认证成功 - 用户: {user_name}, App Key: {app_key[:8]}***, IP: {client_ip}")


def log_auth_failure(app_key: str, reason: str, client_ip: str):
    """记录认证失败"""
    logger.warning(f"❌ 认证失败 - App Key: {app_key[:8]}***, 原因: {reason}, IP: {client_ip}")


def log_token_consumption(user_name: str, app_key: str, before: int, after: int, total: int):
    """记录Token消费"""
    logger.info(f"💰 Token消费 - 用户: {user_name}, App Key: {app_key[:8]}***, {before}→{after}/{total}")


def log_api_request(endpoint: str, user_name: str, params: dict = None):
    """记录API请求"""
    params_str = f", 参数: {params}" if params else ""
    logger.info(f"📡 API请求 - 端点: {endpoint}, 用户: {user_name}{params_str}")


if __name__ == "__main__":
    # 测试日志配置
    setup_debug_logger()
    
    logger.debug("这是一条调试信息")
    logger.info("这是一条信息")
    logger.warning("这是一条警告")
    logger.error("这是一条错误")
    
    # 测试认证日志
    log_auth_request("192.168.1.100", "POST", "/v1/api/trigger/imagine")
    log_auth_success("abc123def456", "testuser", "192.168.1.100")
    log_auth_failure("invalid_key", "用户不存在", "192.168.1.100")
    log_token_consumption("testuser", "abc123def456", 5, 6, 100)
    log_api_request("/imagine", "testuser", {"prompt": "test"}) 