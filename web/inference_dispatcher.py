import asyncio
from typing import Any
from loguru import logger
from models import inferences
from datetime import datetime
from pymongo.asynchronous.database import AsyncDatabase
from typing import Any
import json
import gridfs
import httpx


class Dispatcher:

    def __init__(self, db: AsyncDatabase) -> None:
        self.__db = db

    async def serve_forever(self) -> None:

        while True:
            waiting_tasks = (
                inferences.Inference.find(
                    inferences.Inference.state == inferences.State.waiting,
                    with_children=True,
                )
                .sort("+ctime")
                .limit(10)
            )

            async for task in waiting_tasks:
                logger.info(f"find waiting task {task.id}")

                await task.sync()

                if task.state == inferences.State.waiting:
                    task.state = inferences.State.processing
                    task.utime = datetime.now()
                    await task.save()
                else:
                    continue

                if isinstance(task, inferences.StandardTask):
                    await self.__process_standard_task(task)
                if isinstance(task, inferences.CompositeTask):
                    await self.__process_composite_task(task)

            await asyncio.sleep(1)

    async def __process_standard_task(self, task: inferences.StandardTask) -> None:
        logger.info(f"process standard inference task {task.id}")
        url = task.request.url
        body = await self.__read_request_data(task.request)

        resp = await self.__send_request(url, body)

        task.response = inferences.Response.in_place(resp)
        task.state = inferences.State.down
        task.utime = datetime.now()
        await task.save()

        await self.__notify_down(task.callback, resp)

    async def __process_composite_task(self, task: inferences.CompositeTask) -> None:
        logger.info(
            f"process composite inference task {task.id}, total request {len(task.requests)}"
        )

        responses = []
        for i in range(len(task.requests)):
            req = task.requests[i]
            url = req.url
            logger.debug(f"process request {i}, url: {url}")

            body = await self.__read_request_data(req)
            resp = await self.__send_request(url, body)
            logger.debug(
                f"request {i} have response, code: {resp['code']}, msg: {resp['msg']}"
            )

            responses.append(resp)
            task.response.append(inferences.Response.in_place(resp))
            task.utime = datetime.now()
            await task.save()

        task.state = inferences.State.down
        task.utime = datetime.now()
        await task.save()
        logger.info(f"task {task.id} complete.")

        await self.__notify_down(task.callback, {"results": responses})

    async def __read_request_data(self, req: inferences.Request) -> dict[str, Any]:
        match req.data_source:
            case inferences.DataSource.in_place:
                return req.data
            case inferences.DataSource.gridfs:
                fs = gridfs.AsyncGridFS(self.__db)
                out = await fs.get(file_id=req.data)
                return json.load(out)

    async def __send_request(self, url: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                resp = await client.post(url=url, json=body)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error(f"inference request failed, {str(e)}")
            return {"code": 1, "msg": f"sending inference request error: {e}"}

    async def __notify_down(self, url: str, resp: dict[str, Any]) -> None:
        logger.debug(f"call task callback url {url}")
        async with httpx.AsyncClient() as client:
            await client.post(url=url, json=resp)


if __name__ == "__main__":

    from argparse import ArgumentParser
    from pymongo import AsyncMongoClient
    import models

    async def main() -> None:
        parser = ArgumentParser()
        parser.add_argument("url")
        arguments = parser.parse_args()

        client = AsyncMongoClient(arguments.url)
        await models.init(client.aigc)

        dispatcher = Dispatcher(client.aigc)
        await dispatcher.serve_forever()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        print("service exit.")
