#!/usr/bin/env python3
"""
检查队列阻塞问题
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from util._queue import taskqueue
from loguru import logger


def check_detailed_status():
    """检查详细的队列状态"""
    print("=== 详细队列状态 ===")
    print(f"并发队列容量: {taskqueue._concur_size}")
    print(f"等待队列容量: {taskqueue._wait_size}")
    print(f"当前并发队列 ({len(taskqueue._concur_queue)}/{taskqueue._concur_size}): {taskqueue._concur_queue}")
    print(f"当前等待队列 ({len(taskqueue._wait_queue)}): {[list(item.keys())[0] for item in taskqueue._wait_queue]}")
    print()
    
    # 检查环境变量
    print("=== 环境变量 ===")
    print(f"CONCUR_SIZE: {os.getenv('CONCUR_SIZE', '未设置')}")
    print(f"WAIT_SIZE: {os.getenv('WAIT_SIZE', '未设置')}")
    print()
    
    # 分析问题
    if len(taskqueue._concur_queue) >= taskqueue._concur_size:
        print("⚠️  **问题发现**: 并发队列已满！")
        print("可能原因:")
        print("1. 之前的任务没有正确释放队列位置")
        print("2. CONCUR_SIZE设置太小")
        print("3. 任务执行时间太长或被阻塞")
        print()


def clear_stuck_queue():
    """清理卡住的队列"""
    print("=== 清理队列 ===")
    print("清理前:")
    check_detailed_status()
    
    # 清理并发队列
    taskqueue.clear_concur()
    print("✅ 已清理并发队列")
    
    print("清理后:")
    check_detailed_status()


if __name__ == "__main__":
    print("🔍 检查队列阻塞问题")
    check_detailed_status()
    
    # 询问是否清理队列
    if len(taskqueue._concur_queue) > 0:
        response = input("是否清理卡住的队列? (y/n): ")
        if response.lower() == 'y':
            clear_stuck_queue() 