import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from loguru import logger

from .database import database, midjourney_task, user_info


class MidjourneyTaskOperations:
    """Midjourney任务数据库操作类"""

    @staticmethod
    async def create_task(
        task_name: str,
        task_id: str,
        trigger_id: str,
        task_type: str,
        ref_pic_url: Optional[str] = None,
        image_index: int = 0,
        msg_id: int = 0,
        prompt: str = "",
        msg_hash: str = "",
        zoom_out: int = 0,
        direction: str = "",
        task_status: str = "NOT_START"
    ) -> int:
        """创建新任务"""
        try:
            query = midjourney_task.insert().values(
                task_name=task_name,
                task_id=task_id,
                trigger_id=trigger_id,
                ref_pic_url=ref_pic_url,
                image_index=image_index,
                msg_id=msg_id,
                msg_hash=msg_hash,
                zoom_out=zoom_out,
                direction=direction,
                task_type=task_type,
                task_status=task_status,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            result = await database.execute(query)
            logger.info(f"创建任务成功，task_id: {task_id}, trigger_id: {trigger_id}, db_id: {result}")
            return result
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise

    @staticmethod
    async def get_task_by_task_id(task_id: str) -> Optional[Dict]:
        """根据task_id获取任务"""
        try:
            query = midjourney_task.select().where(midjourney_task.c.task_id == task_id)
            result = await database.fetch_one(query)
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"查询任务失败: {e}")
            return None

    @staticmethod
    async def get_task_by_trigger_id(trigger_id: str) -> Optional[Dict]:
        """根据trigger_id获取任务"""
        try:
            query = midjourney_task.select().where(midjourney_task.c.trigger_id == trigger_id).order_by(midjourney_task.c.id.desc())
            result = await database.fetch_one(query)
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"查询任务失败: {e}")
            return None


    @staticmethod
    async def get_task_by_trigger_id_status(trigger_id: str, task_status: str) -> Optional[Dict]:
        """根据trigger_id和任务状态获取任务"""
        try:
            query = midjourney_task.select().where(midjourney_task.c.trigger_id == trigger_id).where(midjourney_task.c.task_status == task_status)
            result = await database.fetch_one(query)
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"查询任务失败: {e}")
            return None
        
    @staticmethod
    async def get_task_by_msg_id(msg_id: int) -> Optional[Dict]:
        """根据msg_id获取任务"""
        try:
            query = midjourney_task.select().where(midjourney_task.c.msg_id == msg_id)
            result = await database.fetch_one(query)
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"查询任务失败: {e}")
            return None

    @staticmethod
    async def update_task_status_by_task_id(task_id: str, task_status: str) -> bool:
        """根据task_id更新任务状态"""
        try:
            query = midjourney_task.update().where(
                midjourney_task.c.task_id == task_id
            ).values(
                task_status=task_status,
                updated_at=datetime.now()
            )
            result = await database.execute(query)
            logger.info(f"更新任务状态成功，task_id: {task_id}, status: {task_status}")
            return result > 0
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False

    @staticmethod
    async def update_task_status(trigger_id: str, task_status: str) -> bool:
        """根据trigger_id更新任务状态"""
        try:
            query = midjourney_task.update().where(
                midjourney_task.c.trigger_id == trigger_id
            ).values(
                task_status=task_status,
                updated_at=datetime.now()
            )
            result = await database.execute(query)
            logger.info(f"更新任务状态成功，trigger_id: {trigger_id}, status: {task_status}")
            return result > 0
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False

    @staticmethod
    async def update_task_result(
        task_id: str,
        task_status: str,
        result_url: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
        msg_id: Optional[int] = None,
        msg_hash: Optional[str] = None
    ) -> bool:
        """更新任务结果"""
        try:
            update_data = {
                "task_status": task_status,
                "updated_at": datetime.now()
            }
            
            if result_url:
                update_data["result_url"] = result_url
            
            if attachments:
                update_data["attachments"] = json.dumps(attachments, ensure_ascii=False)
            
            if msg_id:
                update_data["msg_id"] = msg_id
                
            if msg_hash:
                update_data["msg_hash"] = msg_hash

            query = midjourney_task.update().where(
                midjourney_task.c.task_id == task_id
            ).values(**update_data)
            
            result = await database.execute(query)
            logger.info(f"更新任务结果成功，trigger_id: {task_id}")
            return result > 0
        except Exception as e:
            logger.error(f"更新任务结果失败: {e}")
            return False

    @staticmethod
    async def get_tasks_by_status(task_status: str, limit: int = 100) -> List[Dict]:
        """根据状态获取任务列表"""
        try:
            query = midjourney_task.select().where(
                midjourney_task.c.task_status == task_status
            ).limit(limit).order_by(midjourney_task.c.created_at.desc())
            
            results = await database.fetch_all(query)
            return [dict(result) for result in results]
        except Exception as e:
            logger.error(f"查询任务列表失败: {e}")
            return []

    @staticmethod
    async def delete_task(trigger_id: str) -> bool:
        """删除任务"""
        try:
            query = midjourney_task.delete().where(midjourney_task.c.trigger_id == trigger_id)
            result = await database.execute(query)
            logger.info(f"删除任务成功，trigger_id: {trigger_id}")
            return result > 0
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return False

    @staticmethod
    async def get_all_tasks(limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取所有任务"""
        try:
            query = midjourney_task.select().limit(limit).offset(offset).order_by(
                midjourney_task.c.created_at.desc()
            )
            results = await database.fetch_all(query)
            return [dict(result) for result in results]
        except Exception as e:
            logger.error(f"查询所有任务失败: {e}")
            return []


class UserInfoOperations:
    """用户信息数据库操作类"""

    @staticmethod
    async def get_user_by_app_key(app_key: str) -> Optional[Dict]:
        """根据app_key获取用户信息"""
        try:
            logger.debug(f"🔍 数据库查询用户 - App Key: {app_key}")
            query = user_info.select().where(user_info.c.app_key == app_key)
            result = await database.fetch_one(query)
            if result:
                user_data = dict(result)
                logger.debug(f"✅ 数据库查询成功 - 用户: {user_data.get('user_name')}, ID: {user_data.get('id')}")
                return user_data
            else:
                logger.debug(f"❌ 数据库中未找到用户 - App Key: {app_key}")
                return None
        except Exception as e:
            logger.error(f"❌ 数据库查询用户信息异常 - App Key: {app_key}, 错误: {e}")
            return None

    @staticmethod
    async def get_user_by_username(user_name: str) -> Optional[Dict]:
        """根据用户名获取用户信息"""
        try:
            query = user_info.select().where(user_info.c.user_name == user_name)
            result = await database.fetch_one(query)
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"查询用户信息失败: {e}")
            return None

    @staticmethod
    async def create_user(user_name: str, app_key: str, token_total: int = 0) -> Optional[int]:
        """创建新用户"""
        try:
            query = user_info.insert().values(
                user_name=user_name,
                app_key=app_key,
                token_total=token_total,
                token_use=0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            result = await database.execute(query)
            logger.info(f"创建用户成功，user_name: {user_name}, app_key: {app_key}")
            return result
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return None

    @staticmethod
    async def update_token_usage(app_key: str, token_use_increment: int = 1) -> bool:
        """更新用户token使用量"""
        try:
            # 先获取当前使用量
            query = user_info.update().where(
                user_info.c.app_key == app_key
            ).values(
                token_use=user_info.c.token_use + token_use_increment,
                updated_at=datetime.now()
            )
            result = await database.execute(query)
            if result > 0:
                logger.info(f"更新用户token使用量成功，app_key: {app_key}, increment: {token_use_increment}")
                return True
            return False
        except Exception as e:
            logger.error(f"更新用户token使用量失败: {e}")
            return False

    @staticmethod
    async def check_token_limit(app_key: str) -> bool:
        """检查用户是否还有可用token"""
        try:
            user = await UserInfoOperations.get_user_by_app_key(app_key)
            if not user:
                return False
            
            return user.get('token_use', 0) < user.get('token_total', 0)
        except Exception as e:
            logger.error(f"检查token限制失败: {e}")
            return False


# 创建操作实例
db_ops = MidjourneyTaskOperations()
user_ops = UserInfoOperations() 