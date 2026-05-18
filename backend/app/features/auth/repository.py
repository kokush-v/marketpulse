import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_supabase_id(self, supabase_user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.supabase_user_id == supabase_user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, supabase_user_id: uuid.UUID, email: str) -> User:
        user = User(supabase_user_id=supabase_user_id, email=email.lower())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user_email(self, user: User, email: str) -> User:
        user.email = email.lower()
        await self.session.commit()
        await self.session.refresh(user)
        return user
