import os
from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from pydantic import BaseModel
from typing import Optional

from backend.app.core.config import settings
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    oauth2_scheme,
    User,
)
from src.database.user_repository import (
    count_admins,
    create_user,
    get_user_by_username,
    list_users as repo_list_users,
    update_user_password,
)

router = APIRouter()
DB_PATH = str(settings.DB_PATH)


def bootstrap_admin_from_env(db_path: str = DB_PATH) -> None:
    """Optionally bootstraps the first admin if BOOTSTRAP_ADMIN_PASSWORD is set and no admin exists."""
    bootstrap_pw = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    if not bootstrap_pw:
        return
    if count_admins(db_path=db_path) > 0:
        return
    username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin")
    email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@smartsched.edu")
    full_name = os.getenv("BOOTSTRAP_ADMIN_NAME", "University Timetable Administrator")
    create_user(
        username=username,
        full_name=full_name,
        email=email,
        hashed_password=get_password_hash(bootstrap_pw),
        role="admin",
        db_path=db_path,
    )


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


class UserCreatePayload(BaseModel):
    username: str
    full_name: str
    email: str
    password: str
    role: str = "viewer"


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

    user_dict = get_user_by_username(token_data.username, db_path=str(settings.DB_PATH))
    if user_dict is None or user_dict.get("disabled"):
        raise credentials_exception

    return User(
        username=user_dict["username"],
        email=user_dict["email"],
        full_name=user_dict["full_name"],
        role=user_dict["role"],
        disabled=bool(user_dict["disabled"]),
    )


# Dependency for Administrator role only
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to perform this action.",
        )
    return current_user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginPayload, response: Response):
    user = get_user_by_username(payload.username, db_path=str(settings.DB_PATH))
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if user.get("disabled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is disabled")

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

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
        "full_name": user["full_name"],
    }


@router.post("/logout")
def logout(response: Response):
    is_prod = settings.ENVIRONMENT == "production"
    response.delete_cookie(
        key="smartsched_auth_token",
        httponly=True,
        samesite="none" if is_prod else "lax",
        secure=is_prod,
    )
    return {"status": "logged_out", "message": "Session invalidated successfully"}


@router.get("/me", response_model=User)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(payload: PasswordChangePayload, current_user: User = Depends(get_current_user)):
    db_path = str(settings.DB_PATH)
    user = get_user_by_username(current_user.username, db_path=db_path)
    if not user or not verify_password(payload.old_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password incorrect")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    update_user_password(current_user.username, get_password_hash(payload.new_password), db_path=db_path)
    return {"status": "success", "message": "Password changed successfully"}


@router.get("/users", dependencies=[Depends(require_admin)])
def list_users():
    return repo_list_users(db_path=str(settings.DB_PATH))


@router.post("/users", dependencies=[Depends(require_admin)])
def create_account(payload: UserCreatePayload):
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    ok, msg = create_user(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        db_path=str(settings.DB_PATH),
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "username": payload.username, "role": payload.role}
