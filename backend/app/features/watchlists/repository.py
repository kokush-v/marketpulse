import uuid

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.watchlists.models import WatchlistAsset


class WatchlistAssetAlreadySavedError(Exception):
    """Raised when a concurrent insert hits the watchlist uniqueness constraint."""


class WatchlistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_assets_for_user(self, user_id: uuid.UUID) -> list[WatchlistAsset]:
        stmt = (
            select(WatchlistAsset)
            .where(WatchlistAsset.user_id == user_id)
            .order_by(WatchlistAsset.created_at.asc(), WatchlistAsset.name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_asset_for_user(self, user_id: uuid.UUID, asset_id: str) -> WatchlistAsset | None:
        stmt = select(WatchlistAsset).where(
            WatchlistAsset.user_id == user_id,
            WatchlistAsset.asset_id == asset_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_asset_for_user(
        self,
        user_id: uuid.UUID,
        asset_id: str,
        symbol: str,
        name: str,
        image_url: str | None,
    ) -> WatchlistAsset:
        stmt = (
            insert(WatchlistAsset)
            .values(
                user_id=user_id,
                asset_id=asset_id,
                symbol=symbol,
                name=name,
                image_url=image_url,
            )
            .returning(WatchlistAsset)
        )
        try:
            result = await self.session.execute(stmt)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise WatchlistAssetAlreadySavedError from exc
        return result.scalar_one()

    async def delete_asset_for_user(self, user_id: uuid.UUID, asset_id: str) -> bool:
        stmt = delete(WatchlistAsset).where(
            WatchlistAsset.user_id == user_id,
            WatchlistAsset.asset_id == asset_id,
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return bool(result.rowcount)
