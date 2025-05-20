from fastapi import FastAPI


def set_wx_app_id_and_secret(app: FastAPI, app_id: str, app_secret: str):
    app.state.wx_app_id = app_id
    app.state.wx_app_secret = app_secret

def get_wx_app_id_and_secret(app: FastAPI) -> tuple[str, str]:
    return (app.state.wx_app_id, app.state.wx_app_secret)