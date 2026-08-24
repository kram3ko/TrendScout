from fastapi import APIRouter, HTTPException, Response, status

from app.auth.deps import (
    ACCESS_TOKEN_COOKIE,
    AuthServiceDep,
    CurrentUser,
    LoginRateLimiterDep,
)
from app.auth.schemas import LoginRequest, UserRead
from app.core.config import get_settings
from app.core.security import issue_token

SECONDS_PER_MINUTE = 60

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserRead)
async def login(
    payload: LoginRequest,
    response: Response,
    auth: AuthServiceDep,
    limiter: LoginRateLimiterDep,
) -> UserRead:
    if await limiter.is_blocked(payload.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts, try again later",
        )

    user = await auth.authenticate(payload.username, payload.password)
    if user is None:
        await limiter.register_attempt(payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )

    await limiter.reset(payload.username)
    settings = get_settings()
    response.set_cookie(
        ACCESS_TOKEN_COOKIE,
        issue_token(user.username),
        max_age=settings.access_token_ttl_minutes * SECONDS_PER_MINUTE,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    return UserRead.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(ACCESS_TOKEN_COOKIE, httponly=True, samesite="lax")


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
