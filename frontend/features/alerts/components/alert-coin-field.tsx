"use client";

import * as React from "react";
import { useDeferredValue } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Check, LoaderCircle, Plus, Search } from "lucide-react";

import type { WatchlistAssetResponse } from "@/src/api/generated/models/watchlistAssetResponse";
import type { WatchlistAssetSearchResult } from "@/src/api/generated/models/watchlistAssetSearchResult";
import {
  getGetStarredWatchlistWatchlistsStarredGetQueryKey,
  useAddStarredWatchlistAssetWatchlistsStarredAssetsPost,
  useSearchWatchlistAssetsWatchlistsAssetsSearchGet,
} from "@/src/api/generated/watchlists/watchlists";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { cn } from "@/shared/lib/utils";

export function AlertCoinField({
  assets,
  selectedAssetId,
  onSelect,
  onError,
}: {
  assets: WatchlistAssetResponse[];
  selectedAssetId: string | null;
  onSelect: (assetId: string) => void;
  onError: (message: string) => void;
}) {
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const deferredQuery = useDeferredValue(searchQuery.trim());

  const searchResults = useSearchWatchlistAssetsWatchlistsAssetsSearchGet(
    { q: deferredQuery || "btc" },
    { query: { enabled: isAdding && deferredQuery.length > 0, staleTime: 30_000, retry: 1 } },
  );
  const addAssetMutation = useAddStarredWatchlistAssetWatchlistsStarredAssetsPost();

  const handleAdd = async (asset: WatchlistAssetSearchResult) => {
    try {
      await addAssetMutation.mutateAsync({
        data: {
          asset_id: asset.asset_id,
          symbol: asset.symbol,
          name: asset.name,
          image_url: asset.image_url,
        },
      });
      await queryClient.invalidateQueries({ queryKey: getGetStarredWatchlistWatchlistsStarredGetQueryKey() });
      setSearchQuery("");
      setIsAdding(false);
      onSelect(asset.asset_id);
    } catch (error) {
      onError(error instanceof Error ? error.message : "Unable to add this coin right now.");
    }
  };

  return (
    <div className="space-y-3">
      {assets.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border/50 px-3 py-3 text-sm text-muted-foreground">
          Your watchlist is empty. Add a coin to create an alert for it.
        </p>
      ) : (
        <div className="flex flex-wrap gap-2" role="group" aria-label="Coin">
          {assets.map((asset) => {
            const isSelected = asset.asset_id === selectedAssetId;
            return (
              <button
                key={asset.asset_id}
                type="button"
                aria-pressed={isSelected}
                onClick={() => onSelect(asset.asset_id)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium transition-colors",
                  isSelected
                    ? "border-sky-500/60 bg-sky-500/15 text-sky-300"
                    : "border-border/40 text-muted-foreground hover:border-sky-500/30 hover:text-foreground",
                )}
              >
                {isSelected ? <Check className="size-3.5" /> : null}
                {asset.symbol}
              </button>
            );
          })}
        </div>
      )}

      {isAdding ? (
        <div className="space-y-2 rounded-lg border border-border/40 p-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              autoFocus
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search BTC, ETH, Solana..."
              aria-label="Search coins to add"
              className="h-9 rounded-md pl-9"
            />
          </div>
          <div className="max-h-48 space-y-1 overflow-y-auto">
            {deferredQuery.length === 0 ? (
              <p className="px-1 py-2 text-xs text-muted-foreground">Type a coin name or symbol.</p>
            ) : searchResults.isLoading ? (
              <p className="flex items-center gap-2 px-1 py-2 text-xs text-muted-foreground">
                <LoaderCircle className="size-3.5 animate-spin" /> Searching…
              </p>
            ) : searchResults.isError ? (
              <p className="px-1 py-2 text-xs text-destructive">Search is unavailable right now.</p>
            ) : searchResults.data?.items.length ? (
              searchResults.data.items.map((asset) => {
                const alreadySaved = assets.some((item) => item.asset_id === asset.asset_id);
                return (
                  <div key={asset.asset_id} className="flex items-center justify-between gap-3 rounded-md px-2 py-1.5">
                    <p className="min-w-0 truncate text-sm">
                      <span className="font-semibold">{asset.symbol}</span>{" "}
                      <span className="text-muted-foreground">{asset.name}</span>
                    </p>
                    {alreadySaved ? (
                      <Button type="button" variant="outline" size="sm" onClick={() => onSelect(asset.asset_id)}>
                        Select
                      </Button>
                    ) : (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={addAssetMutation.isPending}
                        onClick={() => void handleAdd(asset)}
                      >
                        <Plus className="size-4" />
                        Add
                      </Button>
                    )}
                  </div>
                );
              })
            ) : (
              <p className="px-1 py-2 text-xs text-muted-foreground">No coins matched this search.</p>
            )}
          </div>
        </div>
      ) : (
        <Button type="button" variant="ghost" size="sm" className="gap-1.5 px-2" onClick={() => setIsAdding(true)}>
          <Plus className="size-4" />
          Add another coin
        </Button>
      )}
    </div>
  );
}
