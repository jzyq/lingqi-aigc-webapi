import requests
from fastapi import APIRouter
from . import models


BASE_URL = "http://zdxai.iepose.cn"
REPLACE_WITH_ANY = BASE_URL + "/replace_with_any"

router = APIRouter(prefix="/infer")


# TODO: add auth control and magic point limit.
@router.post("/image")
def replace_with_reference(req: models.infer.ReplaceRequest) -> models.infer.ReplaceResponse:
    resp = requests.post(REPLACE_WITH_ANY,
                         json=req.model_dump(by_alias=True))
    if resp.status_code == 200:
        return models.infer.ReplaceResponse.model_validate_json(resp.content)
    raise Exception(resp.content.decode())
