from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Random import random
import base64

NONCE_DEFAULT_LEN = 16


# Ganerate the signature of data with SHA256 RSA encrypted using private key.
def sha256_with_rsa_sign(rsa_key: str | bytes, data: bytes) -> bytes:
    pubkey = RSA.importKey(rsa_key)
    signer = PKCS1_v1_5.new(pubkey)
    digest = SHA256.new()

    digest.update(data)
    sign = signer.sign(digest)

    return base64.b64encode(sign)


# Verify the signature of data with SHA256 RSA encrypted using public key.
# Input signature should be a base64 encoded bytes.
def sha256_with_rsa_verify(
    pub_key: str | bytes, signature: bytes, data: str | bytes
) -> bool:
    try:
        public_key = RSA.import_key(pub_key)

        if isinstance(data, str):
            data = data.encode()

        data_hash = SHA256.new(data)
        signature = base64.b64decode(signature)

        verifier = PKCS1_v1_5.new(public_key)
        verifier.verify(data_hash, signature)
        return True

    except (ValueError, TypeError):
        return False


def decrypt_aes_256_gcm(
    key: str, ciphertext_b64: str, nonce: str, associate: str
) -> bytes:
    cipher = AES.new(key=key.encode(), mode=AES.MODE_GCM, nonce=nonce.encode())  # type: ignore
    cipher.update(associate.encode())

    ciphertext = base64.b64decode(ciphertext_b64)
    data, tag = ciphertext[:-16], ciphertext[-16:]

    plaintext = cipher.decrypt_and_verify(data, tag)
    return plaintext


# Make a nonce string which represent a 128-bits little endian non-sign integer.
def make_nonce_str(k: int = NONCE_DEFAULT_LEN) -> str:
    bitwidth = 8
    num = random.getrandbits(bitwidth * k)  # 16 one Byte number.
    return num.to_bytes(k, byteorder="little", signed=False).hex()
