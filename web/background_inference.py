import asyncio
import httpx
from enum import StrEnum
import secrets
from typing import NamedTuple
from .common.excpetions import NotFoundError


class State(StrEnum):
    in_progess = "in progess"
    down = "down"


class Req(NamedTuple):
    state: State
    resp: httpx.Response | None = None


class ReqDict:

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._cond = asyncio.Condition()
        self._requests: dict[str, Req] = {}

    async def new_request(self) -> str:
        tid = secrets.token_hex(8)
        async with self._lock:
            r = Req(State.in_progess)
            self._requests[tid] = r

        return tid

    async def state(self, tid: str) -> State:
        async with self._lock:
            if tid not in self._requests:
                raise NotFoundError("no such request")
            return self._requests[tid].state

    async def response(self, tid: str) -> httpx.Response | None:
        async with self._lock:
            if tid not in self._requests:
                raise NotFoundError("no such request")
            return self._requests[tid].resp

    async def wait_response(self, tid: str) -> httpx.Response:
        async with self._cond:
            if tid not in self._requests:
                raise NotFoundError("no such request")

            await self._cond.wait_for(lambda: self._requests[tid].state == State.down)
            resp = self._requests[tid].resp

            if resp is None:
                raise AssertionError("resp must not be none when request down")
            return resp

    async def set_response(self, tid: str, resp: httpx.Response):
        async with self._cond:
            if tid not in self._requests:
                raise NotFoundError("no such request")
            self._requests[tid] = Req(
                State.down, resp)
            self._cond.notify_all()
