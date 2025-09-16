from fastapi import FastAPI
from . import cloud_env, rpc, login


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(cloud_env.router)
    app.include_router(rpc.router)
    app.include_router(login.router)

    return app
