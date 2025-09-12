import asyncio
from loguru import logger
from models import inferences
from datetime import datetime
from pymongo.asynchronous.database import AsyncDatabase
import httpx
import oss
import base64
from pydantic import BaseModel


class InferenceRequest(BaseModel):
    init_image: str
    text_prompt: str | None = None


class Dispatcher:

    def __init__(self, db: AsyncDatabase) -> None:
        self.__db = db

    async def serve_forever(self) -> None:

        while True:
            try:
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

                    # TODO: change timeout be a config params.
                    try:
                        async with asyncio.timeout(1800):
                            await self.__serve_next(task)
                            await self.__callback(task)
                    except asyncio.TimeoutError:
                        task.state = inferences.State.error
                        task.utime = datetime.now()
                        await task.save()

                await asyncio.sleep(1)

            except asyncio.CancelledError as e:
                raise e
            except Exception as exc:
                logger.error(f"inference dispatcher serve error: {exc}")

    async def __serve_next(self, task: inferences.Inference) -> None:
        await task.sync()

        if task.state == inferences.State.waiting:
            task.state = inferences.State.processing
            task.utime = datetime.now()
            await task.save()
        else:
            return

        if isinstance(task, inferences.StandardTask):
            await self.__process_standard_task(task)
        if isinstance(task, inferences.CompositeTask):
            await self.__process_composite_task(task)

    async def __process_standard_task(self, task: inferences.StandardTask) -> None:
        logger.info(f"process standard inference task {task.id}")

        # Sending request.
        body = await self.__read_request_data(task.request)
        resp = await self.__send_request(task.request.url, body)
        logger.debug(f"task have response, code {resp.code}, msg {resp.msg}")

        # Check result.
        if resp.code != 0:
            logger.error(f"task {task.id} encounter error, abort")
            return await task.set_error(code=resp.code, msg=resp.msg)

        if resp.data and len(resp.data) > 0:
            return await task.set_success(resp.data[0])
        else:
            logger.error("inference response must set data.")
            return await task.set_error(
                code=1, msg="invalid response data, data must be set."
            )

    async def __process_composite_task(self, task: inferences.CompositeTask) -> None:
        if not task.requests:
            raise ValueError("task requests must not be none, task not ready.")

        logger.info(
            f"process composite inference task {task.id}, total request {len(task.requests)}"
        )

        # Sending request one by one.
        for i in range(len(task.requests)):
            req = task.requests[i]
            logger.debug(f"process request {i}, url: {req.url}")

            # Sending request.
            body = await self.__read_request_data(req)
            resp = await self.__send_request(req.url, body)
            logger.debug(
                f"request {i} of task {task.id} have response, code: {resp.code}, msg: {resp.msg}"
            )

            # Check response code.
            if resp.code != 0:
                logger.error(f"task {task.id} encounter inference error, abort.")
                return await task.set_error(code=resp.code, msg=resp.msg)

            # Check result, set result if have, else abort task.
            if resp.data and len(resp.data) > 0:
                await task.add_data(resp.data[0])
            else:
                logger.error("inference response set result, but not found.")
                return await task.set_error(
                    code=1, msg="invalid inference response data."
                )

        logger.info(f"task {task.id} complete.")
        return await task.set_success()

    async def __read_request_data(self, req: inferences.Request) -> InferenceRequest:
        match req.image_source:
            case inferences.DataSource.in_place:
                request = InferenceRequest(
                    init_image=req.image, text_prompt=req.aigc_prompt
                )
                return request
            case inferences.DataSource.gridfs:
                async with oss.load_file(req.image) as fp:
                    request = InferenceRequest(
                        init_image=base64.b64encode(await fp.read()).decode(),
                        text_prompt=req.aigc_prompt,
                    )
                    return request

    async def __send_request(
        self, url: str, body: InferenceRequest
    ) -> inferences.InferenceResult:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                resp = await client.post(
                    url=url, json=body.model_dump(exclude_none=True)
                )
                resp.raise_for_status()
                return inferences.InferenceResult.model_validate_json(resp.content)
        except httpx.HTTPError as e:
            logger.error(f"inference request failed, {str(e)}")
            return inferences.InferenceResult(
                code=1, msg=f"sending inference request error: {e}"
            )

    async def __callback(self, task: inferences.Inference) -> None:
        logger.debug(f"call task callback url {task.callback}")

        cb_data = inferences.CallbackData(userdata=task.userdata, state=task.state)
        if isinstance(task, inferences.StandardTask):
            cb_data.result = task.response
        if isinstance(task, inferences.CompositeTask):
            cb_data.result = task.response

        async with httpx.AsyncClient() as client:
            await client.post(url=task.callback, json=cb_data.model_dump())


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
