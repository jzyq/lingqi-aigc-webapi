import configparser
import uvicorn
from aigc import app, config, utils, models
from argparse import ArgumentParser


def must_load_secerts_file(path: str) -> tuple[str, str]:
    secrets = configparser.ConfigParser()
    secrets.read(path)
    app_id = secrets.get("wx", "app_id", fallback="")
    app_secret = secrets.get("wx", "app_secret", fallback="")

    if app_id == "" or app_secret == "":
        print("app secrets is required. check secrtes file.")
        exit(1)

    return (app_id, app_secret)


def main() -> None:
    # Load default config, default can overwrite by env variables.
    default_config = config.Config()

    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument(
        "secret", help="The secret file which contain senstive data like appid."
    )
    parser.add_argument(
        "--host", help="WEB API host address", default=default_config.api_host
    )
    parser.add_argument("--port", help="WEB API port", default=default_config.api_port)
    arguments = parser.parse_args()

    # Load and parse secerts file.
    # Set it to app.
    (app_id, app_secret) = must_load_secerts_file(arguments.secret)
    utils.set_wx_app_id_and_secret(app.app, app_id, app_secret)

    # Initialize databases.
    db_file = default_config.database_file
    models.initialize_database_io(db_file)

    # Start webapi service.
    try:
        uvicorn.run(app.app, host=arguments.host, port=arguments.port)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
