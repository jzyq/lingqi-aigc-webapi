from pydantic import BaseModel
from enum import IntEnum


class PayAmount(BaseModel):
    total: int  # 总金额
    currency: str = "CNY"  # 货币类型


class Order(BaseModel):
    # 商品描述，商品描述信息，用户微信账单的商品字段中可见，
    # 商户需传递能真实代表商品信息的描述，不能超过127个字符
    description: str

    # 商户订单号，商户系统内部订单号，要求6-32个字符内，只能是数字、大小写字母_-|* 且在同一个商户号下唯一
    out_trade_no: str

    # 回调地质
    notify_url: str

    # 金额
    amount: PayAmount

    # 可选，支付结束时间，格式为rfc3339
    time_expire: str | None = None

    # 商户数据包，对用户不可见，wx回调时回传给商户，128个字符以内
    attach: str | None = None


class AccessToken(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str
    openid: str
    scope: str
    unionid: str


class UserSex(IntEnum):
    unknown = 0
    male = 1
    female = 2


class UserInfo(BaseModel):
    openid: str
    nickname: str
    sex: UserSex
    province: str
    city: str
    country: str
    headimgurl: str
    privilege: list[str]
    unionid: str
