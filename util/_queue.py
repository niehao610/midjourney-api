import asyncio
from collections import deque
from os import getenv
from typing import ParamSpec, Callable, Any, Dict, List, Deque
import time
from datetime import datetime, timedelta

from loguru import logger

from exceptions import QueueFullError

P = ParamSpec("P")


class Task:
    def __init__(
        self, func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs
    ) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.created_at = datetime.now()  # 添加创建时间戳

    async def __call__(self) -> None:
        await self.func(*self.args, **self.kwargs)

    def __repr__(self) -> str:
        return f"{self.func.__name__}({self.args}, {self.kwargs})"
    
    def is_expired(self, timeout_minutes: int = 5) -> bool:
        """检查任务是否已超时"""
        return datetime.now() - self.created_at > timedelta(minutes=timeout_minutes)


class TaskQueue:
    def __init__(self, concur_size: int, wait_size: int) -> None:
        self._concur_size = concur_size
        self._wait_size = wait_size
        self._wait_queue: Deque[Dict[str, Task]] = deque()
        self._concur_queue: List[str] = []
        self._concur_start_times: Dict[str, datetime] = {}  # 记录并发任务开始时间
        self._cleanup_task = None  # 清理任务的引用
        self._start_cleanup_timer()  # 启动定时清理

    def put(
            self,
            _trigger_id: str,
            func: Callable[P, Any],
            *args: P.args,
            **kwargs: P.kwargs
    ) -> None:
        if len(self._wait_queue) >= self._wait_size:
            raise QueueFullError(f"Task queue is full: {self._wait_size}")

        # 确保定时清理任务已启动
        if self._cleanup_task is None or self._cleanup_task.done():
            self._start_cleanup_timer()

        task = Task(func, *args, **kwargs)
        self._wait_queue.append({
            _trigger_id: task
        })
        
        logger.info(f"📝 Task[{_trigger_id}] 添加到队列: {task}")
        logger.info(f"📊 队列状态 - 等待: {len(self._wait_queue)}, 并发: {len(self._concur_queue)}/{self._concur_size}")
        
        while self._wait_queue and len(self._concur_queue) < self._concur_size:
            self._exec()

    def pop(self, _trigger_id: str) -> None:
        try:
            logger.info(f"🧹 Task[{_trigger_id}] 从并发队列移除!!!!!!!!!!!!!")
            self._concur_queue.remove(_trigger_id)
            # 清理开始时间记录
            if _trigger_id in self._concur_start_times:
                del self._concur_start_times[_trigger_id]
            if self._wait_queue:
                self._exec()
        except ValueError:
            pass

    def _exec(self):
        try:
            key, task = self._wait_queue.popleft().popitem()
            self._concur_queue.append(key)
            # 记录任务开始时间
            self._concur_start_times[key] = datetime.now()

            logger.info(f"🚀 Task[{key}] 开始执行: {task}")
            
            loop = asyncio.get_running_loop()
            tsk = loop.create_task(task())
            
            def task_done_callback(future):
                try:
                    result = future.result()
                    logger.info(f"✅ Task[{key}] 执行成功")
                except Exception as e:
                    logger.error(f"❌ Task[{key}] 执行失败: {e}")
                    logger.exception(e)
                # finally:
                #     # 🔥 关键修复：任务完成后自动从并发队列移除
                #     logger.info(f"🧹 Task[{key}] 从并发队列移除")
                #     self.pop(key)
            
            tsk.add_done_callback(task_done_callback)
            
        except Exception as e:
            logger.error(f"❌ 队列执行异常: {e}")
            logger.exception(e)

    def concur_size(self):
        return self._concur_size

    def wait_size(self):
        return self._wait_size

    def clear_wait(self):
        self._wait_queue.clear()

    def clear_concur(self):
        self._concur_queue.clear()
    
    def _start_cleanup_timer(self):
        """启动定时清理任务"""
        try:
            loop = asyncio.get_running_loop()
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = loop.create_task(self._periodic_cleanup())
                logger.info("🕐 队列定时清理任务已启动")
        except RuntimeError:
            # 如果没有运行中的事件循环，稍后再启动
            logger.warning("⚠️ 暂无运行中的事件循环，定时清理将在队列使用时启动")
    
    async def _periodic_cleanup(self):
        """定期清理超时任务"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                await self._cleanup_expired_tasks()
            except asyncio.CancelledError:
                logger.info("🛑 队列定时清理任务已停止")
                break
            except Exception as e:
                logger.error(f"❌ 定时清理任务异常: {e}")
                logger.exception(e)
    
    async def _cleanup_expired_tasks(self):
        """清理超时的任务"""
        current_time = datetime.now()
        timeout_minutes = 5
        
        # 清理等待队列中的超时任务
        expired_wait_tasks = []
        for i, task_dict in enumerate(self._wait_queue):
            for trigger_id, task in task_dict.items():
                if task.is_expired(timeout_minutes):
                    expired_wait_tasks.append((i, trigger_id))
        
        # 从后往前删除，避免索引问题
        for i, trigger_id in reversed(expired_wait_tasks):
            try:
                del self._wait_queue[i]
                logger.warning(f"⏰ 等待队列中超时任务已清理: {trigger_id}")
                # 更新数据库状态
                await self._update_task_timeout_status(trigger_id)
            except IndexError:
                pass
        
        # 清理并发队列中的超时任务
        expired_concur_tasks = []
        for trigger_id in self._concur_queue[:]:  # 创建副本避免修改时迭代
            start_time = self._concur_start_times.get(trigger_id)
            if start_time and current_time - start_time > timedelta(minutes=timeout_minutes):
                expired_concur_tasks.append(trigger_id)
        
        for trigger_id in expired_concur_tasks:
            try:
                self._concur_queue.remove(trigger_id)
                if trigger_id in self._concur_start_times:
                    del self._concur_start_times[trigger_id]
                logger.warning(f"⏰ 并发队列中超时任务已清理: {trigger_id}")
                # 更新数据库状态
                await self._update_task_timeout_status(trigger_id)
                
                # 尝试启动等待队列中的下一个任务
                if self._wait_queue:
                    self._exec()
            except ValueError:
                pass
        
        if expired_wait_tasks or expired_concur_tasks:
            logger.info(f"🧹 队列清理完成 - 等待队列清理: {len(expired_wait_tasks)}, 并发队列清理: {len(expired_concur_tasks)}")
            logger.info(f"📊 当前队列状态 - 等待: {len(self._wait_queue)}, 并发: {len(self._concur_queue)}/{self._concur_size}")
    
    async def _update_task_timeout_status(self, trigger_id: str):
        """更新超时任务的数据库状态"""
        try:
            # 动态导入避免循环导入
            from lib.db_operations import db_ops
            await db_ops.update_task_status(trigger_id, "TIMEOUT")
            logger.info(f"📝 任务超时状态已更新至数据库: {trigger_id}")
        except Exception as e:
            logger.error(f"❌ 更新任务超时状态失败: {trigger_id} - {e}")
    
    def get_queue_status(self):
        """获取队列状态信息"""
        return {
            "wait_queue_size": len(self._wait_queue),
            "concur_queue_size": len(self._concur_queue),
            "max_concur_size": self._concur_size,
            "max_wait_size": self._wait_size,
            "concur_tasks": list(self._concur_queue),
            "concur_start_times": {k: v.isoformat() for k, v in self._concur_start_times.items()}
        }


taskqueue = TaskQueue(
    int(getenv("CONCUR_SIZE") or 9999),
    int(getenv("WAIT_SIZE") or 9999),
)
