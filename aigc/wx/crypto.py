from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import base64

def sha256_with_rsa_b64_encode(data: bytes, rsa_key: str | bytes) -> bytes:
    pubkey = RSA.importKey(rsa_key)
    signer = PKCS1_v1_5.new(pubkey)
    digest = SHA256.new()

    digest.update(data)
    sign = signer.sign(digest)

    return base64.b64encode(sign)