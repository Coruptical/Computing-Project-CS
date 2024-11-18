import hashlib
import os
import hmac
import base64

HASH_ITERATIONS = 100_000

def new_salt():
    salt = os.urandom(16)
    return salt

def encode64(data: bytes):
    b64_bytes = base64.b64encode(data)
    return b64_bytes.decode()

def decode64(data: str):
    b64_bytes = base64.b64decode(data.encode())
    return b64_bytes

def hash_password(salt: bytes, password: str):
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, HASH_ITERATIONS)
    b64_hash = base64.b64encode(password_hash)
    return b64_hash.decode()

def check_password(salt: bytes, password_hash: str, password: str) -> bool:
    password_hash = password_hash.encode()
    password_hash = base64.b64decode(password_hash)
    password_hash_comp = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, HASH_ITERATIONS)
    return hmac.compare_digest(password_hash, password_hash_comp)