import asyncio
from collections import deque
from os import getenv
from typing import ParamSpec, Callable, Any, Dict, List, Deque

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

    async def __call__(self) -> None:
        await self.func(*self.args, **self.kwargs)

    def __repr__(self) -> str:
        return f"{self.func.__name__}({self.args}, {self.kwargs})"


class TaskQueue:
    def __init__(self, concur_size: int, wait_size: int) -> None:
        self._concur_size = concur_size
        self._wait_size = wait_size
        self._wait_queue: Deque[Dict[str, Task]] = deque()
        self._concur_queue: List[str] = []

    def put(
            self,
            _trigger_id: str,
            func: Callable[P, Any],
            *args: P.args,
            **kwargs: P.kwargs
    ) -> None:
        if len(self._wait_queue) >= self._wait_size:
            raise QueueFullError(f"Task queue is full: {self._wait_size}")

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
            self._concur_queue.remove(_trigger_id)
            if self._wait_queue:
                self._exec()
        except ValueError:
            pass

    def _exec(self):
        try:
            key, task = self._wait_queue.popleft().popitem()
            self._concur_queue.append(key)

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


taskqueue = TaskQueue(
    int(getenv("CONCUR_SIZE") or 9999),
    int(getenv("WAIT_SIZE") or 9999),
)
