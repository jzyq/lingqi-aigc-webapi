from dataclasses import dataclass, field
from enum import StrEnum
from .models.infer import replace, i2v, segment
import asyncio
import secrets

from typing import TypeVar, Generic, TypeAlias
from collections.abc import Callable, Awaitable

ReqT = TypeVar("ReqT", replace.Request, i2v.Request, segment.Request)
RespT = TypeVar("RespT", replace.Response, i2v.Response, segment.Response)


InferProxy: TypeAlias = Callable[[int, str, ReqT], Awaitable[RespT]]


class TaskStage(StrEnum):
    waiting = "waiting"
    infer = "infer"
    down = "down"
    canceled = "canceled"


@dataclass
class AsyncInferTask(Generic[ReqT, RespT]):
    uid: int
    tid: str
    stage: TaskStage = field(default=TaskStage.waiting, init=False)

    request: ReqT
    response: RespT | None = field(default=None, init=False)


class AsyncTaskManager(Generic[ReqT, RespT]):

    def __init__(self, max_working_task: int, proxy: InferProxy[ReqT, RespT]) -> None:
        self.cond: asyncio.Condition = asyncio.Condition()

        # To store all tasks data.
        self.tasks: dict[str, AsyncInferTask[ReqT, RespT]] = {}

        # Queue waiting tasks.
        self.waiting: asyncio.Queue[str] = asyncio.Queue()

        # Use to reference background tasks to protect from GC.
        self.backgrounds: set[asyncio.Task[None]] = set()

        # To limit the max paraillel requests.
        self.max_working_task_cnt: int = max_working_task

        # A proxy callable use send actual infer request to infer server.
        self.infer_proxy: InferProxy[ReqT, RespT] = proxy

        # Dispatcher task run in background.
        self.dispatch_task = asyncio.create_task(self.dispatch_forever())

    # Poll task from queue and send request, update state and response.
    async def dispatch_forever(self) -> None:
        async with self.cond:
            await self.cond.wait_for(lambda: len(self.backgrounds) < self.max_working_task_cnt)

            tid = await self.waiting.get()
            next_task = self.tasks[tid]

            if next_task.stage == TaskStage.canceled:
                self.waiting.task_done()
                self.cond.notify_all()

            next_task.stage = TaskStage.infer
            handler = asyncio.create_task(self.handler(next_task))
            self.backgrounds.add(handler)
            handler.add_done_callback(self.backgrounds.discard)

    async def new_request(self, uid: int, req: ReqT) -> str:
        async with self.cond:
            tid = secrets.token_hex(8)
            self.tasks[tid] = AsyncInferTask[ReqT, RespT](uid, tid, req)
            await self.waiting.put(tid)
            self.cond.notify_all()

        return tid

    async def handler(self, task: AsyncInferTask[ReqT, RespT]):
        resp = await self.infer_proxy(task.uid, task.tid, task.request)

        async with self.cond:
            task.response = resp
            task.stage = TaskStage.down
            self.cond.notify_all()

    async def queue_state(self, tid: str) -> TaskStage:
        async with self.cond:
            if tid not in self.tasks:
                raise KeyError("no such task")
            return self.tasks[tid].stage

    async def wait_result(self, tid: str) -> RespT:
        async with self.cond:
            if tid not in self.tasks:
                raise KeyError("no such task")
            task = self.tasks[tid]
            await self.cond.wait_for(lambda: task.response is not None)

            if task.response is None:
                raise AssertionError("task response should not be none")
            return task.response
