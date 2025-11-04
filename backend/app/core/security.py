from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from .config import settings

# Password hashing context using Argon2 (more secure than bcrypt)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Initialize Fernet cipher for OAuth token encryption
def get_fernet() -> Fernet:
    """Get Fernet cipher instance for encrypting OAuth tokens."""
    # Ensure the key is properly formatted (32 url-safe base64-encoded bytes)
    key = settings.ENCRYPTION_KEY.encode()
    return Fernet(key)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for secure storage."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token (short-lived)."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token (long-lived)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token_type(payload: dict, expected_type: str) -> bool:
    """Verify that the token is of the expected type (access or refresh)."""
    return payload.get("type") == expected_type


def encrypt_token(token: str) -> bytes:
    """Encrypt an OAuth token for secure storage in the database."""
    fernet = get_fernet()
    return fernet.encrypt(token.encode())


def decrypt_token(encrypted_token: bytes) -> str:
    """Decrypt an OAuth token from the database."""
    fernet = get_fernet()
    return fernet.decrypt(encrypted_token).decode()
