from supabase import AsyncClient, acreate_client

from app.core.config import settings


async def get_supabase_client() -> AsyncClient:
    return await acreate_client(settings.supabase_url, settings.supabase_anon_key)


async def get_supabase_admin_client() -> AsyncClient:
    if not settings.supabase_secret_key:
        raise RuntimeError("SUPABASE_SECRET_KEY is not configured.")
    return await acreate_client(
        settings.supabase_url,
        settings.supabase_secret_key,
    )
