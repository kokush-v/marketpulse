from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.watchlists.schemas import (
    AddWatchlistAssetRequest,
    WatchlistAssetContextResponse,
    WatchlistAssetResponse,
    WatchlistAssetSearchResponse,
    WatchlistErrorResponse,
    WatchlistOperationResponse,
    WatchlistResponse,
)
from app.features.watchlists.service import WatchlistService, WatchlistServiceError

router = APIRouter(prefix="/watchlists", tags=["watchlists"])
current_user_dependency = Depends(get_current_user)


def _service_error_response(error: WatchlistServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=WatchlistErrorResponse(message=error.message).model_dump(),
    )


@router.get(
    "/starred",
    response_model=WatchlistResponse,
    summary="Get the authenticated user's starred watchlist",
)
async def get_starred_watchlist(
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[WatchlistService, Depends()],
) -> WatchlistResponse:
    try:
        return await service.get_watchlist(current_user)
    except WatchlistServiceError as error:
        return _service_error_response(error)


@router.get(
    "/assets/search",
    response_model=WatchlistAssetSearchResponse,
    summary="Search assets available for the starred watchlist",
)
async def search_watchlist_assets(
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[WatchlistService, Depends()],
    query: Annotated[str, Query(alias="q", min_length=1)],
) -> WatchlistAssetSearchResponse:
    _ = current_user
    try:
        return await service.search_assets(query)
    except WatchlistServiceError as error:
        return _service_error_response(error)


@router.post(
    "/starred/assets",
    response_model=WatchlistAssetResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": WatchlistErrorResponse, "description": "Duplicate saved asset"}},
    summary="Add an asset to the starred watchlist",
)
async def add_starred_watchlist_asset(
    payload: AddWatchlistAssetRequest,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[WatchlistService, Depends()],
) -> WatchlistAssetResponse:
    try:
        return await service.add_asset(current_user, payload)
    except WatchlistServiceError as error:
        return _service_error_response(error)


@router.delete(
    "/starred/assets/{asset_id}",
    response_model=WatchlistOperationResponse,
    responses={404: {"model": WatchlistErrorResponse, "description": "Saved asset not found"}},
    summary="Remove an asset from the starred watchlist",
)
async def remove_starred_watchlist_asset(
    asset_id: str,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[WatchlistService, Depends()],
) -> WatchlistOperationResponse:
    try:
        return await service.remove_asset(current_user, asset_id)
    except WatchlistServiceError as error:
        return _service_error_response(error)


@router.get(
    "/starred/assets/{asset_id}/context",
    response_model=WatchlistAssetContextResponse,
    responses={
        404: {
            "model": WatchlistErrorResponse,
            "description": "Saved asset or context not found",
        }
    },
    summary="Get selected asset context for the starred watchlist",
)
async def get_starred_watchlist_asset_context(
    asset_id: str,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[WatchlistService, Depends()],
) -> WatchlistAssetContextResponse:
    try:
        return await service.get_asset_context(current_user, asset_id)
    except WatchlistServiceError as error:
        return _service_error_response(error)
