from pyexpat import model
import requests
from fastapi import APIRouter, Request, Response
from . import models, deps
from sqlmodel import select
from datetime import datetime
from loguru import logger


BASE_URL = "http://zdxai.iepose.cn"
REPLACE_WITH_ANY = BASE_URL + "/replace_with_any"
IMAGE_TO_VIDEO = "https://115c-116-172-93-214.ngrok-free.app/wan_video_i2v_accelerate"


router = APIRouter(prefix="/infer")


@router.post("/image",  response_model=models.infer.ReplaceResponse, response_model_exclude_none=True)
def replace_with_reference(req: models.infer.ReplaceRequest, ses: deps.UserSession, db: deps.Database) -> models.infer.ReplaceResponse:
    # read user data check if have magic point.
    subscription = db.exec(select(models.db.MagicPointSubscription).where(
        models.db.MagicPointSubscription.uid == ses.uid).where(models.db.MagicPointSubscription.expired != True)).one()

    if subscription.remains == 0:
        logger.info(
            f"user {ses.nickname}(uid {ses.uid}) try infer but no enough magic point.")
        return models.infer.ReplaceResponse(code=1, msg="no more magic points today.")

    resp = requests.post(REPLACE_WITH_ANY,
                         json=req.model_dump(by_alias=True))

    if resp.status_code != 200:
        logger.error(
            f"infer server response status code {resp.status_code}, detail: {resp.text}")
        return models.infer.ReplaceResponse(code=2, msg="infer server unavailable.")

    if resp.headers['content-type'] != 'application/json':
        logger.error(
            f"expect infer result to be a json but actual is {resp.headers['content-type']}")
        logger.error(f"resp: {resp.text}")
        return models.infer.ReplaceResponse(code=3, msg="response data not json")

    infer_data = models.infer.ReplaceResponse.model_validate_json(
        resp.content)
    logger.debug("infer success complete.")

    if infer_data.code == 0:
        subscription.remains -= 1
        subscription.utime = datetime.now()
        db.commit()
        logger.info(
            f"reduce user {ses.nickname} (uid: {ses.uid}) magic point.")
    return infer_data


@router.post("/image2video", response_model=models.infer.Image2VideoResponse, response_model_exclude_none=True)
def make_i2v_process(req: models.infer.Image2VideoRequest, ses: deps.UserSession, db: deps.Database) -> models.infer.Image2VideoResponse:

    logger.info(f"user {ses.nickname} (uid {ses.uid}) call image to video")
    subscription = db.exec(select(models.db.MagicPointSubscription).where(
        models.db.MagicPointSubscription.uid == ses.uid).where(models.db.MagicPointSubscription.expired != True)).one()
    if subscription.remains == 0:
        logger.info(
            f"user {ses.nickname}(uid {ses.uid}) try image to video but no enough magic point.")
        return models.infer.Image2VideoResponse(code=1, msg="no more magic points today.")

    resp = requests.post(IMAGE_TO_VIDEO, json=req.model_dump())
    logger.debug("infer server response")

    if resp.status_code != 200:
        logger.error(f"infer server respose error, code {resp.status_code}")
        return models.infer.Image2VideoResponse(code=2, msg="infer server error")

    body = resp.json()
    if "error" in body:
        res = models.infer.Image2VideoResponse(code=3, msg=body["error"])
        logger.warning(f"gen image error, res: {res.msg}")
        return res

    else:
        res = models.infer.Image2VideoResponse.model_validate(body)
        if res.code == 0:
            subscription.remains -= 1
            subscription.utime = datetime.now()
            db.commit()
            logger.info(
                f"reduce user {ses.nickname} (uid: {ses.uid}) magic point.")

        return res
