"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";
import { BellPlus, ChevronDown, ChevronRight, Plus, RefreshCw, SearchX } from "lucide-react";
import { keepPreviousData, useQueryClient } from "@tanstack/react-query";

import { useAlertsViewPreference } from "@/features/alerts/hooks/use-alerts-view-preference";
import { useDebouncedValue } from "@/features/alerts/hooks/use-debounced-value";
import {
  DEFAULT_ALERT_FILTERS,
  hasActiveFilters,
  toListAlertsParams,
  type AlertFilters,
} from "@/features/alerts/lib/alert-filters";
import { AppSidebar } from "@/features/market-dashboard/components/app-sidebar";
import {
  getListAlertsAlertsGetQueryKey,
  useDeleteAlertAlertsAlertIdDelete,
  useListAlertsAlertsGet,
  usePauseAlertAlertsAlertIdPausePost,
  useResumeAlertAlertsAlertIdResumePost,
} from "@/src/api/generated/alerts/alerts";
import type { AlertResponse } from "@/src/api/generated/models/alertResponse";
import { Badge } from "@/shared/components/ui/badge";
import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from "@/shared/components/ui/breadcrumb";
import { Button } from "@/shared/components/ui/button";
import { Separator } from "@/shared/components/ui/separator";
import { SidebarInset, SidebarTrigger } from "@/shared/components/ui/sidebar";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { cn } from "@/shared/lib/utils";

import { AlertPanel } from "./alert-panel";
import { AlertCard, AlertRow } from "./alert-list-item";
import { AlertsFilterBar, AlertsViewSwitcher } from "./alerts-filter-bar";
import { DeleteAlertDialog } from "./delete-alert-dialog";

const SEARCH_DEBOUNCE_MS = 300;

interface AlertGroup {
  assetId: string;
  name: string;
  symbol: string;
  alerts: AlertResponse[];
}

function groupAlertsByCoin(alerts: AlertResponse[]): AlertGroup[] {
  const groups = new Map<string, AlertGroup>();

  for (const alert of alerts) {
    const existing = groups.get(alert.asset_id);
    if (existing) {
      existing.alerts.push(alert);
      continue;
    }

    groups.set(alert.asset_id, {
      assetId: alert.asset_id,
      name: alert.name,
      symbol: alert.symbol,
      alerts: [alert],
    });
  }

  return Array.from(groups.values()).sort((left, right) => left.name.localeCompare(right.name));
}

function getActionErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallback;
}

export type AlertPanelTarget = { mode: "new"; assetId?: string } | { mode: "edit"; alertId: string };

export function AlertsWorkspace({ panel = null }: { panel?: AlertPanelTarget | null }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [view, setView] = useAlertsViewPreference();
  const [filters, setFilters] = React.useState<AlertFilters>(DEFAULT_ALERT_FILTERS);
  const [collapsedGroups, setCollapsedGroups] = React.useState<Record<string, boolean>>({});
  const [actionError, setActionError] = React.useState<string | null>(null);
  const [alertToDelete, setAlertToDelete] = React.useState<AlertResponse | null>(null);

  const debouncedSearch = useDebouncedValue(filters.search, SEARCH_DEBOUNCE_MS);
  const appliedFilters = React.useMemo<AlertFilters>(
    () => ({ ...filters, search: debouncedSearch }),
    [filters, debouncedSearch],
  );
  const filtersApplied = hasActiveFilters(appliedFilters);

  const alertsQuery = useListAlertsAlertsGet(toListAlertsParams(appliedFilters), {
    query: {
      staleTime: 30_000,
      retry: 1,
      placeholderData: keepPreviousData,
    },
  });
  const pauseAlertMutation = usePauseAlertAlertsAlertIdPausePost();
  const resumeAlertMutation = useResumeAlertAlertsAlertIdResumePost();
  const deleteAlertMutation = useDeleteAlertAlertsAlertIdDelete();

  const alerts = React.useMemo(() => alertsQuery.data?.items ?? [], [alertsQuery.data?.items]);
  const counts = alertsQuery.data?.counts;
  const groupedAlerts = React.useMemo(() => groupAlertsByCoin(alerts), [alerts]);
  const isMutating =
    pauseAlertMutation.isPending || resumeAlertMutation.isPending || deleteAlertMutation.isPending;
  const showToolbar = !alertsQuery.isLoading && !alertsQuery.isError && (filtersApplied || alerts.length > 0);

  const closePanel = React.useCallback(() => router.replace("/alerts"), [router]);

  const refreshAlerts = () => queryClient.invalidateQueries({ queryKey: getListAlertsAlertsGetQueryKey() });

  const toggleGroup = (assetId: string) => {
    setCollapsedGroups((current) => ({ ...current, [assetId]: !current[assetId] }));
  };

  const handleToggleStatus = async (alert: AlertResponse) => {
    const isPausing = alert.status === "active";

    try {
      if (isPausing) {
        await pauseAlertMutation.mutateAsync({ alertId: alert.id });
      } else {
        await resumeAlertMutation.mutateAsync({ alertId: alert.id });
      }
      await refreshAlerts();
      setActionError(null);
    } catch (error) {
      setActionError(getActionErrorMessage(error, `Unable to ${isPausing ? "pause" : "resume"} this alert.`));
    }
  };

  const handleConfirmDelete = async () => {
    if (!alertToDelete) {
      return;
    }

    try {
      await deleteAlertMutation.mutateAsync({ alertId: alertToDelete.id });
      await refreshAlerts();
      setActionError(null);
    } catch (error) {
      setActionError(getActionErrorMessage(error, "Unable to delete this alert."));
    } finally {
      setAlertToDelete(null);
    }
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
                  <BreadcrumbPage className="text-sm font-semibold">Alerts</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
            <Badge variant="outline" className="hidden border-sky-500/20 text-sky-700 md:inline-flex">
              Protected workspace
            </Badge>
            <div className="ml-auto flex items-center gap-3">
              <AlertsViewSwitcher view={view} onChange={setView} />
              <Button asChild variant="outline" size="sm" className="gap-2">
                <Link href="/alerts?new=1">
                  <Plus className="size-4" />
                  New alert
                </Link>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-9 w-9 p-0"
                onClick={() => void alertsQuery.refetch()}
                disabled={alertsQuery.isFetching}
                aria-label="Refresh alerts list"
              >
                <RefreshCw className={cn("size-4", alertsQuery.isFetching && "animate-spin")} />
              </Button>
            </div>
          </div>
        </header>

        <div className="@container/main flex min-h-[calc(100svh-4rem)] flex-col bg-background">
          <div
            className={cn(
              "flex flex-1 flex-col gap-4 px-4 py-4 md:gap-5 md:py-6 lg:px-6",
              panel && "md:pr-[calc(520px+1.5rem)]",
            )}
          >
            {showToolbar ? <AlertsFilterBar filters={filters} counts={counts} onChange={setFilters} /> : null}

            {actionError ? (
              <div
                role="alert"
                className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
              >
                {actionError}
              </div>
            ) : null}

            {alertsQuery.isLoading ? (
              <div className="space-y-3" aria-label="Loading alerts">
                {Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton key={index} className="h-16 w-full rounded-2xl" />
                ))}
              </div>
            ) : alertsQuery.isError ? (
              <StatePanel
                title="Alerts are taking a moment"
                description={
                  alertsQuery.error instanceof Error
                    ? alertsQuery.error.message
                    : "The alerts workspace is unavailable right now."
                }
                actionLabel="Retry"
                onAction={() => void alertsQuery.refetch()}
              />
            ) : alerts.length === 0 && filtersApplied ? (
              <StatePanel
                icon="no-results"
                title="No alerts match these filters"
                description="Try a different search or clear the filters to see all of your alerts."
                actionLabel="Clear filters"
                onAction={() => setFilters(DEFAULT_ALERT_FILTERS)}
              />
            ) : alerts.length === 0 ? (
              <StatePanel
                title="No alerts yet"
                description="Pick a coin, choose one of three clear scenarios, and create your first alert in a focused flow."
                actionLabel="Create first alert"
                href="/alerts?new=1"
              />
            ) : (
              <div className={cn("space-y-4 transition-opacity", alertsQuery.isPlaceholderData && "opacity-60")}>
                {groupedAlerts.map((group) => {
                  const isCollapsed = collapsedGroups[group.assetId] ?? false;
                  const activeCount = group.alerts.filter((alert) => alert.status === "active").length;

                  return (
                    <section key={group.assetId} className="overflow-hidden rounded-2xl border border-border/30 bg-card/40">
                      <button
                        type="button"
                        onClick={() => toggleGroup(group.assetId)}
                        aria-expanded={!isCollapsed}
                        className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left transition hover:bg-muted/20"
                      >
                        <div className="flex items-center gap-3">
                          <p className="text-base font-semibold">{group.name}</p>
                          <Badge variant="outline" className="rounded-full px-2.5 py-0.5">
                            {group.symbol}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {group.alerts.length} {group.alerts.length === 1 ? "alert" : "alerts"} · {activeCount} active
                          </span>
                        </div>
                        <ChevronDown
                          className={cn(
                            "size-4 text-muted-foreground transition-transform duration-200",
                            !isCollapsed && "rotate-180",
                          )}
                        />
                      </button>

                      {!isCollapsed ? (
                        view === "list" ? (
                          <div className="divide-y divide-border/20 border-t border-border/20">
                            {group.alerts.map((alert) => (
                              <AlertRow
                                key={alert.id}
                                alert={alert}
                                disabled={isMutating}
                                onToggleStatus={(target) => void handleToggleStatus(target)}
                                onDelete={setAlertToDelete}
                              />
                            ))}
                          </div>
                        ) : (
                          <div className="grid gap-3 border-t border-border/20 p-4 sm:grid-cols-2 xl:grid-cols-3">
                            {group.alerts.map((alert) => (
                              <AlertCard
                                key={alert.id}
                                alert={alert}
                                disabled={isMutating}
                                onToggleStatus={(target) => void handleToggleStatus(target)}
                                onDelete={setAlertToDelete}
                              />
                            ))}
                          </div>
                        )
                      ) : null}
                    </section>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </SidebarInset>

      {panel ? (
        <AlertPanel
          key={panel.mode === "edit" ? `edit-${panel.alertId}` : `new-${panel.assetId ?? ""}`}
          alertId={panel.mode === "edit" ? panel.alertId : undefined}
          initialAssetId={panel.mode === "new" ? panel.assetId : undefined}
          onClose={closePanel}
        />
      ) : null}

      <DeleteAlertDialog
        alert={alertToDelete}
        pending={deleteAlertMutation.isPending}
        onCancel={() => setAlertToDelete(null)}
        onConfirm={() => void handleConfirmDelete()}
      />
    </>
  );
}

function StatePanel({
  title,
  description,
  actionLabel,
  href,
  onAction,
  icon = "alerts",
}: {
  title: string;
  description: string;
  actionLabel: string;
  href?: string;
  onAction?: () => void;
  icon?: "alerts" | "no-results";
}) {
  const Icon = icon === "no-results" ? SearchX : BellPlus;

  return (
    <div className="flex min-h-[22rem] flex-1 flex-col items-center justify-center rounded-3xl border border-dashed border-border/60 bg-background/80 px-6 py-10 text-center">
      <div className="flex size-14 items-center justify-center rounded-full border border-border/50 bg-muted/30">
        <Icon className="size-6 text-muted-foreground" />
      </div>
      <h3 className="mt-5 text-lg font-semibold tracking-tight text-foreground">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>
      {onAction ? (
        <Button className="mt-6" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : (
        <Button asChild className="mt-6">
          <Link href={href ?? "/alerts?new=1"}>
            {actionLabel}
            <ChevronRight className="ml-2 size-4" />
          </Link>
        </Button>
      )}
    </div>
  );
}
