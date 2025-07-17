if __name__ == "__main__":
    from argparse import ArgumentParser
    from aigc import config, infer_dispatch
    from loguru import logger
    import sqlmodel
    import redis

    parser = ArgumentParser("inference dispatcher")
    parser.add_argument(
        "config", help="the path to config file.", default="config.toml"
    )
    arguments = parser.parse_args()

    logger.info(f"config file: {arguments.config}")
    config.set_config_file_path(arguments.config)
    conf = config.get_config()

    db = sqlmodel.create_engine(conf.database.url)
    rdb = redis.Redis(
        host=conf.redis.host,
        port=conf.redis.port,
        db=conf.redis.db,
        decode_responses=True,
    )

    try:
        logger.info("inference dispatcher start")
        srv = infer_dispatch.Server(rdb, db)
        srv.serve_forever()
    finally:
        rdb.close()
