from fastapi import APIRouter
from pydantic import BaseModel
from typing import Sequence
from .lib.heaven_album import HeavenAlbum


class UpdateTaskStateRequest(BaseModel):
    tid: str
    state: str
    images: Sequence[str] | None = None


class UpdateTaskStateResponse(BaseModel):
    pass


router = APIRouter(prefix="/rpc")


@router.post("/heaven_album/task/state")
async def update_task_state(req: UpdateTaskStateRequest) -> UpdateTaskStateResponse:
    ha = HeavenAlbum()
    await ha.update_task(req.tid, req.state, req.images)
    return UpdateTaskStateResponse()
