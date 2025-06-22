#!/usr/bin/env python3
"""
用户管理脚本
用于创建、查询、更新用户信息
"""

import asyncio
import sys
import secrets
import string
from datetime import datetime

# 导入项目模块
from lib.database import connect_db, disconnect_db, create_tables
from lib.db_operations import user_ops


def generate_app_key(length=32):
    """生成随机的app_key"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


async def create_user(username: str, token_total: int = 100):
    """创建新用户"""
    try:
        # 检查用户是否已存在
        existing_user = await user_ops.get_user_by_username(username)
        if existing_user:
            print(f"❌ 用户 '{username}' 已存在！")
            return False
        
        # 生成app_key
        app_key = generate_app_key()
        
        # 创建用户
        user_id = await user_ops.create_user(username, app_key, token_total)
        if user_id:
            print(f"✅ 用户创建成功！")
            print(f"   用户名: {username}")
            print(f"   App Key: {app_key}")
            print(f"   总Token数: {token_total}")
            print(f"   数据库ID: {user_id}")
            return True
        else:
            print(f"❌ 用户创建失败！")
            return False
    except Exception as e:
        print(f"❌ 创建用户时发生错误: {e}")
        return False


async def get_user_info(identifier: str, by_username: bool = True):
    """查询用户信息"""
    try:
        if by_username:
            user = await user_ops.get_user_by_username(identifier)
            query_type = "用户名"
        else:
            user = await user_ops.get_user_by_app_key(identifier)
            query_type = "App Key"
        
        if user:
            print(f"✅ 找到用户信息:")
            print(f"   ID: {user['id']}")
            print(f"   用户名: {user['user_name']}")
            print(f"   App Key: {user['app_key']}")
            print(f"   总Token数: {user['token_total']}")
            print(f"   已使用Token: {user['token_use']}")
            print(f"   剩余Token: {user['token_total'] - user['token_use']}")
            print(f"   创建时间: {user['created_at']}")
            print(f"   更新时间: {user['updated_at']}")
            return user
        else:
            print(f"❌ 未找到{query_type} '{identifier}' 对应的用户")
            return None
    except Exception as e:
        print(f"❌ 查询用户信息时发生错误: {e}")
        return None


async def update_user_tokens(app_key: str, new_total: int):
    """更新用户token总数"""
    try:
        # 先查询用户信息
        user = await user_ops.get_user_by_app_key(app_key)
        if not user:
            print(f"❌ App Key '{app_key}' 对应的用户不存在")
            return False
        
        # 更新token总数（这里需要扩展db_operations）
        # 暂时通过直接数据库操作实现
        from lib.database import database, user_info
        query = user_info.update().where(
            user_info.c.app_key == app_key
        ).values(
            token_total=new_total,
            updated_at=datetime.now()
        )
        result = await database.execute(query)
        
        if result > 0:
            print(f"✅ Token总数更新成功！")
            print(f"   用户: {user['user_name']}")
            print(f"   新的Token总数: {new_total}")
            return True
        else:
            print(f"❌ Token总数更新失败")
            return False
    except Exception as e:
        print(f"❌ 更新Token总数时发生错误: {e}")
        return False


async def reset_user_usage(app_key: str):
    """重置用户token使用量"""
    try:
        from lib.database import database, user_info
        query = user_info.update().where(
            user_info.c.app_key == app_key
        ).values(
            token_use=0,
            updated_at=datetime.now()
        )
        result = await database.execute(query)
        
        if result > 0:
            print(f"✅ 用户token使用量重置成功！")
            return True
        else:
            print(f"❌ 用户token使用量重置失败")
            return False
    except Exception as e:
        print(f"❌ 重置token使用量时发生错误: {e}")
        return False


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python manage_users.py create <username> [token_total]  # 创建用户")
        print("  python manage_users.py info <username>                  # 查询用户信息（按用户名）")
        print("  python manage_users.py info-key <app_key>               # 查询用户信息（按App Key）")
        print("  python manage_users.py update-tokens <app_key> <total>  # 更新Token总数")
        print("  python manage_users.py reset-usage <app_key>            # 重置使用量")
        sys.exit(1)
    
    # 连接数据库
    create_tables()
    await connect_db()
    
    try:
        command = sys.argv[1]
        
        if command == "create":
            if len(sys.argv) < 3:
                print("❌ 请提供用户名")
                return
            username = sys.argv[2]
            token_total = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            await create_user(username, token_total)
        
        elif command == "info":
            if len(sys.argv) < 3:
                print("❌ 请提供用户名")
                return
            username = sys.argv[2]
            await get_user_info(username, by_username=True)
        
        elif command == "info-key":
            if len(sys.argv) < 3:
                print("❌ 请提供App Key")
                return
            app_key = sys.argv[2]
            await get_user_info(app_key, by_username=False)
        
        elif command == "update-tokens":
            if len(sys.argv) < 4:
                print("❌ 请提供App Key和新的Token总数")
                return
            app_key = sys.argv[2]
            new_total = int(sys.argv[3])
            await update_user_tokens(app_key, new_total)
        
        elif command == "reset-usage":
            if len(sys.argv) < 3:
                print("❌ 请提供App Key")
                return
            app_key = sys.argv[2]
            await reset_user_usage(app_key)
        
        else:
            print(f"❌ 未知命令: {command}")
    
    except Exception as e:
        print(f"❌ 执行命令时发生错误: {e}")
    
    finally:
        # 断开数据库连接
        await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main()) 