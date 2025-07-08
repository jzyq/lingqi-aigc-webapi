from fastapi import APIRouter, Depends
from pydantic import BaseModel
from .. import sessions, deps
import sqlmodel


class APIResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: BaseModel | None = None


class InferenceHistory(BaseModel):
    pass


router = APIRouter(prefix="/gallery")


@router.get("/history", response_model=APIResponse, response_model_exclude_none=True)
async def get_inference_history(
    ses: sessions.Session = Depends(deps.get_user_session),
    db: sqlmodel.Session = Depends(deps.get_db_session)
) -> APIResponse:
    return APIResponse()


@router.delete(
    "/history/{hid}", response_model=APIResponse, response_model_exclude_none=True
)
async def delete_inference_history(hid: str) -> APIResponse:
    return APIResponse()
