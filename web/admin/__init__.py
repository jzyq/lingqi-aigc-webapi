from fastapi import FastAPI
from pydantic import BaseModel
from models import inferences
from typing import Any
from loguru import logger

webapp = FastAPI()


class ListInferenceTaskResp(BaseModel):
    offset: int
    limit: int
    total: int
    tasks: Any


@webapp.get("/inference/tasks")
async def list_inference_task(offset: int, limit: int = 10):
    tasks = (
        await inferences.Inference.find_all(with_children=True)
        .sort("-ctime")
        .skip(offset)
        .limit(limit)
        .to_list()
    )
    logger.debug(tasks)

    cnt = await inferences.Inference.find_all(with_children=True).count()

    return ListInferenceTaskResp(offset=offset, limit=limit, total=cnt, tasks=tasks)
