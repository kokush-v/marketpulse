"use client";

import * as React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import type { DateRange } from "react-day-picker";
import { LoaderCircle, Newspaper, X } from "lucide-react";

import { getScenarioLabel, isPriceScenario, type AlertScenario, type TriggerMode } from "@/features/alerts/lib/alert-builder";
import {
  buildAlertSummary,
  getProjectedPrice,
  getScopeChartData,
  thresholdInputFromPrice,
  type AlertTimeBehavior,
  type ChartScope,
} from "@/features/alerts/lib/alert-draft";
import {
  getListAlertsAlertsGetQueryKey,
  useCreateAlertAlertsPost,
  useListAlertsAlertsGet,
  useUpdateAlertAlertsAlertIdPut,
} from "@/src/api/generated/alerts/alerts";
import {
  getGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGetQueryKey,
  useGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGet,
  useGetStarredWatchlistWatchlistsStarredGet,
} from "@/src/api/generated/watchlists/watchlists";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { cn } from "@/shared/lib/utils";

import { AlertCoinField } from "./alert-coin-field";
import { AlertPriceChart } from "./alert-price-chart";
import { AlertRepeatControl } from "./alert-repeat-control";

const SCENARIO_OPTIONS: AlertScenario[] = ["price_above", "price_below", "coin_news"];

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{children}</p>;
}

function PanelMessage({
  title,
  description,
  actionLabel,
  onAction,
}: {
  title: string;
  description: string;
  actionLabel: string;
  onAction: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-16 text-center">
      <p className="text-base font-semibold">{title}</p>
      <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      <Button className="mt-3" onClick={onAction}>
        {actionLabel}
      </Button>
    </div>
  );
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message.trim().length > 0 ? error.message : fallback;
}

/**
 * Create/edit form shown beside the alerts list. Mount it with a `key` per target
 * so closing and reopening discards unsaved input.
 */
export function AlertPanel({
  alertId,
  initialAssetId,
  onClose,
}: {
  alertId?: string;
  initialAssetId?: string;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const isEditing = Boolean(alertId);

  const [selectedAssetId, setSelectedAssetId] = React.useState<string | null>(null);
  const [scenario, setScenario] = React.useState<AlertScenario | null>(null);
  const [timeBehavior, setTimeBehavior] = React.useState<AlertTimeBehavior>("one_time");
  const [recurringRange, setRecurringRange] = React.useState<DateRange | undefined>(undefined);
  const [triggerMode, setTriggerMode] = React.useState<TriggerMode>("currency");
  const [thresholdInput, setThresholdInput] = React.useState("");
  const [chartScope, setChartScope] = React.useState<ChartScope>("1W");
  const [formError, setFormError] = React.useState<string | null>(null);
  const [requestError, setRequestError] = React.useState<string | null>(null);
  const hydratedRef = React.useRef(false);

  const watchlistQuery = useGetStarredWatchlistWatchlistsStarredGet(undefined, {
    query: { staleTime: 30_000, retry: 1 },
  });
  const contextQuery = useGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGet(
    selectedAssetId ?? "",
    undefined,
    { query: { enabled: Boolean(selectedAssetId), retry: 1 } },
  );
  const alertsQuery = useListAlertsAlertsGet(undefined, {
    query: { enabled: isEditing, staleTime: 30_000, retry: 1 },
  });
  const createAlertMutation = useCreateAlertAlertsPost();
  const updateAlertMutation = useUpdateAlertAlertsAlertIdPut();

  const watchlistAssets = React.useMemo(() => watchlistQuery.data?.assets ?? [], [watchlistQuery.data?.assets]);
  const selectedAsset = watchlistAssets.find((asset) => asset.asset_id === selectedAssetId) ?? null;
  const targetAlert = alertsQuery.data?.items.find((item) => item.id === alertId) ?? null;
  const isSaving = createAlertMutation.isPending || updateAlertMutation.isPending;

  React.useEffect(() => {
    if (!isEditing || hydratedRef.current || !targetAlert) {
      return;
    }

    hydratedRef.current = true;
    setSelectedAssetId(targetAlert.asset_id);
    setScenario(targetAlert.scenario);
    setTimeBehavior(targetAlert.time_behavior);
    setRecurringRange({
      from: targetAlert.recurring_start_date ? parseISO(targetAlert.recurring_start_date) : undefined,
      to: targetAlert.recurring_end_date ? parseISO(targetAlert.recurring_end_date) : undefined,
    });
    setTriggerMode(targetAlert.trigger_mode ?? "currency");
    setThresholdInput(typeof targetAlert.threshold_value === "number" ? String(targetAlert.threshold_value) : "");
  }, [isEditing, targetAlert]);

  React.useEffect(() => {
    if (isEditing || selectedAssetId || !initialAssetId) {
      return;
    }

    if (watchlistAssets.some((asset) => asset.asset_id === initialAssetId)) {
      setSelectedAssetId(initialAssetId);
    }
  }, [initialAssetId, isEditing, selectedAssetId, watchlistAssets]);

  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isSaving) {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSaving, onClose]);

  const currentPrice = contextQuery.data?.summary.current_price ?? 0;
  const thresholdValue = thresholdInput.trim() ? Number(thresholdInput) : null;
  const projectedPrice = getProjectedPrice({ currentPrice, scenario, triggerMode, thresholdValue });
  const chartData = React.useMemo(
    () => getScopeChartData(contextQuery.data?.chart ?? [], chartScope),
    [contextQuery.data?.chart, chartScope],
  );
  const recurringStart = recurringRange?.from;
  const recurringEnd = recurringRange?.to;
  const summary = buildAlertSummary({
    symbol: selectedAsset?.symbol ?? null,
    scenario,
    triggerMode,
    thresholdValue,
    projectedPrice,
    timeBehavior,
    recurringStart,
    recurringEnd,
  });

  const clearErrors = () => {
    setFormError(null);
    setRequestError(null);
  };

  const handleScenarioSelect = (next: AlertScenario) => {
    setScenario(next);
    clearErrors();
    if (next === "coin_news") {
      setTriggerMode("currency");
      setThresholdInput("");
    }
  };

  const handlePickPrice = (price: number) => {
    const next = thresholdInputFromPrice(price, triggerMode, currentPrice);
    if (next) {
      setThresholdInput(next);
      clearErrors();
    }
  };

  const handleSave = async () => {
    if (!selectedAsset) {
      setFormError("Choose a coin from your watchlist before saving.");
      return;
    }
    if (!scenario) {
      setFormError("Pick one of the three alert scenarios first.");
      return;
    }
    if (timeBehavior === "daily_recurring") {
      if (!recurringStart || !recurringEnd) {
        setFormError("Choose both a start date and an end date for the daily range.");
        return;
      }
      if (recurringEnd < recurringStart) {
        setFormError("The end date must not be earlier than the start date.");
        return;
      }
    }
    if (scenario !== "coin_news" && (!thresholdValue || thresholdValue <= 0)) {
      setFormError("Enter a positive trigger value for this price alert.");
      return;
    }

    clearErrors();

    const isDaily = timeBehavior === "daily_recurring";
    const payload = {
      asset_id: selectedAsset.asset_id,
      symbol: selectedAsset.symbol,
      name: selectedAsset.name,
      image_url: selectedAsset.image_url,
      scenario,
      time_behavior: timeBehavior,
      recurring_start_date: isDaily && recurringStart ? format(recurringStart, "yyyy-MM-dd") : undefined,
      recurring_end_date: isDaily && recurringEnd ? format(recurringEnd, "yyyy-MM-dd") : undefined,
      trigger_mode: scenario === "coin_news" ? undefined : triggerMode,
      threshold_value: scenario === "coin_news" ? undefined : (thresholdValue ?? undefined),
    };

    try {
      if (alertId) {
        await updateAlertMutation.mutateAsync({ alertId, data: payload });
      } else {
        await createAlertMutation.mutateAsync({ data: payload });
      }

      await queryClient.invalidateQueries({ queryKey: getListAlertsAlertsGetQueryKey() });
      await queryClient.invalidateQueries({
        queryKey: getGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGetQueryKey(
          selectedAsset.asset_id,
        ),
      });
      onClose();
    } catch (error) {
      setRequestError(errorMessage(error, "Unable to save this alert right now."));
    }
  };

  const renderBody = () => {
    if (watchlistQuery.isLoading || (isEditing && alertsQuery.isLoading)) {
      return (
        <div className="space-y-4 p-5" aria-label="Loading alert form">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-[300px] w-full" />
        </div>
      );
    }

    if (watchlistQuery.isError) {
      return (
        <PanelMessage
          title="Watchlist unavailable"
          description={errorMessage(watchlistQuery.error, "We could not load your saved coins right now.")}
          actionLabel="Retry"
          onAction={() => void watchlistQuery.refetch()}
        />
      );
    }

    if (isEditing && alertsQuery.isError) {
      return (
        <PanelMessage
          title="Alert unavailable"
          description={errorMessage(alertsQuery.error, "We could not load this alert right now.")}
          actionLabel="Retry"
          onAction={() => void alertsQuery.refetch()}
        />
      );
    }

    if (isEditing && alertsQuery.isSuccess && !targetAlert) {
      return (
        <PanelMessage
          title="Alert not found"
          description="This alert could not be loaded. It may have been removed already."
          actionLabel="Back to alerts"
          onAction={onClose}
        />
      );
    }

    return (
      <div className="space-y-6 p-5">
        <section>
          <FieldLabel>Coin</FieldLabel>
          <AlertCoinField
            assets={watchlistAssets}
            selectedAssetId={selectedAssetId}
            onSelect={(assetId) => {
              setSelectedAssetId(assetId);
              clearErrors();
            }}
            onError={setRequestError}
          />
        </section>

        <section>
          <FieldLabel>Notify me when</FieldLabel>
          <div
            role="group"
            aria-label="Scenario"
            className="inline-flex divide-x divide-border/40 overflow-hidden rounded-md border border-border/40"
          >
            {SCENARIO_OPTIONS.map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={scenario === option}
                onClick={() => handleScenarioSelect(option)}
                className={cn(
                  "h-9 px-3 text-sm font-medium transition-colors",
                  scenario === option
                    ? "bg-sky-500/15 text-sky-400"
                    : "text-muted-foreground hover:bg-muted/40 hover:text-foreground",
                )}
              >
                {getScenarioLabel(option)}
              </button>
            ))}
          </div>
        </section>

        {scenario && isPriceScenario(scenario) ? (
          <section className="space-y-4">
            <div>
              <FieldLabel>Trigger value</FieldLabel>
              <div className="flex items-center gap-2">
                <Input
                  inputMode="decimal"
                  value={thresholdInput}
                  onChange={(event) => {
                    setThresholdInput(event.target.value);
                    clearErrors();
                  }}
                  placeholder={triggerMode === "currency" ? "100000" : "12.5"}
                  aria-label="Trigger value"
                  className="h-10 rounded-md text-base"
                />
                <div role="group" aria-label="Trigger unit" className="inline-flex divide-x divide-border/40 overflow-hidden rounded-md border border-border/40">
                  {(["percent", "currency"] as const).map((mode) => (
                    <button
                      key={mode}
                      type="button"
                      aria-pressed={triggerMode === mode}
                      onClick={() => setTriggerMode(mode)}
                      className={cn(
                        "h-10 w-10 text-sm font-semibold transition-colors",
                        triggerMode === mode
                          ? "bg-sky-500/15 text-sky-400"
                          : "text-muted-foreground hover:bg-muted/40 hover:text-foreground",
                      )}
                    >
                      {mode === "percent" ? "%" : "$"}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {!selectedAssetId ? (
              <p className="rounded-lg border border-dashed border-border/40 px-3 py-6 text-center text-sm text-muted-foreground">
                Choose a coin to see its price chart.
              </p>
            ) : contextQuery.isLoading ? (
              <Skeleton className="h-[340px] w-full" />
            ) : contextQuery.isError ? (
              <PanelMessage
                title="Price data unavailable"
                description={errorMessage(contextQuery.error, "We could not load chart data for this coin right now.")}
                actionLabel="Retry"
                onAction={() => void contextQuery.refetch()}
              />
            ) : (
              <AlertPriceChart
                data={chartData}
                scope={chartScope}
                onScopeChange={setChartScope}
                scenario={scenario}
                triggerPrice={projectedPrice}
                onPickPrice={handlePickPrice}
              />
            )}
          </section>
        ) : null}

        {scenario === "coin_news" ? (
          <section className="flex items-start gap-3 rounded-lg border border-border/40 px-4 py-3">
            <Newspaper className="mt-0.5 size-4 shrink-0 text-sky-400" />
            <p className="text-sm text-muted-foreground">
              You will be notified about any new article for {selectedAsset?.name ?? "the selected coin"}.
            </p>
          </section>
        ) : null}

        <section>
          <FieldLabel>Repeat</FieldLabel>
          <AlertRepeatControl
            timeBehavior={timeBehavior}
            range={recurringRange}
            onTimeBehaviorChange={(value) => {
              setTimeBehavior(value);
              clearErrors();
              if (value === "one_time") {
                setRecurringRange(undefined);
              }
            }}
            onRangeChange={(range) => {
              setRecurringRange(range);
              clearErrors();
            }}
          />
        </section>
      </div>
    );
  };

  return (
    <aside
      role="complementary"
      aria-label={isEditing ? "Edit alert" : "New alert"}
      className="fixed inset-0 z-30 flex w-full flex-col border-l border-border/40 bg-background shadow-2xl md:left-auto md:w-[520px]"
    >
      <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-border/40 px-5">
        <h2 className="text-base font-semibold">{isEditing ? "Edit alert" : "New alert"}</h2>
        <Button variant="ghost" size="icon" className="size-8" onClick={onClose} disabled={isSaving} aria-label="Close panel">
          <X className="size-4" />
        </Button>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">{renderBody()}</div>

      <footer className="shrink-0 space-y-3 border-t border-border/40 bg-background px-5 py-4">
        {formError || requestError ? (
          <div role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {formError ?? requestError}
          </div>
        ) : null}
        <p className="text-sm font-medium">{summary}</p>
        <div className="flex items-center justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button type="button" onClick={() => void handleSave()} disabled={isSaving || !selectedAssetId || !scenario}>
            {isSaving ? <LoaderCircle className="size-4 animate-spin" /> : null}
            {isEditing ? "Save alert" : "Create alert"}
          </Button>
        </div>
      </footer>
    </aside>
  );
}
