import redis.asyncio as asyncredis
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel, create_engine
from loguru import logger
from threading import Thread
from service import (
    config,
    api,
    infer_dispatch,
    refresh_subscriptions,
    mainpage_config,
    depends,
)
import persistence
import models
from pymongo import AsyncMongoClient
import inference_dispatcher
import asyncio
import admin
import ossapp
import oss
import dataio
import rpcclient
import wxproxy
import oplog


async def main(conf: config.AppConfig) -> None:

    # Setup redis client.
    async_rdb = asyncredis.Redis(
        host=conf.redis_host,
        port=conf.redis_port,
        db=conf.redis_db,
        decode_responses=True,
    )

    async_redis_conn_pool = asyncredis.ConnectionPool(
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

    client = AsyncMongoClient(conf.mongodb_url)
    await persistence.init_presistence(client)
    await models.init(client.aigc)
    await oss.init(client.aigc)
    await dataio.init(conf.mongodb_url)
    await oplog.init(conf.mongodb_url)
    await rpcclient.init("http://127.0.0.1:8090", rpcclient.Prefix())

    # Use app lifespan function to cleanup resource after shutdown.
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.db = db
        app.state.rdb = async_rdb

        disp = inference_dispatcher.Dispatcher()
        task = asyncio.create_task(disp.serve_forever())

        depends.Initlization.set_async_redis_connection_pool(app, async_redis_conn_pool)

        try:
            yield
        finally:
            await async_rdb.aclose()
            await async_redis_conn_pool.aclose()

            try:
                task.cancel()
                await task
            except asyncio.CancelledError:
                pass

    if conf.refresh_mainpage:
        rc = mainpage_config.RemoteConfig(
            app_id="cli_a8f212a1f91c501c",
            secret="KSRIFs0wipqk4zTv6LBVZd0xPyxjHs3E",
            bitable_id="UrycwJ6bQiWmEqkyU74cSh01nNh",
        )
        mrc = mainpage_config.MainPageRemoteConfig(rc)
        await mrc.refresh_banner()
        await mrc.refresh_magic()
        await mrc.refresh_shortcut()

    app = FastAPI(lifespan=lifespan)
    app.include_router(api.router)
    app.mount("/admin/api", admin.webapp)
    app.mount("/oss", ossapp.make_app(ossapp.Config()))
    app.mount("/wechat", wxproxy.make_app())

    if conf.mode == "dev":
        logger.info("develop mode")
        app.include_router(api.dev.router, prefix="/dev")

    srv_conf = uvicorn.Config(
        app, host=conf.api_host, port=conf.api_port, timeout_keep_alive=300
    )
    srv = uvicorn.Server(srv_conf)
    await srv.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main(config.AppConfig()))
    except KeyboardInterrupt:
        pass
