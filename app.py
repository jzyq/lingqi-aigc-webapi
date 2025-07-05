import uvicorn
from aigc import config, deps, bg_tasks
from argparse import ArgumentParser
import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import Session
from loguru import logger

from aigc.router import router


# Make app lifespan manager.
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    conf = config.get_config()

    # Setup redis connection.
    conn_pool = redis.ConnectionPool(
        host=conf.redis.host,
        port=conf.redis.port,
        db=conf.redis.db,
        decode_responses=True,
    )
    rdb = redis.Redis(connection_pool=conn_pool)
    deps.set_rdb_deps(app, rdb)

    # Setup subscription manage task.
    # TODO: if reload config, database file may changed so must reload this task.
    dbses = Session(deps.get_db_engine(conf.database.file))
    refresh_task = bg_tasks.arrage_refresh_subscriptions(dbses)

    yield

    refresh_task.cancel()
    await refresh_task
    dbses.close()

    await conn_pool.aclose()


def main() -> None:
    logger.add("api.log", rotation="100 MB")

    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument("--config", help="The config file path.", default="config.toml")
    arguments = parser.parse_args()

    # Load default config, default can overwrite by env variables.
    logger.info(f"config file path: {arguments.config}")
    config.set_config_file_path(arguments.config)

    app = FastAPI(lifespan=app_lifespan)
    app.include_router(router)

    try:
        conf = config.get_config()
        uvicorn.run(app, host=conf.web.host, port=conf.web.port, timeout_keep_alive=300)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
