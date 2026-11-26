"""Authentication and Security Utilities for SmartSched AI.

Provides:
  - Strong password hashing with bcrypt.
  - JWT creation and verification.
  - Role-based access control (Admin vs Read-only).
  - Rate-limiting helper.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from backend.app.core.config import settings

# Security settings
_DEV_FALLBACK_KEY = "smartsched-super-secure-production-secret-key-2026"
SECRET_KEY = settings.JWT_SECRET_KEY
if settings.ENVIRONMENT == "production" and (not SECRET_KEY or SECRET_KEY == _DEV_FALLBACK_KEY):
    raise RuntimeError("JWT_SECRET_KEY environment variable must be set to a secure random value in production.")
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

class TokenData(BaseModel):
    username: str
    role: str
    exp: Optional[int] = None

class User(BaseModel):
    username: str
    email: str
    full_name: str
    role: str  # "admin" or "viewer"
    disabled: bool = False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "viewer")
        if username is None:
            return None
        return TokenData(username=username, role=role, exp=payload.get("exp"))
    except JWTError:
        return None
