import redis.asyncio
import uvicorn
from aigc import config, api, infer_dispatch, refresh_subscriptions, mainpage_config
from argparse import ArgumentParser
import redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel, create_engine
from loguru import logger
from threading import Thread


def main(configpath: str, inference_dispatch: bool = False, dev: bool = False) -> None:

    # Load config.
    config.set_config_file_path(configpath)
    conf = config.get_config()

    # Setup redis client.
    async_rdb = redis.asyncio.Redis(
        host=conf.redis.host,
        port=conf.redis.port,
        db=conf.redis.db,
        decode_responses=True,
    )

    # Setup database client.
    db = create_engine(conf.database.url)
    SQLModel.metadata.create_all(db)

    # start refresh subscription.
    refresh_thread = Thread(
        target=refresh_subscriptions.arrage_refresh_subscriptions,
        args=(db,),
        daemon=True,
    )
    refresh_thread.start()

    # if inference dispatcher needed, start dispatch server.
    if inference_dispatch:
        logger.info("with inference dispatch with process")
        rdb = redis.Redis(
            host=conf.redis.host,
            port=conf.redis.port,
            db=conf.redis.db,
            decode_responses=True,
        )
        srv = infer_dispatch.Server(rdb, db)
        dispatch_thread = Thread(target=srv.serve_forever, daemon=True)
        dispatch_thread.start()

    # mainpage remote config sync.
    conf_sync = mainpage_config.MainPageRemoteConfig(conf.redis, conf.remote_config)
    conf_sync.refresh_banner()
    conf_sync.refresh_magic()

    # Use app lifespan function to cleanup resource after shutdown.
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.conf_sync = conf_sync
        app.state.db = db
        app.state.rdb = async_rdb
        yield
        await async_rdb.aclose()

    app = FastAPI(lifespan=lifespan)

    if dev:
        logger.info("develop mode")
        app.include_router(api.router, prefix="/aigc")
        app.include_router(api.dev.router, prefix="/dev")
    else:
        app.include_router(api.router)

    try:
        uvicorn.run(app, host=conf.web.host, port=conf.web.port, timeout_keep_alive=300)
    except KeyboardInterrupt:
        pass
    finally:
        pass


if __name__ == "__main__":

    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument("--config", help="The config file path.", default="config.toml")
    parser.add_argument(
        "--with-inference-dispatch",
        help="Run infernece dispatcher in a thread within main process",
        action="store_true",
        dest="with_dispatcher",
    )
    parser.add_argument(
        "--dev", help="Run in develop mode.", action="store_true", dest="dev"
    )
    arguments = parser.parse_args()

    logger.add("api.log", rotation="100 MB")
    logger.info(f"config file path: {arguments.config}")

    main(
        configpath=arguments.config,
        inference_dispatch=arguments.with_dispatcher,
        dev=arguments.dev,
    )
