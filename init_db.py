#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import asyncio
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from lib.database import create_tables, connect_db, disconnect_db
from loguru import logger


async def init_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 创建数据库表
        create_tables()
        logger.info("数据库表创建成功")
        
        # 测试数据库连接
        await connect_db()
        logger.info("数据库连接测试成功")
        
        await disconnect_db()
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_database()) 