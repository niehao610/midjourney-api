#!/usr/bin/env python3
"""
队列调试脚本 - 检查任务队列状态和执行情况
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from util._queue import taskqueue
from loguru import logger


def check_queue_status():
    """检查队列状态"""
    print("=== 队列状态检查 ===")
    print(f"并发大小: {taskqueue.concur_size()}")
    print(f"等待队列大小: {taskqueue.wait_size()}")
    print(f"当前并发队列: {taskqueue._concur_queue}")
    print(f"当前等待队列长度: {len(taskqueue._wait_queue)}")
    print(f"等待队列内容: {list(taskqueue._wait_queue)}")
    print()


def check_environment():
    """检查环境变量"""
    print("=== 环境变量检查 ===")
    print(f"CONCUR_SIZE: {os.getenv('CONCUR_SIZE', '未设置 (默认9999)')}")
    print(f"WAIT_SIZE: {os.getenv('WAIT_SIZE', '未设置 (默认9999)')}")
    print()


async def test_simple_task():
    """测试简单任务"""
    print("=== 测试简单任务 ===")
    
    async def simple_task(msg):
        logger.info(f"🔥 执行测试任务: {msg}")
        await asyncio.sleep(1)
        logger.info(f"✅ 测试任务完成: {msg}")
    
    # 添加测试任务
    test_trigger_id = "test_123"
    logger.info(f"添加测试任务: {test_trigger_id}")
    taskqueue.put(test_trigger_id, simple_task, "测试消息")
    
    # 检查队列状态
    check_queue_status()
    
    # 等待任务执行
    await asyncio.sleep(3)
    
    # 再次检查状态
    check_queue_status()


async def main():
    """主函数"""
    print("🚀 开始队列调试")
    
    # 检查环境
    check_environment()
    
    # 检查初始状态
    check_queue_status()
    
    # 测试简单任务
    await test_simple_task()
    
    print("✅ 队列调试完成")


if __name__ == "__main__":
    asyncio.run(main()) 