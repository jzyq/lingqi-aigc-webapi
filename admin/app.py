from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse
import uvicorn
from service import config, api
from contextlib import asynccontextmanager

from sqlmodel import create_engine
import database
import redis.asyncio
from os import path


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    conf = config.AppConfig()
    engine = create_engine(conf.db_url)
    database.create_all_tables(engine)

    async_rdb = redis.asyncio.Redis(
        host=conf.redis_host,
        port=conf.redis_port,
        db=conf.redis_db,
        decode_responses=True,
    )

    app.state.db = engine
    app.state.rdb = async_rdb

    yield

    await async_rdb.close()


conf = config.AppConfig()

app = FastAPI(lifespan=app_lifespan)

ui_prefix = ""
api_prefix = "/api"

if conf.mode == "dev":
    service_prefix = "/aigc/admin"
    ui_prefix = service_prefix + ui_prefix
    api_prefix = service_prefix + api_prefix

# Do not change the order of router define.
main_router = APIRouter(prefix=api_prefix)
main_router.include_router(api.system_config.router)
main_router.include_router(api.auth.router)
app.include_router(main_router)


@app.get(ui_prefix + "/")
@app.get(ui_prefix + "/{filepath:path}")
async def serve_ui(filepath: str = "") -> FileResponse:
    print(f"file path: {filepath}")
    if filepath == "":
        filepath = path.join(conf.ui_base, "index.html")
    else:
        filepath = path.join(conf.ui_base, filepath)

    if not path.exists(filepath):
        filepath = path.join(conf.ui_base, "index.html")

    return FileResponse(filepath)


if __name__ == "__main__":
    uvicorn.run(app, host=conf.api_host, port=conf.api_port)
