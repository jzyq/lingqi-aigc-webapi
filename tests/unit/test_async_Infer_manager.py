import asyncio
from unittest import mock, IsolatedAsyncioTestCase
from aigc.async_task_manager import AsyncTaskManager, TaskState
from aigc.models.infer import replace


class TestAsyncInferManager(IsolatedAsyncioTestCase):

    async def test_add_new_task(self) -> None:
        fake_req = replace.Request()
        fake_proxy = mock.AsyncMock()
        mgr: AsyncTaskManager[replace.Request,
                              replace.Response] = AsyncTaskManager(1, fake_proxy)

        tid = await mgr.new_request(1, fake_req)

        self.assertIn(tid, mgr.tasks)

    async def test_call_proxy(self) -> None:
        fake_req = replace.Request()
        fake_proxy = mock.AsyncMock()

        mgr: AsyncTaskManager[replace.Request,
                              replace.Response] = AsyncTaskManager(1, fake_proxy)

        tid = await mgr.new_request(1, fake_req)
        await asyncio.sleep(0.1)
        fake_proxy.assert_called_once_with(1, tid, fake_req)

    async def test_queue_state(self) -> None:
        fake_req = replace.Request()
        fake_proxy = mock.AsyncMock()

        async def sleep(*_) -> None:
            await asyncio.sleep(0.1)
        fake_proxy.side_effect = sleep

        mgr: AsyncTaskManager[replace.Request,
                              replace.Response] = AsyncTaskManager(1, fake_proxy)

        tid = await mgr.new_request(1, fake_req)
        await asyncio.sleep(0)
        state = await mgr.queue_state(tid)

        self.assertEqual(state, TaskState.infer)

    async def test_wait_result(self) -> None:
        fake_req = replace.Request()
        fake_proxy = mock.AsyncMock()
        fake_resp = replace.Response(code=0, msg="ok")
        fake_proxy.return_value = fake_resp

        mgr: AsyncTaskManager[replace.Request,
                              replace.Response] = AsyncTaskManager(1, fake_proxy)

        tid = await mgr.new_request(1, fake_req)
        resp = await mgr.wait_result(tid)

        self.assertEqual(resp, fake_resp)
