import redis.asyncio
import uvicorn
import config, api, infer_dispatch, refresh_subscriptions
import redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel, create_engine
from loguru import logger
from threading import Thread
import mainpage_config


def main(conf: config.AppConfig) -> None:

    # Setup redis client.
    async_rdb = redis.asyncio.Redis(
        host=conf.redis_host,
        port=conf.redis_port,
        db=conf.redis_db,
        decode_responses=True,
    )

    # Setup database client.
    db = create_engine(conf.db_url)
    SQLModel.metadata.create_all(db)

    # start refresh subscription.
    refresh_thread = Thread(
        target=refresh_subscriptions.arrage_refresh_subscriptions,
        args=(db,),
        daemon=True,
    )
    refresh_thread.start()

    srv = infer_dispatch.Server(db)
    dispatch_thread = Thread(target=srv.serve_forever, daemon=True)
    dispatch_thread.start()

    # Use app lifespan function to cleanup resource after shutdown.
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.db = db
        app.state.rdb = async_rdb
        yield
        await async_rdb.aclose()

    rc = mainpage_config.RemoteConfig(
        app_id="cli_a8f212a1f91c501c",
        secret="KSRIFs0wipqk4zTv6LBVZd0xPyxjHs3E",
        bitable_id="UrycwJ6bQiWmEqkyU74cSh01nNh",
    )
    mrc = mainpage_config.MainPageRemoteConfig(conf, rc)
    mrc.refresh_banner()
    mrc.refresh_magic()
    mrc.refresh_shortcut()

    app = FastAPI(lifespan=lifespan)
    app.include_router(api.router)

    if conf.mode == "dev":
        logger.info("develop mode")
        app.include_router(api.dev.router, prefix="/dev")

    try:
        uvicorn.run(app, host=conf.api_host, port=conf.api_port, timeout_keep_alive=300)
    except KeyboardInterrupt:
        pass
    finally:
        pass


if __name__ == "__main__":
    main(config.AppConfig())
