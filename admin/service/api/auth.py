from fastapi import APIRouter, Depends
from pydantic import BaseModel
import redis.asyncio as redis
from .. import depends, session, config, models


class LoginRequest(BaseModel):
    username: str
    password: str


router = APIRouter(prefix="/auth")


@router.post(
    "/login", response_model=models.APIResponse, response_model_exclude_none=True
)
async def login(
    login_req: LoginRequest, rdb: redis.Redis = Depends(depends.get_rdb)
) -> models.APIResponse:
    conf = config.AppConfig()

    if (
        login_req.username != conf.superuser
        or login_req.password != conf.superuser_password
    ):
        return models.APIResponse(code=1, msg="username or password incorrect")

    token = await session.create_session(rdb, login_req.username)
    return models.APIResponse(data={"token": token})
