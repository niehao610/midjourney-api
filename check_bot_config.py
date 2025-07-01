#!/usr/bin/env python3
"""
简单的Bot配置检查工具
检查基本的配置问题
"""

import os
from dotenv import load_dotenv
from loguru import logger

def check_config():
    """检查Bot配置"""
    logger.info("🔧 Bot配置检查工具")
    logger.info("=" * 40)
    
    # 加载环境变量
    load_dotenv()
    
    # 1. 检查BOT_TOKEN
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("❌ 未找到BOT_TOKEN环境变量!")
        logger.info("请确保在.env文件中设置: BOT_TOKEN=your_bot_token_here")
        return False
    else:
        logger.success("✅ BOT_TOKEN已配置")
        logger.info(f"Token长度: {len(bot_token)} 字符")
        if len(bot_token) < 50:
            logger.warning("⚠️ Token长度似乎不正确，正确的Discord Bot Token通常有70+字符")
    
    # 2. 检查其他环境变量
    env_vars = {
        "CONCUR_SIZE": "并发队列大小",
        "WAIT_SIZE": "等待队列大小",
        "PROXY_URL": "代理URL"
    }
    
    for var, desc in env_vars.items():
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {desc} ({var}): {value}")
        else:
            logger.warning(f"⚠️ {desc} ({var}): 未设置")
    
    # 3. 检查必要的包
    try:
        import discord
        logger.success(f"✅ discord.py 版本: {discord.__version__}")
    except ImportError:
        logger.error("❌ discord.py 未安装!")
        logger.info("请运行: pip install discord.py")
        return False
    
    try:
        import loguru
        logger.success("✅ loguru 已安装")
    except ImportError:
        logger.error("❌ loguru 未安装!")
        return False
    
    # 4. 检查权限和Intents要求
    logger.info("📋 Discord Bot 权限检查清单:")
    logger.info("请确保以下设置正确:")
    logger.info("  1. 在Discord开发者面板中启用 'Message Content Intent'")
    logger.info("  2. Bot已被邀请到包含Midjourney Bot的服务器")
    logger.info("  3. Bot在目标频道有以下权限:")
    logger.info("     - 读取消息")
    logger.info("     - 读取消息历史")
    logger.info("     - 发送消息")
    logger.info("  4. 确认Midjourney Bot的用户ID是否为: 936929561302675456")
    
    logger.info("")
    logger.info("🔍 故障排除步骤:")
    logger.info("1. 运行诊断工具: python debug_bot_connection.py")
    logger.info("2. 检查Bot日志中的连接信息")
    logger.info("3. 确认Midjourney Bot的实际用户ID")
    logger.info("4. 检查网络连接和代理设置")
    
    return True

if __name__ == "__main__":
    check_config() 