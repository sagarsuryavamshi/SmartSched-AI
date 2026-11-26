from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    oauth2_scheme,
    User
)

router = APIRouter()

# In-memory secure user store (production ready with hashed passwords)
# Password for admin: 'Admin@SmartSched2026'
# Password for viewer: 'Viewer@SmartSched2026'
USERS_DB = {
    "admin": {
        "username": "admin",
        "full_name": "University Timetable Administrator",
        "email": "admin@smartsched.edu",
        "hashed_password": get_password_hash("Admin@SmartSched2026"),
        "role": "admin",
        "disabled": False
    },
    "viewer": {
        "username": "viewer",
        "full_name": "Academic Observer / Student",
        "email": "viewer@smartsched.edu",
        "hashed_password": get_password_hash("Viewer@SmartSched2026"),
        "role": "viewer",
        "disabled": False
    }
}

class LoginPayload(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    full_name: str

class PasswordChangePayload(BaseModel):
    old_password: str
    new_password: str

# Dependency for current active user (supports Bearer header or HttpOnly cookie)
async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    resolved_token = token or request.cookies.get("smartsched_auth_token")
    if not resolved_token:
        raise credentials_exception

    token_data = decode_access_token(resolved_token)
    if token_data is None:
        raise credentials_exception

    user_dict = USERS_DB.get(token_data.username)
    if user_dict is None or user_dict.get("disabled"):
        raise credentials_exception

    return User(
        username=user_dict["username"],
        email=user_dict["email"],
        full_name=user_dict["full_name"],
        role=user_dict["role"],
        disabled=user_dict["disabled"]
    )

# Dependency for Administrator role only
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to perform this action."
        )
    return current_user

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginPayload, response: Response):
    user = USERS_DB.get(payload.username)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    if user.get("disabled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is disabled")

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    # Set secure HttpOnly cookie for cookie-based browser architectures
    from backend.app.core.config import settings
    is_prod = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="smartsched_auth_token",
        value=access_token,
        httponly=True,
        samesite="none" if is_prod else "lax",
        secure=is_prod,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"],
        "full_name": user["full_name"]
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="smartsched_auth_token")
    return {"status": "logged_out", "message": "Session invalidated successfully"}

@router.get("/me", response_model=User)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/change-password")
def change_password(payload: PasswordChangePayload, current_user: User = Depends(get_current_user)):
    user = USERS_DB.get(current_user.username)
    if not user or not verify_password(payload.old_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password incorrect")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    user["hashed_password"] = get_password_hash(payload.new_password)
    return {"status": "success", "message": "Password changed successfully"}

@router.get("/users", dependencies=[Depends(require_admin)])
def list_users():
    return [
        {
            "username": u["username"],
            "full_name": u["full_name"],
            "email": u["email"],
            "role": u["role"],
            "disabled": u["disabled"]
        }
        for u in USERS_DB.values()
    ]
