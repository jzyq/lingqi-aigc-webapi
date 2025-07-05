import httpx
from fastapi import APIRouter, Request, Response, Depends
from loguru import logger

from ... import deps, config

from .common import NoPointError, InferResponse, point_manager, InferRoute
from sqlmodel import Session


# Forward request to infer server and return is resp code and body.
async def forward_to_infer_srv(url: str, req: Request) -> tuple[int, Response]:
    async with httpx.AsyncClient(timeout=None) as client:
        content = await req.body()
        resp = (
            await client.post(url, content=content, headers=req.headers)
        ).raise_for_status()
        infer_resp = InferResponse.model_validate_json(resp.content)

        return infer_resp.code, Response(content=resp.content, headers=resp.headers)


router = APIRouter(prefix="/infer", route_class=InferRoute)


@router.post("/image")
async def old_replace_with_reference(
    req: Request,
    ses: deps.UserSession,
    db: Session = Depends(deps.get_db_session),
    conf: config.Config = Depends(config.get_config),
) -> Response:

    async with point_manager(ses.uid, db) as pm:
        if pm.magic_points < 10:
            raise NoPointError(ses.uid)

        url = conf.infer.base + conf.infer.replace_any
        code, resp = await forward_to_infer_srv(url, req)

        if code == 0:
            pm.deduct(10)
            logger.info(f"reduce user {ses.nickname} magic points.")

        return resp


@router.post("/replace_any")
async def replace_with_any(
    req: Request,
    ses: deps.UserSession,
    db: Session = Depends(deps.get_db_session),
    conf: config.Config = Depends(config.get_config),
) -> Response:

    async with point_manager(ses.uid, db) as pm:
        if pm.magic_points < 10:
            raise NoPointError(ses.uid)

        url = conf.infer.base + conf.infer.replace_any
        code, resp = await forward_to_infer_srv(url, req)

        if code == 0:
            pm.deduct(10)
            logger.info(f"reduce user {ses.nickname} magic points.")

        return resp


@router.post("/replace_with_reference")
async def replace_with_reference(
    req: Request,
    ses: deps.UserSession,
    db: Session = Depends(deps.get_db_session),
    conf: config.Config = Depends(config.get_config),
) -> Response:

    async with point_manager(ses.uid, db) as pm:
        if pm.magic_points < 10:
            raise NoPointError(ses.uid)

        url = conf.infer.base + conf.infer.replace_any
        code, resp = await forward_to_infer_srv(url, req)

        if code == 0:
            pm.deduct(10)
            logger.info(f"deduct user {ses.nickname} magic points.")

        return resp


@router.post("/image2video")
async def make_i2v_process(
    req: Request,
    ses: deps.UserSession,
    db: Session = Depends(deps.get_db_session),
    conf: config.Config = Depends(config.get_config),
) -> Response:

    async with point_manager(ses.uid, db) as pm:
        if pm.magic_points < 10:
            raise NoPointError(ses.uid)

        url = conf.infer.base + conf.infer.image_to_video
        code, resp = await forward_to_infer_srv(url, req)

        if code == 0:
            pm.deduct(10)
            logger.info(f"reduce user {ses.nickname} magic points.")

        return resp


@router.post("/segment_any")
async def segment_any(
    req: Request,
    ses: deps.UserSession,
    db: Session = Depends(deps.get_db_session),
    conf: config.Config = Depends(config.get_config),
) -> Response:

    async with point_manager(ses.uid, db) as pm:
        if pm.magic_points < 1:
            raise NoPointError(ses.uid)

        url = conf.infer.base + conf.infer.segment_any
        code, resp = await forward_to_infer_srv(url, req)

        if code == 0:
            pm.deduct(1)
            logger.info(f"reduce user {ses.nickname} magic points.")

        return resp
