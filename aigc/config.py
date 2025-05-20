from pydantic_settings import BaseSettings

class Config(BaseSettings):
    api_host: str = "127.0.0.1"
    api_port: int = 8090

