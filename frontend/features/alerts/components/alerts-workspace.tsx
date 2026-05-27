"use client";

import Link from "next/link";
import * as React from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BellDot,
  BellPlus,
  CalendarClock,
  ChevronDown,
  ChevronRight,
  Newspaper,
  PauseCircle,
  Pencil,
  PlayCircle,
  Plus,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import {
  formatAlertSubtitle,
  formatRelativeDate,
  formatTriggerMode,
  getScenarioLabel,
} from "@/features/alerts/lib/alert-builder";
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Separator } from "@/shared/components/ui/separator";
import { SidebarInset, SidebarTrigger } from "@/shared/components/ui/sidebar";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { cn } from "@/shared/lib/utils";

export function AlertsWorkspace() {
  const queryClient = useQueryClient();
  const [collapsedGroups, setCollapsedGroups] = React.useState<Record<string, boolean>>({});
  const alertsQuery = useListAlertsAlertsGet(undefined, {
    query: {
      staleTime: 30_000,
      retry: 1,
    },
  });
  const pauseAlertMutation = usePauseAlertAlertsAlertIdPausePost();
  const resumeAlertMutation = useResumeAlertAlertsAlertIdResumePost();
  const deleteAlertMutation = useDeleteAlertAlertsAlertIdDelete();

  const alerts = alertsQuery.data?.items ?? [];
  const groupedAlerts = React.useMemo(() => {
    const groups = new Map<
      string,
      {
        assetId: string;
        name: string;
        symbol: string;
        alerts: AlertResponse[];
      }
    >();

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
  }, [alerts]);
  const isMutatingCard =
    pauseAlertMutation.isPending || resumeAlertMutation.isPending || deleteAlertMutation.isPending;

  const toggleGroup = (assetId: string) => {
    setCollapsedGroups((current) => ({
      ...current,
      [assetId]: !current[assetId],
    }));
  };

  const handlePauseResume = async (alert: AlertResponse) => {
    try {
      if (alert.status === "active") {
        await pauseAlertMutation.mutateAsync({ alertId: alert.id });
      } else {
        await resumeAlertMutation.mutateAsync({ alertId: alert.id });
      }
      await queryClient.invalidateQueries({ queryKey: getListAlertsAlertsGetQueryKey() });
    } catch {
      // Shared request handler already surfaces meaningful error messages.
    }
  };

  const handleDelete = async (alert: AlertResponse) => {
    try {
      await deleteAlertMutation.mutateAsync({ alertId: alert.id });
      await queryClient.invalidateQueries({ queryKey: getListAlertsAlertsGetQueryKey() });
    } catch {
      // Shared request handler already surfaces meaningful error messages.
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
              <Button asChild variant="outline" size="sm" className="gap-2">
                <Link href="/alerts/new">
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
              >
                <RefreshCw className={cn("size-4", alertsQuery.isFetching && "animate-spin")} />
              </Button>
            </div>
          </div>
        </header>

        <div className="@container/main flex min-h-[calc(100svh-4rem)] flex-col bg-background">
          <div className="flex flex-1 flex-col gap-4 px-4 py-4 lg:px-6 md:gap-6 md:py-6">
            <section className="grid min-h-0 flex-1 items-stretch gap-4">
              <Card className="flex h-full min-h-0 flex-col border-border/30 bg-card/60 backdrop-blur-sm">
                <CardHeader className="gap-5">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <CardTitle className="flex items-center gap-3 text-balance">
                        <span className="flex size-10 items-center justify-center rounded-full border border-sky-500/25 bg-sky-500/10 text-sky-600">
                          <BellDot className="size-4" />
                        </span>
                        Alert control center
                      </CardTitle>
                      <CardDescription className="mt-2 max-w-2xl leading-6">
                        Manage quick price and news alerts with a cleaner exchange-inspired flow.
                      </CardDescription>
                    </div>
                    <Badge
                      variant="secondary"
                      className="min-w-16 justify-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold tracking-[0.02em] text-foreground/85"
                    >
                      <BellPlus className="size-3.5 text-sky-600" />
                      {alerts.length}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex min-h-0 flex-1 flex-col space-y-4">
                  {alertsQuery.isLoading ? (
                    <div className="flex flex-wrap gap-4">
                      {Array.from({ length: 4 }).map((_, index) => (
                        <Skeleton key={index} className="h-56 w-full max-w-[420px] rounded-3xl" />
                      ))}
                    </div>
                  ) : alertsQuery.isError ? (
                    <EmptyPanel
                      title="Alerts are taking a moment"
                      description={
                        alertsQuery.error instanceof Error
                          ? alertsQuery.error.message
                          : "The alerts workspace is unavailable right now."
                      }
                      actionLabel="Retry"
                      href="#"
                      onAction={() => void alertsQuery.refetch()}
                    />
                  ) : alerts.length === 0 ? (
                    <EmptyPanel
                      title="No alerts yet"
                      description="Pick a coin, choose one of three clear scenarios, and create your first alert in a focused flow."
                      actionLabel="Create first alert"
                      href="/alerts/new"
                    />
                  ) : (
                    <div className="space-y-4">
                      {groupedAlerts.map((group) => {
                        const isCollapsed = collapsedGroups[group.assetId] ?? false;

                        return (
                          <div
                            key={group.assetId}
                            className="overflow-hidden rounded-3xl border border-border/30 bg-background/25"
                          >
                            <button
                              type="button"
                              onClick={() => toggleGroup(group.assetId)}
                              className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition hover:bg-muted/20"
                            >
                              <div className="flex items-center gap-3">
                                <span className="flex size-10 items-center justify-center rounded-2xl border border-sky-500/25 bg-sky-500/10 text-sky-300">
                                  <BellDot className="size-4" />
                                </span>
                                <div>
                                  <p className="text-base font-semibold">{group.name}</p>
                                  <div className="mt-1 flex items-center gap-2">
                                    <Badge variant="outline" className="rounded-full px-2.5 py-0.5">
                                      {group.symbol}
                                    </Badge>
                                    <span className="text-xs text-muted-foreground">
                                      {group.alerts.length} {group.alerts.length === 1 ? "alert" : "alerts"}
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center gap-3">
                                <Badge variant="secondary" className="rounded-full px-2.5 py-1">
                                  {group.alerts.filter((alert) => alert.status === "active").length} active
                                </Badge>
                                <ChevronDown
                                  className={cn(
                                    "size-4 text-muted-foreground transition-transform duration-200",
                                    !isCollapsed && "rotate-180"
                                  )}
                                />
                              </div>
                            </button>

                            {!isCollapsed ? (
                              <div className="border-t border-border/20 px-5 py-5">
                                <div className="flex flex-wrap items-start gap-4">
                                  {group.alerts.map((alert) => (
                                    <Card
                                      key={alert.id}
                                      className="relative w-full max-w-[430px] overflow-hidden border-border/30 bg-card/80 shadow-sm backdrop-blur-sm"
                                    >
                                      <CardHeader className="gap-5 pb-4">
                                        <div className="flex items-start justify-between gap-4">
                                          <div className="space-y-3">
                                            <div className="flex flex-wrap items-center gap-2.5">
                                              <CardTitle className="text-lg">{getScenarioLabel(alert.scenario)}</CardTitle>
                                              <Badge variant="secondary" className="rounded-full px-2.5 py-1">
                                                {formatTriggerMode(alert.trigger_mode)}
                                              </Badge>
                                            </div>
                                            <CardDescription className="text-sm leading-6">
                                              {formatAlertSubtitle(alert)}
                                            </CardDescription>
                                          </div>
                                          <Badge
                                            variant={alert.status === "active" ? "default" : "secondary"}
                                            className={cn(
                                              "rounded-full px-3 py-1 capitalize",
                                              alert.status === "active"
                                                ? "bg-emerald-600 text-white"
                                                : "bg-slate-200 text-slate-700"
                                            )}
                                          >
                                            {alert.status}
                                          </Badge>
                                        </div>
                                        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                                          <span className="inline-flex items-center gap-1.5">
                                            <CalendarClock className="size-3.5" />
                                            Created {formatRelativeDate(alert.created_at)}
                                          </span>
                                          <span className="h-1 w-1 rounded-full bg-muted-foreground/50" />
                                          <span>Updated {formatRelativeDate(alert.updated_at)}</span>
                                        </div>
                                      </CardHeader>
                                      <CardContent className="space-y-5 pt-0">
                                        <div className="rounded-3xl border border-border/40 bg-background/55 px-4 py-4">
                                          <div className="flex items-start gap-3">
                                            <span
                                              className={cn(
                                                "mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-2xl border",
                                                getAlertRuleTone(alert.scenario)
                                              )}
                                            >
                                              {getAlertRuleIcon(alert.scenario)}
                                            </span>
                                            <div className="space-y-1">
                                              <p className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
                                                Trigger rule
                                              </p>
                                              <p className="text-sm leading-6 text-foreground">{alert.rule_summary}</p>
                                            </div>
                                          </div>
                                        </div>
                                        <div className="rounded-3xl border border-border/40 bg-background/55 px-4 py-4">
                                          <div className="flex items-start gap-3">
                                            <span className="mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-2xl border border-sky-500/25 bg-sky-500/10 text-sky-300">
                                              <CalendarClock className="size-4" />
                                            </span>
                                            <div className="space-y-1">
                                              <p className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
                                                Timing
                                              </p>
                                              <p className="text-sm leading-6 text-foreground">{alert.time_summary}</p>
                                            </div>
                                          </div>
                                        </div>
                                        <div className="flex flex-wrap gap-2.5 pt-1">
                                          <Button
                                            asChild
                                            variant="outline"
                                            size="sm"
                                            className="gap-2 rounded-full"
                                            disabled={isMutatingCard}
                                          >
                                            <Link href={`/alerts/${alert.id}/edit`}>
                                              <Pencil className="size-4" />
                                              Edit
                                            </Link>
                                          </Button>
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            className="gap-2 rounded-full"
                                            onClick={() => void handlePauseResume(alert)}
                                            disabled={isMutatingCard}
                                          >
                                            {alert.status === "active" ? (
                                              <>
                                                <PauseCircle className="size-4" />
                                                Pause
                                              </>
                                            ) : (
                                              <>
                                                <PlayCircle className="size-4" />
                                                Resume
                                              </>
                                            )}
                                          </Button>
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            className="gap-2 rounded-full px-0 text-destructive hover:text-destructive"
                                            onClick={() => void handleDelete(alert)}
                                            disabled={isMutatingCard}
                                          >
                                            <Trash2 className="size-4" />
                                            Delete
                                          </Button>
                                        </div>
                                      </CardContent>
                                    </Card>
                                  ))}
                                </div>
                              </div>
                            ) : null}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </section>
          </div>
        </div>
      </SidebarInset>
    </>
  );
}

function getAlertRuleIcon(scenario: AlertResponse["scenario"]) {
  if (scenario === "price_above") {
    return <ArrowUpRight className="size-4" />;
  }
  if (scenario === "price_below") {
    return <ArrowDownRight className="size-4" />;
  }
  return <Newspaper className="size-4" />;
}

function getAlertRuleTone(scenario: AlertResponse["scenario"]) {
  if (scenario === "price_above") {
    return "border-emerald-500/25 bg-emerald-500/10 text-emerald-300";
  }
  if (scenario === "price_below") {
    return "border-rose-500/25 bg-rose-500/10 text-rose-300";
  }
  return "border-sky-500/25 bg-sky-500/10 text-sky-300";
}

function EmptyPanel({
  title,
  description,
  actionLabel,
  href,
  onAction,
}: {
  title: string;
  description: string;
  actionLabel: string;
  href: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex min-h-[22rem] flex-1 flex-col items-center justify-center rounded-3xl border border-dashed border-border/60 bg-background/80 px-6 py-10 text-center">
      <div className="flex size-14 items-center justify-center rounded-full border border-border/50 bg-muted/30">
        <BellPlus className="size-6 text-muted-foreground" />
      </div>
      <h3 className="mt-5 text-lg font-semibold tracking-tight text-foreground">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>
      {onAction ? (
        <Button className="mt-6" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : (
        <Button asChild className="mt-6">
          <Link href={href}>
            {actionLabel}
            <ChevronRight className="ml-2 size-4" />
          </Link>
        </Button>
      )}
    </div>
  );
}
