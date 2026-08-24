from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status

from app.auth.models import User
from app.auth.ratelimit import LoginRateLimiter
from app.auth.service import AuthService
from app.core.deps import RedisDep, SessionDep
from app.core.security import read_token

ACCESS_TOKEN_COOKIE = "trendscout_access"


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_login_rate_limiter(redis: RedisDep) -> LoginRateLimiter:
    return LoginRateLimiter(redis)


LoginRateLimiterDep = Annotated[LoginRateLimiter, Depends(get_login_rate_limiter)]


async def get_current_user(
    auth: AuthServiceDep,
    access_token: Annotated[str | None, Cookie(alias=ACCESS_TOKEN_COOKIE)] = None,
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
    )
    if access_token is None:
        raise credentials_error

    username = read_token(access_token)
    if username is None:
        raise credentials_error

    user = await auth.get_by_username(username)
    if user is None:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
