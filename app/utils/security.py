import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Union

# JWT Configuration
SECRET_KEY = "kimbo_ai_super_secret_key_change_me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 Days

def get_password_hash(password: str):
    # Password ko bytes mein badlein
    pwd_bytes = password.encode('utf-8')
    # Salt generate karein aur hash banayein
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    # Wapas string mein badal kar return karein
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    # Dono ko bytes mein badal kar check karein
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# app/utils/security.py में जोड़ें:
def decode_access_token(token: str) -> dict:
    try:
        # Token को secret key और algorithm से decode करें
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        # Agar token invalid ya expire hai toh None return karein
        return None
