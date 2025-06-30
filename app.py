import uvicorn
from aigc import config, models, deps, bg_tasks
from argparse import ArgumentParser
import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import Session
from loguru import logger

from aigc.router import router


def main() -> None:
    logger.add("api.log", rotation="100 MB")

    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument("--config", help="The config file path.", default="config.toml")
    arguments = parser.parse_args()

    # Load default config, default can overwrite by env variables.
    config.setup_config_file(arguments.config)
    conf = config.Config()

    # Make app lifespan manager.
    @asynccontextmanager
    async def app_lifespan(app: FastAPI):
        deps.set_wx_client_deps(app, conf.wechat.secrets)

        engine = models.initialize_database_io(conf.database.file)
        deps.set_db_session_deps(app, engine)

        conn_pool = redis.ConnectionPool(
            host=conf.redis.host,
            port=conf.redis.port,
            db=conf.redis.db,
            decode_responses=True,
        )
        rdb = redis.Redis(connection_pool=conn_pool)
        deps.set_rdb_deps(app, rdb)

        dbses = Session(engine)
        refresh_task = bg_tasks.arrage_refresh_subscriptions(dbses)

        yield

        refresh_task.cancel()
        await refresh_task
        dbses.close()

        await conn_pool.aclose()

    app = FastAPI(lifespan=app_lifespan)
    app.include_router(router)

    try:
        uvicorn.run(app, host=conf.web.host, port=conf.web.port, timeout_keep_alive=300)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
