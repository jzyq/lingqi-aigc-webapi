from pydantic_settings import BaseSettings


class Config(BaseSettings):
    api_host: str = "127.0.0.1"
    api_port: int = 8090

    database_file: str = "database.db"

    secrets: str = "secrets/secrets"
    apiclient_key: str = "secrets/apiclient_key.pem"
    pub_key: str = "secrets/pub_key.pem"
