import uuid

from sqlalchemy import insert, select, update
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
        stmt = (
            insert(User)
            .values(supabase_user_id=supabase_user_id, email=email.lower())
            .returning(User)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def update_user_email(self, user: User, email: str) -> User:
        stmt = update(User).where(User.id == user.id).values(email=email.lower()).returning(User)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
