from datetime import datetime

import requests
from fastapi import APIRouter
from loguru import logger
from sqlmodel import select

from . import ai, deps
from .models import db as db_models
from .models import infer

BASE_URL = "http://zdxai.iepose.cn"
REPLACE_WITH_ANY = BASE_URL + "/replace_with_any"
IMAGE_TO_VIDEO = "https://115c-116-172-93-214.ngrok-free.app/wan_video_i2v_accelerate"


router = APIRouter(prefix="/infer")


@router.post("/image",  response_model=infer.ReplaceResponse, response_model_exclude_none=True)
def replace_with_reference(req: infer.ReplaceRequest, ses: deps.UserSession, db: deps.Database) -> infer.ReplaceResponse:
    # read user data check if have magic point.
    subscription = db.exec(select(db_models.MagicPointSubscription).where(
        db_models.MagicPointSubscription.uid == ses.uid).where(db_models.MagicPointSubscription.expired != True)).one()

    if subscription.remains == 0:
        logger.info(
            f"user {ses.nickname}(uid {ses.uid}) try infer but no enough magic point.")
        return infer.ReplaceResponse(code=1, msg="no more magic points today.")

    resp = requests.post(REPLACE_WITH_ANY,
                         json=req.model_dump(by_alias=True))

    if resp.status_code != 200:
        logger.error(
            f"infer server response status code {resp.status_code}, detail: {resp.text}")
        return infer.ReplaceResponse(code=2, msg="infer server unavailable.")

    if resp.headers['content-type'] != 'application/json':
        logger.error(
            f"expect infer result to be a json but actual is {resp.headers['content-type']}")
        logger.error(f"resp: {resp.text}")
        return infer.ReplaceResponse(code=3, msg="response data not json")

    infer_data = infer.ReplaceResponse.model_validate_json(
        resp.content)
    logger.debug("infer success complete.")

    if infer_data.code == 0:
        subscription.remains -= 1
        subscription.utime = datetime.now()
        db.commit()
        logger.info(
            f"reduce user {ses.nickname} (uid: {ses.uid}) magic point.")
    return infer_data


@router.post("/image2video", response_model=infer.i2v.Response, response_model_exclude_none=True)
async def make_i2v_process(req: infer.i2v.Request, ses: deps.UserSession, db: deps.Database) -> infer.i2v.Response:

    logger.info(f"user {ses.nickname} (uid {ses.uid}) call image to video")
    subscription = db.exec(select(db_models.MagicPointSubscription).where(
        db_models.MagicPointSubscription.uid == ses.uid).where(db_models.MagicPointSubscription.expired != True)).one()
    if subscription.remains == 0:
        logger.info(
            f"user {ses.nickname}(uid {ses.uid}) try image to video but no enough magic point.")
        return infer.i2v.Response(code=1, msg="no more magic points today.")

    try:
        result = await ai.i2v.generate(ses.uid, req.init_image, req.text_prompt, 300)
        logger.debug("generate complete")

        if result.code == 0:
            subscription.remains -= 1
            subscription.utime = datetime.now()
            db.commit()
            logger.info(
                f"reduce user {ses.nickname} (uid: {ses.uid}) magic point.")

        response = infer.i2v.Response(
            code=result.code, msg=result.msg, data=result.data)
        return response

    except (ai.GenerateError, ai.ServerError) as e:
        logger.error(f"generate video error, {str(e)}")
        return infer.i2v.Response(code=2, msg=str(e))
