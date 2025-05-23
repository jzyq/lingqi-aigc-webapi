import uvicorn
from aigc import app, config, models, wx, deps
from argparse import ArgumentParser


def main() -> None:
    # Load default config, default can overwrite by env variables.
    default_config = config.Config()

    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument(
        "secret", help="The secret file which contain senstive data like appid."
    )
    parser.add_argument("apiclient_key_file",
                        help="path to the api client key file from wx.")
    parser.add_argument("pub_key_file", help="path to the wx pub key file.")
    parser.add_argument(
        "--host", help="WEB API host address", default=default_config.api_host
    )
    parser.add_argument("--port", help="WEB API port",
                        default=default_config.api_port)
    arguments = parser.parse_args()

    # Load and parse secerts file.
    # Set it to app.
    sec = wx.must_load_secert(
        secerts=arguments.secret,
        apiclient_key=arguments.apiclient_key_file,
        pub_key=arguments.pub_key_file)
    deps.set_wx_client_deps(app.app, sec)

    # Initialize databases.
    db_file = default_config.database_file
    engine = models.initialize_database_io(db_file)
    deps.set_db_session_deps(app.app, engine)

    # Start webapi service.
    try:
        uvicorn.run(app.app, host=arguments.host, port=arguments.port)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
