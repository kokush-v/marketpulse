"use client";

import * as React from "react";
import Link from "next/link";
import { startTransition, useDeferredValue } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  BellPlus,
  ChartColumn,
  CircleDollarSign,
  Coins,
  ExternalLink,
  MoreHorizontal,
  Newspaper,
  RefreshCw,
  Search,
  Star,
  Trash2,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { AppSidebar } from "@/features/market-dashboard/components/app-sidebar";
import { getStoredSelectedAssetId, setStoredSelectedAssetId } from "@/features/watchlist/lib/selection-storage";
import {
  getGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGetQueryKey,
  getGetStarredWatchlistWatchlistsStarredGetQueryKey,
  useAddStarredWatchlistAssetWatchlistsStarredAssetsPost,
  useGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGet,
  useGetStarredWatchlistWatchlistsStarredGet,
  useRemoveStarredWatchlistAssetWatchlistsStarredAssetsAssetIdDelete,
  useSearchWatchlistAssetsWatchlistsAssetsSearchGet,
} from "@/src/api/generated/watchlists/watchlists";
import { Badge } from "@/shared/components/ui/badge";
import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from "@/shared/components/ui/breadcrumb";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { Input } from "@/shared/components/ui/input";
import { ScrollArea } from "@/shared/components/ui/scroll-area";
import { Separator } from "@/shared/components/ui/separator";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { Spinner } from "@/shared/components/ui/spinner";
import { SidebarInset, SidebarTrigger } from "@/shared/components/ui/sidebar";
import { cn } from "@/shared/lib/utils";

export function WatchlistWorkspace() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = React.useState("");
  const [selectedAssetId, setSelectedAssetId] = React.useState<string | null>(null);
  const [placeholderMessage, setPlaceholderMessage] = React.useState<string | null>(null);
  const deferredSearchQuery = useDeferredValue(searchQuery.trim());

  const watchlistQuery = useGetStarredWatchlistWatchlistsStarredGet(undefined, {
    query: {
      staleTime: 30_000,
      retry: 1,
    },
  });

  const searchQueryResult = useSearchWatchlistAssetsWatchlistsAssetsSearchGet(
    { q: deferredSearchQuery || "btc" },
    {
      query: {
        enabled: deferredSearchQuery.length > 0,
        staleTime: 30_000,
        retry: 1,
      },
    }
  );

  const selectedAssetContextQuery = useGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGet(
    selectedAssetId ?? "",
    undefined,
    {
      query: {
        enabled: Boolean(selectedAssetId),
        retry: 1,
      },
    }
  );

  const addAssetMutation = useAddStarredWatchlistAssetWatchlistsStarredAssetsPost();
  const removeAssetMutation = useRemoveStarredWatchlistAssetWatchlistsStarredAssetsAssetIdDelete();

  const assets = watchlistQuery.data?.assets ?? [];
  const selectedAsset = assets.find((asset) => asset.asset_id === selectedAssetId) ?? null;

  React.useEffect(() => {
    if (!watchlistQuery.data) {
      return;
    }

    if (assets.length === 0) {
      setSelectedAssetId(null);
      setStoredSelectedAssetId(null);
      return;
    }

    if (selectedAssetId && assets.some((asset) => asset.asset_id === selectedAssetId)) {
      return;
    }

    const storedAssetId = getStoredSelectedAssetId();
    const restoredAsset = storedAssetId
      ? assets.find((asset) => asset.asset_id === storedAssetId)
      : null;
    const nextSelectedAssetId = restoredAsset?.asset_id ?? assets[0]?.asset_id ?? null;

    setSelectedAssetId(nextSelectedAssetId);
    setStoredSelectedAssetId(nextSelectedAssetId);
  }, [assets, selectedAssetId, watchlistQuery.data]);

  const handleSelectAsset = (assetId: string) => {
    startTransition(() => {
      setSelectedAssetId(assetId);
      setStoredSelectedAssetId(assetId);
      setPlaceholderMessage(null);
    });
  };

  const handleAddAsset = async (asset: NonNullable<typeof searchQueryResult.data>["items"][number]) => {
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
      handleSelectAsset(asset.asset_id);
      setSearchQuery("");
    } catch (error) {
      setPlaceholderMessage(error instanceof Error ? error.message : "Unable to save asset right now.");
    }
  };

  const handleDeleteAsset = async (assetId: string) => {
    try {
      await removeAssetMutation.mutateAsync({ assetId });
      await queryClient.invalidateQueries({ queryKey: getGetStarredWatchlistWatchlistsStarredGetQueryKey() });
      await queryClient.invalidateQueries({
        queryKey: getGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGetQueryKey(assetId),
      });

      if (selectedAssetId === assetId) {
        setSelectedAssetId(null);
        setStoredSelectedAssetId(null);
      }

      setPlaceholderMessage(null);
    } catch (error) {
      setPlaceholderMessage(error instanceof Error ? error.message : "Unable to remove asset right now.");
    }
  };

  const handleAddAlertPlaceholder = (assetName: string) => {
    setPlaceholderMessage(`Add alert for ${assetName} is not available yet.`);
  };

  return (
    <>
      <AppSidebar />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b border-border/40 bg-background/95 backdrop-blur-sm">
          <div className="flex w-full items-center gap-3 px-4 lg:px-6">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="h-6 bg-border" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbPage className="text-sm font-semibold">Watchlist</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
            <Badge variant="outline" className="hidden border-emerald-500/20 text-emerald-700 md:inline-flex">
              Protected workspace
            </Badge>
            <div className="ml-auto flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                className="h-9 w-9 p-0"
                onClick={() => void watchlistQuery.refetch()}
                disabled={watchlistQuery.isFetching}
              >
                <RefreshCw className={cn("size-4", watchlistQuery.isFetching && "animate-spin")} />
              </Button>
            </div>
          </div>
        </header>

        <div className="@container/main flex flex-1 flex-col bg-gradient-to-b from-background via-background to-background/80">
          <div className="flex flex-1 flex-col gap-4 px-4 py-4 lg:px-6 md:gap-6 md:py-6">
            <section className="grid flex-1 items-stretch gap-4 xl:min-h-[calc(100vh-7.5rem)] xl:grid-cols-[360px_minmax(0,1fr)]">
              <Card className="flex h-full min-h-[520px] flex-col border-border/30 bg-card/60 backdrop-blur-sm xl:min-h-[calc(100vh-7.5rem)]">
                <CardHeader className="gap-5 pb-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <CardTitle className="flex items-center gap-3">
                        <span className="flex size-9 items-center justify-center rounded-full border border-amber-500/25 bg-amber-500/10 text-amber-500">
                          <CircleDollarSign className="size-4" />
                        </span>
                        Your saved coins
                      </CardTitle>
                      <CardDescription className="mt-2 max-w-[26ch] leading-6">
                        Save a few key assets and open one focused market brief at a time.
                      </CardDescription>
                    </div>
                    <Badge
                      variant="secondary"
                      className="min-w-16 justify-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold tracking-[0.02em] text-foreground/85"
                    >
                      <Coins className="size-3.5 text-amber-500" />
                      {assets.length}
                    </Badge>
                  </div>
                  <div className="relative">
                    <Search className="pointer-events-none absolute left-3 top-3.5 size-4 text-muted-foreground" />
                    <Input
                      value={searchQuery}
                      onChange={(event) => setSearchQuery(event.target.value)}
                      placeholder="Search BTC, ETH, Bitcoin..."
                      className="pl-10"
                    />
                    {deferredSearchQuery.length > 0 && (
                      <Card className="absolute left-0 right-0 top-[calc(100%+0.5rem)] z-20 border-border/50 bg-background/95 shadow-xl">
                        <CardContent className="p-2">
                          {searchQueryResult.isLoading ? (
                            <div className="flex items-center gap-2 px-3 py-3 text-sm text-muted-foreground">
                              <Spinner className="size-4" />
                              Looking through the market snapshot...
                            </div>
                          ) : searchQueryResult.isError ? (
                            <div className="px-3 py-3 text-sm text-destructive">
                              {searchQueryResult.error instanceof Error
                                ? searchQueryResult.error.message
                                : "Search is unavailable right now."}
                            </div>
                          ) : searchQueryResult.data?.items.length ? (
                            <div className="space-y-1">
                              {searchQueryResult.data.items.map((asset) => (
                                (() => {
                                  const isSaved = assets.some(
                                    (savedAsset) => savedAsset.asset_id === asset.asset_id
                                  );

                                  return (
                                <div
                                  key={asset.asset_id}
                                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-accent"
                                  onClick={() => {
                                    if (isSaved) {
                                      handleSelectAsset(asset.asset_id);
                                      return;
                                    }

                                    void handleAddAsset(asset);
                                  }}
                                >
                                  <AssetAvatar symbol={asset.symbol} imageUrl={asset.image_url} />
                                  <div className="min-w-0 flex-1">
                                    <div className="flex items-center gap-2">
                                      <span className="truncate font-medium">{asset.name}</span>
                                      <Badge variant="outline" className="text-[10px]">
                                        #{asset.market_cap_rank}
                                      </Badge>
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                      {asset.symbol} · ${formatCompactCurrency(asset.current_price)}
                                    </p>
                                  </div>
                                  <div className="flex size-8 items-center justify-center rounded-full text-amber-500">
                                    <Star
                                      className="size-4"
                                      fill={isSaved ? "currentColor" : "none"}
                                      strokeWidth={1.9}
                                    />
                                  </div>
                                </div>
                                  );
                                })()
                              ))}
                            </div>
                          ) : (
                            <div className="px-3 py-3 text-sm text-muted-foreground">
                              No matching assets in the current market snapshot.
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="flex flex-1 px-0 pb-0 pt-1">
                  {watchlistQuery.isLoading ? (
                    <WatchlistListLoading />
                  ) : watchlistQuery.isError ? (
                    <EmptyPanel
                      compact
                      className="h-full w-full"
                      title="Your watchlist is taking a moment"
                      description={
                        watchlistQuery.error instanceof Error
                          ? "We couldn’t reach your saved assets just now. Try refreshing in a moment."
                          : "We couldn’t reach your saved assets just now. Try refreshing in a moment."
                      }
                    />
                  ) : assets.length === 0 ? (
                    <EmptyPanel
                      compact
                      className="h-full w-full"
                      title="Start with your first coin"
                      description="Use search above to save an asset, then the chart, market snapshot, and related stories will appear automatically."
                    />
                  ) : (
                    <ScrollArea className="h-full w-full">
                      <div className="space-y-2.5 px-4 pb-4 pt-3">
                        {assets.map((asset) => {
                          const isSelected = asset.asset_id === selectedAssetId;
                          const isDeleting = removeAssetMutation.isPending && removeAssetMutation.variables?.assetId === asset.asset_id;

                          return (
                            <div
                              key={asset.id}
                              role="button"
                              tabIndex={0}
                              onClick={() => handleSelectAsset(asset.asset_id)}
                              onKeyDown={(event) => {
                                if (event.key === "Enter" || event.key === " ") {
                                  event.preventDefault();
                                  handleSelectAsset(asset.asset_id);
                                }
                              }}
                              className={cn(
                                "group flex w-full items-center gap-4 rounded-2xl border px-4 py-3.5 text-left transition-colors",
                                isSelected
                                  ? "border-emerald-500/40 bg-emerald-500/10"
                                  : "border-border/40 bg-background/70 hover:bg-accent"
                              )}
                            >
                              <AssetAvatar symbol={asset.symbol} imageUrl={asset.image_url ?? undefined} />
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-2">
                                  <span className="truncate font-medium">{asset.name}</span>
                                  <Badge variant="outline" className="text-[10px]">
                                    {asset.symbol}
                                  </Badge>
                                </div>
                                <p className="mt-0.5 text-xs text-muted-foreground">
                                  Saved {new Date(asset.created_at).toLocaleDateString()}
                                </p>
                              </div>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="size-8 rounded-full"
                                    onClick={(event) => event.stopPropagation()}
                                  >
                                    {isDeleting ? <Spinner className="size-4" /> : <MoreHorizontal className="size-4" />}
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent
                                  align="end"
                                  className="w-44 rounded-xl border-border/30 bg-background/95 p-1.5 shadow-2xl backdrop-blur-md"
                                >
                                  <DropdownMenuItem onClick={() => handleAddAlertPlaceholder(asset.name)}>
                                    <BellPlus className="size-4" />
                                    Add alert
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() => void handleDeleteAsset(asset.asset_id)}
                                    className="text-destructive focus:text-destructive"
                                  >
                                    <Trash2 className="size-4" />
                                    Delete
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                          );
                        })}
                      </div>
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>

              <div className="flex min-h-[520px] flex-col gap-4 xl:min-h-[calc(100vh-7.5rem)]">
                {placeholderMessage && (
                  <Card className="border-amber-500/30 bg-amber-500/5">
                    <CardContent className="px-5 py-4 text-sm text-amber-800">{placeholderMessage}</CardContent>
                  </Card>
                )}

                {watchlistQuery.isLoading ? (
                  <WatchlistContextLoading className="flex-1" />
                ) : !selectedAssetId ? (
                  <EmptyPanel
                    className="flex-1"
                    icon={<ChartColumn className="size-6" />}
                    title="Pick a coin to open its brief"
                    description="Select any saved asset from the left to fill this panel with pricing, chart context, and the latest related updates."
                  />
                ) : selectedAssetContextQuery.isLoading ? (
                  <WatchlistContextLoading className="flex-1" />
                ) : selectedAssetContextQuery.isError ? (
                  <EmptyPanel
                    className="flex-1"
                    title="This asset brief is unavailable"
                    description={
                      selectedAssetContextQuery.error instanceof Error
                        ? "We couldn’t assemble the latest market brief for this selection. Try again shortly."
                        : "We couldn’t assemble the latest market brief for this selection. Try again shortly."
                    }
                  />
                ) : selectedAssetContextQuery.data ? (
                  <div className="flex h-full flex-col gap-4">
                    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                      <SummaryMetricCard
                        label="Price"
                        value={`$${formatCompactCurrency(selectedAssetContextQuery.data.summary.current_price)}`}
                        detail={selectedAsset?.symbol ?? selectedAssetContextQuery.data.summary.symbol}
                      />
                      <SummaryMetricCard
                        label="24h change"
                        value={`${selectedAssetContextQuery.data.summary.price_change_percentage_24h >= 0 ? "+" : ""}${selectedAssetContextQuery.data.summary.price_change_percentage_24h.toFixed(2)}%`}
                        detail={`$${formatCompactCurrency(selectedAssetContextQuery.data.summary.price_change_24h)}`}
                        positive={selectedAssetContextQuery.data.summary.price_change_percentage_24h >= 0}
                      />
                      <SummaryMetricCard
                        label="Market cap"
                        value={`$${formatCompactCurrency(selectedAssetContextQuery.data.summary.market_cap)}`}
                        detail={`Rank #${selectedAssetContextQuery.data.summary.market_cap_rank}`}
                      />
                      <SummaryMetricCard
                        label="Volume"
                        value={`$${formatCompactCurrency(selectedAssetContextQuery.data.summary.total_volume)}`}
                        detail={`24h range ${formatCompactCurrency(selectedAssetContextQuery.data.summary.low_24h)} - ${formatCompactCurrency(selectedAssetContextQuery.data.summary.high_24h)}`}
                      />
                    </div>

                    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_360px]">
                      <div className="grid gap-4">
                        <Card className="border-border/30 bg-card/60 backdrop-blur-sm">
                          <CardHeader>
                            <CardTitle>7-day chart</CardTitle>
                            <CardDescription className="pb-2">
                              A quick read on recent price movement for {selectedAssetContextQuery.data.summary.name}.
                            </CardDescription>
                          </CardHeader>
                          <CardContent className="h-[320px]">
                            <ResponsiveContainer width="100%" height="100%">
                              <AreaChart data={selectedAssetContextQuery.data.chart}>
                                <defs>
                                  <linearGradient id="watchlist-chart-fill" x1="0" x2="0" y1="0" y2="1">
                                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.35} />
                                    <stop offset="100%" stopColor="#10b981" stopOpacity={0.02} />
                                  </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} strokeOpacity={0.18} />
                                <XAxis
                                  dataKey="time"
                                  axisLine={{ stroke: "rgba(255,255,255,0.14)" }}
                                  tickLine={false}
                                  tick={{ fill: "rgba(255,255,255,0.52)", fontSize: 12 }}
                                  tickFormatter={(value) =>
                                    new Date(value).toLocaleDateString("en-GB", {
                                      month: "short",
                                      day: "numeric",
                                    })
                                  }
                                  minTickGap={32}
                                />
                                <YAxis
                                  axisLine={false}
                                  tickLine={false}
                                  tick={{ fill: "rgba(255,255,255,0.52)", fontSize: 12 }}
                                  tickFormatter={(value) => `$${formatCompactCurrency(Number(value))}`}
                                  width={90}
                                />
                                <Tooltip
                                  content={<WatchlistChartTooltip />}
                                />
                                <Area
                                  type="monotone"
                                  dataKey="price"
                                  stroke="#10b981"
                                  strokeWidth={2}
                                  fill="url(#watchlist-chart-fill)"
                                />
                              </AreaChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>

                        <Card className="border-border/30 bg-card/60 backdrop-blur-sm">
                        <CardHeader>
                          <CardTitle>Market snapshot</CardTitle>
                          <CardDescription className="pb-2">
                            The essentials behind the active selection.
                          </CardDescription>
                        </CardHeader>
                          <CardContent className="space-y-4">
                            <div className="flex items-center gap-3">
                              <AssetAvatar
                                symbol={selectedAssetContextQuery.data.summary.symbol}
                                imageUrl={selectedAssetContextQuery.data.summary.image_url}
                                large
                              />
                              <div>
                                <h3 className="font-semibold">{selectedAssetContextQuery.data.summary.name}</h3>
                                <p className="text-sm text-muted-foreground">
                                  {selectedAssetContextQuery.data.summary.symbol} · Rank #{selectedAssetContextQuery.data.summary.market_cap_rank}
                                </p>
                              </div>
                            </div>
                            <p className="text-sm leading-7 text-muted-foreground">
                              {selectedAssetContextQuery.data.summary.description || "A short profile for this asset is not available yet."}
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {selectedAssetContextQuery.data.summary.categories.length ? (
                                selectedAssetContextQuery.data.summary.categories.map((category) => (
                                  <Badge key={category} variant="secondary">
                                    {category}
                                  </Badge>
                                ))
                              ) : (
                                <Badge variant="secondary">No categories</Badge>
                              )}
                            </div>
                            {selectedAssetContextQuery.data.summary.homepage && (
                              <Button asChild variant="outline" className="w-full justify-between">
                                <Link href={selectedAssetContextQuery.data.summary.homepage} target="_blank" rel="noopener noreferrer">
                                  Visit official homepage
                                  <ExternalLink className="size-4" />
                                </Link>
                              </Button>
                            )}
                          </CardContent>
                        </Card>
                      </div>

                      <Card className="flex h-full min-h-[320px] flex-col border-border/30 bg-card/60 backdrop-blur-sm">
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Newspaper className="size-5 text-muted-foreground" />
                            Related updates
                          </CardTitle>
                          <CardDescription className="pb-2">
                            Recent reading and reference links connected to {selectedAssetContextQuery.data.summary.name}.
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="min-h-0 flex-1 overflow-y-auto">
                          {selectedAssetContextQuery.data.related_news.length ? (
                            <div className="grid gap-3">
                              {selectedAssetContextQuery.data.related_news.map((item) => (
                                <article key={`${item.url}-${item.title}`} className="rounded-xl border border-border/40 bg-background/70 p-4">
                                  <div className="flex items-center justify-between gap-3">
                                    <Badge variant="outline">{item.source}</Badge>
                                    {item.published_at ? (
                                      <span className="text-xs text-muted-foreground">
                                        {new Date(item.published_at).toLocaleDateString()}
                                      </span>
                                    ) : null}
                                  </div>
                                  <h3 className="mt-3 font-medium">{item.title}</h3>
                                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.summary}</p>
                                  <Button asChild variant="link" className="mt-3 px-0">
                                    <Link href={item.url} target="_blank" rel="noopener noreferrer">
                                      Open link
                                      <ExternalLink className="ml-1 size-4" />
                                    </Link>
                                  </Button>
                                </article>
                              ))}
                            </div>
                          ) : (
                            <div className="rounded-xl border border-dashed border-border/50 px-4 py-8 text-sm text-muted-foreground">
                              No related updates are available for this asset yet.
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                ) : null}
              </div>
            </section>
          </div>
        </div>
      </SidebarInset>
    </>
  );
}

function SummaryMetricCard({
  label,
  value,
  detail,
  positive,
}: {
  label: string;
  value: string;
  detail: string;
  positive?: boolean;
}) {
  return (
    <Card className="border-border/30 bg-card/60 backdrop-blur-sm">
      <CardHeader>
        <CardDescription className="pb-2">{label}</CardDescription>
        <CardTitle className={cn("text-2xl", positive !== undefined && (positive ? "text-emerald-600" : "text-rose-600"))}>
          {value}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0 text-sm text-muted-foreground">{detail}</CardContent>
    </Card>
  );
}

function AssetAvatar({
  symbol,
  imageUrl,
  large = false,
}: {
  symbol: string;
  imageUrl?: string;
  large?: boolean;
}) {
  const sizeClass = large ? "size-14 text-base" : "size-11 text-sm";

  if (imageUrl) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={imageUrl}
        alt={`${symbol} logo`}
        className={cn("rounded-full border border-border/40 bg-background object-cover", sizeClass)}
      />
    );
  }

  return (
    <div
      className={cn(
        "relative flex items-center justify-center rounded-full border border-border/40 bg-muted font-semibold text-muted-foreground",
        sizeClass
      )}
    >
      <Coins className={cn("absolute text-muted-foreground/25", large ? "size-7" : "size-5")} />
      <span className="relative z-10 text-[11px] font-semibold tracking-[0.08em] text-foreground/88">
        {symbol.slice(0, 3)}
      </span>
    </div>
  );
}

function EmptyPanel({
  title,
  description,
  className,
  compact = false,
  icon,
}: {
  title: string;
  description: string;
  className?: string;
  compact?: boolean;
  icon?: React.ReactNode;
}) {
  if (compact) {
    return (
      <div
        className={cn(
          "flex h-full min-h-[220px] flex-col items-center justify-center px-6 py-10 text-center",
          className
        )}>
        <div className="flex size-14 items-center justify-center rounded-full border border-border/50 bg-muted/30 text-muted-foreground/70">
          {icon ?? <Coins className="size-6" />}
        </div>
        <div className="mt-5">
          <h3 className="font-semibold">{title}</h3>
          <p className="mt-2 max-w-sm text-sm leading-6 text-muted-foreground">{description}</p>
        </div>
      </div>
    );
  }

  return (
    <Card className={cn("flex h-full border-border/30 bg-card/60 backdrop-blur-sm", className)}>
      <CardContent className="flex h-full min-h-[220px] flex-1 flex-col items-center justify-center px-6 py-10 text-center">
        <div className="flex size-14 items-center justify-center rounded-full border border-border/50 bg-muted/30 text-muted-foreground/70">
          {icon ?? <Coins className="size-6" />}
        </div>
        <div className="mt-4">
          <h3 className="font-semibold">{title}</h3>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">{description}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function WatchlistContextLoading({ className }: { className?: string }) {
  return (
    <div className={cn("space-y-4", className)}>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SummaryMetricSkeleton />
        <SummaryMetricSkeleton />
        <SummaryMetricSkeleton />
        <SummaryMetricSkeleton />
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_360px]">
        <div className="grid gap-4">
          <Card className="border-border/30 bg-card/60 backdrop-blur-sm">
            <CardHeader>
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-56" />
            </CardHeader>
            <CardContent className="h-[320px]">
              <Skeleton className="h-full w-full rounded-xl" />
            </CardContent>
          </Card>
          <Card className="border-border/30 bg-card/60 backdrop-blur-sm">
            <CardHeader>
              <Skeleton className="h-6 w-28" />
              <Skeleton className="h-4 w-44" />
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Skeleton className="size-14 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-5 w-32" />
                  <Skeleton className="h-4 w-24" />
                </div>
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-6 w-20 rounded-full" />
                <Skeleton className="h-6 w-24 rounded-full" />
              </div>
              <Skeleton className="h-10 w-full rounded-lg" />
            </CardContent>
          </Card>
        </div>
        <Card className="border-border/30 bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <Skeleton className="h-6 w-36" />
            <Skeleton className="h-4 w-52" />
          </CardHeader>
          <CardContent>
            <div className="grid gap-3">
              <NewsCardSkeleton />
              <NewsCardSkeleton />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function WatchlistChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value?: number | string }>;
  label?: string;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  const rawValue = payload[0]?.value;
  const numericValue = typeof rawValue === "number" ? rawValue : Number(rawValue ?? 0);

  return (
    <div className="rounded-xl border border-emerald-500/15 bg-background/95 px-3 py-2.5 shadow-2xl backdrop-blur-md">
      <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
        {label ? new Date(label).toLocaleString("en-GB") : "Price point"}
      </p>
      <p className="mt-2 text-sm font-semibold text-emerald-500">
        Price · ${formatCompactCurrency(numericValue)}
      </p>
    </div>
  );
}

function WatchlistListLoading() {
  return (
    <div className="flex h-full w-full flex-col px-4 pb-4 pt-4">
      <div className="space-y-2">
        <ListItemSkeleton />
        <ListItemSkeleton />
        <ListItemSkeleton />
        <ListItemSkeleton />
        <ListItemSkeleton />
      </div>
    </div>
  );
}

function ListItemSkeleton() {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-border/40 bg-background/70 px-4 py-3.5">
      <Skeleton className="size-11 rounded-full" />
      <div className="min-w-0 flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-5 w-12 rounded-full" />
        </div>
        <Skeleton className="h-3.5 w-24" />
      </div>
      <Skeleton className="size-8 rounded-full" />
    </div>
  );
}

function SummaryMetricSkeleton() {
  return (
    <Card className="border-border/30 bg-card/60 backdrop-blur-sm">
      <CardHeader>
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-8 w-24" />
      </CardHeader>
      <CardContent className="pt-0">
        <Skeleton className="h-4 w-28" />
      </CardContent>
    </Card>
  );
}

function NewsCardSkeleton() {
  return (
    <article className="rounded-xl border border-border/40 bg-background/70 p-4">
      <div className="flex items-center justify-between gap-3">
        <Skeleton className="h-6 w-20 rounded-full" />
        <Skeleton className="h-4 w-16" />
      </div>
      <div className="mt-3 space-y-2">
        <Skeleton className="h-5 w-4/5" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </div>
      <Skeleton className="mt-4 h-5 w-24" />
    </article>
  );
}

function formatCompactCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: value >= 1_000 ? "compact" : "standard",
    maximumFractionDigits: value >= 1_000 ? 2 : 2,
  }).format(value);
}
