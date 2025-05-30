from pydantic_settings import BaseSettings
from pydantic import BaseModel


class Config(BaseSettings):
    api_host: str = "127.0.0.1"
    api_port: int = 8090

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0

    database_file: str = "database.db"
    subscriptions_plan_file: str = "subscriptions.csv"

    session_ttl_s: int = 3600

    wx_qrcode_login_redirect_url: str = 'https://www.lingqi.tech/aigc/api/wx/login/callback'
    wx_payment_callback: str = "https://www.lingqi.tech/aigc/api/wx/pay/callback"

    payment_expires_in_s: int = 300

    free_subscription_magic_point: int = 3


class SubscriptionPlan(BaseModel):
    price: int
    month: int
    point_each_day: int
