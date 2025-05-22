def make_authorization_header(mchid: str, serial_no: str, timestamp: str, nonce: str, signature: bytes) -> str:
    auth_type = "WECHATPAY2-SHA256-RSA2048"
    return f'{auth_type} mchid="{mchid}",nonce_str="{nonce}",signature="{signature}",timestamp="{timestamp}",serial_no="{serial_no}"'
