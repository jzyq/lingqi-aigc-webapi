import requests
from fastapi import APIRouter
from . import models, deps
from sqlmodel import select
from datetime import datetime
from loguru import logger


BASE_URL = "http://zdxai.iepose.cn"
REPLACE_WITH_ANY = BASE_URL + "/replace_with_any"

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
