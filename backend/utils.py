import hashlib
import uuid
import math

sessions = {}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(username: str) -> str:
    token = hashlib.sha256(f"{username}_{uuid.uuid4()}".encode()).hexdigest()
    sessions[token] = username
    return token

def verify_token(authorization):
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return sessions.get(token)

def get_session_username(token: str):
    return sessions.get(token)

def remove_session(token: str):
    sessions.pop(token, None)

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"
