from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.audit import audit_event
from app.core.config import settings
from app.core.security import create_access_token, create_csrf_token, hash_password, verify_password
from app.db.session import get_db
from app.middleware.auth import AUTH_COOKIE_NAME
from app.middleware.csrf import CSRF_COOKIE_NAME
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserRead

router = APIRouter(tags=["auth"])


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=create_csrf_token(),
        httponly=False,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    email = payload.email.lower()
    existing_user = db.scalar(select(User).where(User.email == email))

    if existing_user is not None:
        audit_event(event="auth.register", request=request, outcome="duplicate", email=email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    set_auth_cookie(response, create_access_token(str(user.id)))
    audit_event(event="auth.register", request=request, user_id=user.id)
    return AuthResponse(user=UserRead.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    email = payload.email.lower()
    user = db.scalar(select(User).where(User.email == email))

    if user is None or not verify_password(payload.password, user.hashed_password):
        audit_event(event="auth.login", request=request, outcome="failed", email=email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        audit_event(event="auth.login", request=request, user_id=user.id, outcome="disabled")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is disabled.",
        )

    set_auth_cookie(response, create_access_token(str(user.id)))
    audit_event(event="auth.login", request=request, user_id=user.id)
    return AuthResponse(user=UserRead.model_validate(user))


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")
    user_id = getattr(request.state, "user_id", None)
    audit_event(event="auth.logout", request=request, user_id=user_id)
    return {"status": "ok"}


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
