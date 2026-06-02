from supabase import AsyncClient, acreate_client

from app.core.config import settings

_supabase_admin_client: AsyncClient | None = None


async def get_supabase_client() -> AsyncClient:
    return await acreate_client(settings.supabase_url, settings.supabase_anon_key)


async def get_supabase_admin_client() -> AsyncClient:
    global _supabase_admin_client

    if _supabase_admin_client is None:
        if not settings.supabase_secret_key:
            raise RuntimeError("SUPABASE_SECRET_KEY is not configured.")
        _supabase_admin_client = await acreate_client(
            settings.supabase_url,
            settings.supabase_secret_key,
        )
    return _supabase_admin_client
