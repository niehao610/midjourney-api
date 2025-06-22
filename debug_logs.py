#!/usr/bin/env python3
"""
调试日志查看脚本
用于实时查看和分析认证相关的日志
"""

import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta


def tail_log_file(log_file: str, lines: int = 50):
    """显示日志文件的最后N行"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            if len(all_lines) <= lines:
                print(''.join(all_lines))
            else:
                print(''.join(all_lines[-lines:]))
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {log_file}")
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")


def follow_log_file(log_file: str):
    """实时跟踪日志文件"""
    try:
        print(f"🔍 实时跟踪日志文件: {log_file}")
        print("按 Ctrl+C 停止...")
        print("-" * 60)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            # 移动到文件末尾
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    time.sleep(0.1)
                    
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {log_file}")
    except KeyboardInterrupt:
        print("\n🛑 停止跟踪日志")
    except Exception as e:
        print(f"❌ 跟踪日志失败: {e}")


def filter_auth_logs(log_file: str, hours: int = 1):
    """过滤认证相关的日志"""
    try:
        auth_keywords = ['🔐', '🔑', '📝', '✅', '❌', '🔋', '💰', '👤', '🎨']
        
        print(f"🔍 过滤最近 {hours} 小时的认证日志:")
        print("-" * 60)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 简单的关键词过滤
                if any(keyword in line for keyword in auth_keywords):
                    print(line.rstrip())
                    
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {log_file}")
    except Exception as e:
        print(f"❌ 过滤日志失败: {e}")


def search_app_key_logs(log_file: str, app_key: str):
    """搜索特定App Key的相关日志"""
    try:
        print(f"🔍 搜索App Key '{app_key}' 相关日志:")
        print("-" * 60)
        
        found_count = 0
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if app_key in line:
                    found_count += 1
                    print(f"[{line_num}] {line.rstrip()}")
        
        if found_count == 0:
            print(f"❌ 未找到App Key '{app_key}' 相关日志")
        else:
            print(f"\n✅ 共找到 {found_count} 条相关日志")
            
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {log_file}")
    except Exception as e:
        print(f"❌ 搜索日志失败: {e}")


def show_error_logs(log_file: str):
    """显示错误日志"""
    try:
        print("🔍 显示错误和警告日志:")
        print("-" * 60)
        
        error_count = 0
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if 'ERROR' in line or 'WARNING' in line or '❌' in line:
                    error_count += 1
                    print(f"[{line_num}] {line.rstrip()}")
        
        if error_count == 0:
            print("✅ 没有发现错误或警告日志")
        else:
            print(f"\n⚠️ 共发现 {error_count} 条错误/警告日志")
            
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {log_file}")
    except Exception as e:
        print(f"❌ 查看错误日志失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="调试日志查看工具")
    parser.add_argument("--log-file", "-f", default="log/midjourney_api.log", help="日志文件路径")
    parser.add_argument("--tail", "-t", type=int, default=50, help="显示最后N行日志")
    parser.add_argument("--follow", action="store_true", help="实时跟踪日志")
    parser.add_argument("--auth", action="store_true", help="只显示认证相关日志")
    parser.add_argument("--errors", action="store_true", help="只显示错误和警告日志")
    parser.add_argument("--search", "-s", help="搜索特定App Key的日志")
    parser.add_argument("--hours", type=int, default=1, help="过滤最近N小时的日志")
    
    args = parser.parse_args()
    
    log_file = args.log_file
    
    # 检查日志文件是否存在
    if not os.path.exists(log_file):
        print(f"❌ 日志文件不存在: {log_file}")
        print("请确保API服务已启动并生成了日志文件")
        return
    
    print(f"📋 日志文件: {log_file}")
    print(f"📏 文件大小: {os.path.getsize(log_file)} 字节")
    print(f"🕒 修改时间: {datetime.fromtimestamp(os.path.getmtime(log_file))}")
    print()
    
    if args.follow:
        follow_log_file(log_file)
    elif args.auth:
        filter_auth_logs(log_file, args.hours)
    elif args.errors:
        show_error_logs(log_file)
    elif args.search:
        search_app_key_logs(log_file, args.search)
    else:
        print(f"📋 显示最后 {args.tail} 行日志:")
        print("-" * 60)
        tail_log_file(log_file, args.tail)


if __name__ == "__main__":
    main() 