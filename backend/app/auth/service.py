from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.security import hash_password, verify_password


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def authenticate(self, username: str, password: str) -> User | None:
        user = await self.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def ensure_user(self, username: str, password: str) -> User:
        """Idempotent seed of the panel account — runs on every startup."""
        existing = await self.get_by_username(username)
        if existing is not None:
            return existing
        user = User(username=username, password_hash=hash_password(password))
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user
