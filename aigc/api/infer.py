from datetime import datetime

from fastapi import APIRouter, HTTPException
from loguru import logger
from sqlmodel import select

from .. import ai, deps
from ..models import db as db_models
from ..models.infer import i2v as i2v_models
from ..models.infer import replace as replace_models
from ..models.infer import segment as segment_models
import secrets
from http import HTTPStatus

router = APIRouter(prefix="/infer")


@router.post(
    "/image", response_model=replace_models.Response, response_model_exclude_none=True
)
async def replace_with_reference(
    req: replace_models.Request,
    ses: deps.UserSession,
    db: deps.Database,
    conf: deps.Config,
) -> replace_models.Response:
    # read user data check if have magic point.
    subscription = db.exec(
        select(db_models.MagicPointSubscription)
        .where(db_models.MagicPointSubscription.uid == ses.uid)
        .where(db_models.MagicPointSubscription.expired != True)
    ).one()

    if subscription.remains == 0:
        logger.info(
            f"user {ses.nickname}(uid {ses.uid}) try infer but no enough magic point."
        )
        return replace_models.Response(code=1, msg="no more magic points today.")

    url = conf.infer.base + conf.infer.replace_any
    resp = await ai.image.replace_with_any(url, ses.uid, secrets.token_hex(8), req)

    if resp.code == 0:
        subscription.remains -= 10
        subscription.utime = datetime.now()
        db.commit()
        logger.info(f"reduce user {ses.nickname} (uid: {ses.uid}) magic point.")
    return resp


@router.post("/image/async")
async def replace_with_reference_async(
    req: replace_models.Request, ses: deps.UserSession, tasks: deps.ReplaceTasks
) -> replace_models.TaskCreateResponse:
    tid = await tasks.new_request(ses.uid, req)
    return replace_models.TaskCreateResponse(task_id=tid)


@router.get("/image/{task_id}/state")
async def query_replace_task_state(
    task_id: str, ses: deps.UserSession, tasks: deps.ReplaceTasks
) -> replace_models.TaskStateResponse:
    try:
        state = await tasks.queue_state(task_id)
        return replace_models.TaskStateResponse(task_id=task_id, state=state)
    except KeyError:
        raise HTTPException(HTTPStatus.BAD_REQUEST.value, detail="no such task.")


@router.get("/image/{task_id}/result")
async def get_replace_task_result(
    task_id: str, ses: deps.UserSession, tasks: deps.ReplaceTasks
) -> replace_models.Response:
    resp = await tasks.wait_result(task_id)
    return resp


@router.post(
    "/image2video", response_model=i2v_models.Response, response_model_exclude_none=True
)
async def make_i2v_process(
    req: i2v_models.Request, ses: deps.UserSession, db: deps.Database, conf: deps.Config
) -> i2v_models.Response:

    logger.info(f"user {ses.nickname} (uid {ses.uid}) call image to video")
    subscription = db.exec(
        select(db_models.MagicPointSubscription)
        .where(db_models.MagicPointSubscription.uid == ses.uid)
        .where(db_models.MagicPointSubscription.expired != True)
    ).one()
    if subscription.remains == 0:
        logger.info(
            f"user {ses.nickname}(uid {ses.uid}) try image to video but no enough magic point."
        )
        return i2v_models.Response(code=1, msg="no more magic points today.")

    try:
        url = conf.infer.base + conf.infer.image_to_video
        result = await ai.i2v.generate(
            url, ses.uid, req.init_image, req.text_prompt, 300
        )
        logger.debug("generate complete")

        if result.code == 0:
            subscription.remains -= 10
            subscription.utime = datetime.now()
            db.commit()
            logger.info(f"reduce user {ses.nickname} (uid: {ses.uid}) magic point.")

        response = i2v_models.Response(
            code=result.code, msg=result.msg, data=result.data
        )
        return response

    except (ai.GenerateError, ai.ServerError) as e:
        logger.error(f"generate video error, {str(e)}")
        return i2v_models.Response(code=2, msg=str(e))


@router.post(
    "/segment_any",
    response_model=segment_models.Response,
    response_model_exclude_none=True,
)
async def segment_any(
    req: segment_models.Request,
    ses: deps.UserSession,
    db: deps.Database,
    conf: deps.Config,
) -> segment_models.Response:
    logger.info(f"user {ses.nickname} call segment api.")
    subscription = db.exec(
        select(db_models.MagicPointSubscription)
        .where(db_models.MagicPointSubscription.uid == ses.uid)
        .where(db_models.MagicPointSubscription.expired != True)
    ).one()

    if subscription.remains == 0:
        logger.info(
            f"user {ses.nickname}(uid {ses.uid}) try infer but no enough magic point."
        )
        return segment_models.Response(code=1, msg="no more magic points today.")

    url = conf.infer.base + conf.infer.segment_any
    resp = await ai.segment.segment(url, req)
    if resp.code == 0:
        subscription.remains -= 1
        subscription.utime = datetime.now()
        logger.info(f"reduce user {ses.nickname} uid {ses.uid} magic point.")
        db.commit()
    return resp
