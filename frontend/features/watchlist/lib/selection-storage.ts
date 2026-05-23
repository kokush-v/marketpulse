"use client";

const WATCHLIST_SELECTED_ASSET_KEY = "mp_watchlist_selected_asset";

export function getStoredSelectedAssetId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return localStorage.getItem(WATCHLIST_SELECTED_ASSET_KEY);
}

export function setStoredSelectedAssetId(assetId: string | null): void {
  if (typeof window === "undefined") {
    return;
  }

  if (!assetId) {
    localStorage.removeItem(WATCHLIST_SELECTED_ASSET_KEY);
    return;
  }

  localStorage.setItem(WATCHLIST_SELECTED_ASSET_KEY, assetId);
}
