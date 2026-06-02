"use client";

import * as React from "react";
import {
  Bot,
  CheckCircle2,
  Copy,
  ExternalLink,
  Link2Off,
  RefreshCw,
  Send,
  ShieldAlert,
  Zap,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { AppSidebar } from "@/features/market-dashboard/components/app-sidebar";
import {
  getGetTelegramIntegrationStateIntegrationsTelegramGetQueryKey,
  useDisconnectTelegramIntegrationsTelegramDelete,
  useGetTelegramIntegrationStateIntegrationsTelegramGet,
  useSendTelegramTestNotificationIntegrationsTelegramTestNotificationPost,
  useStartTelegramConnectionIntegrationsTelegramConnectPost,
} from "@/src/api/generated/telegram/telegram";
import { useListNotificationsNotificationsGet } from "@/src/api/generated/notifications/notifications";
import { Badge } from "@/shared/components/ui/badge";
import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from "@/shared/components/ui/breadcrumb";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Separator } from "@/shared/components/ui/separator";
import { SidebarInset, SidebarTrigger } from "@/shared/components/ui/sidebar";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { cn } from "@/shared/lib/utils";

export function IntegrationsWorkspace() {
  const queryClient = useQueryClient();
  const [copied, setCopied] = React.useState(false);
  const [actionError, setActionError] = React.useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = React.useState<string | null>(null);
  const [hasRefetchedAfterConnect, setHasRefetchedAfterConnect] = React.useState(false);
  const [pendingConnectState, setPendingConnectState] = React.useState<{
    deep_link: string | null;
    fallback_code: string | null;
    expires_at: string | null;
    bot_username: string;
    state: "token_ready";
  } | null>(null);

  const integrationQuery = useGetTelegramIntegrationStateIntegrationsTelegramGet({
    query: {
      staleTime: 15_000,
      refetchInterval: pendingConnectState ? 3_000 : false,
      retry: 1,
    },
  });
  const notificationsQuery = useListNotificationsNotificationsGet({
    query: {
      staleTime: 15_000,
      retry: 1,
    },
  });
  const connectMutation = useStartTelegramConnectionIntegrationsTelegramConnectPost();
  const disconnectMutation = useDisconnectTelegramIntegrationsTelegramDelete();
  const testNotificationMutation =
    useSendTelegramTestNotificationIntegrationsTelegramTestNotificationPost();

  const liveState = integrationQuery.data;
  const effectiveState =
    liveState?.state === "connected"
      ? liveState
      : pendingConnectState ?? liveState ?? { state: "not_connected" as const, bot_username: "marketpulse_bot" };
  const telegramNotifications = (notificationsQuery.data?.items ?? []).filter(
    (item) => item.channel === "telegram"
  );

  React.useEffect(() => {
    if (liveState?.state === "connected") {
      setPendingConnectState(null);
      if (!hasRefetchedAfterConnect) {
        setHasRefetchedAfterConnect(true);
        void notificationsQuery.refetch();
      }
      return;
    }

    if (hasRefetchedAfterConnect) {
      setHasRefetchedAfterConnect(false);
    }
  }, [hasRefetchedAfterConnect, liveState?.state, notificationsQuery.refetch]);

  const refresh = async () => {
    await Promise.all([integrationQuery.refetch(), notificationsQuery.refetch()]);
  };

  const handleConnect = async () => {
    try {
      const response = await connectMutation.mutateAsync();
      setPendingConnectState({
        state: "token_ready",
        deep_link: response.deep_link ?? null,
        fallback_code: response.fallback_code ?? null,
        expires_at: response.expires_at ?? null,
        bot_username: response.bot_username,
      });
      setActionError(null);
      setActionSuccess(null);
      setHasRefetchedAfterConnect(false);
      await queryClient.invalidateQueries({
        queryKey: getGetTelegramIntegrationStateIntegrationsTelegramGetQueryKey(),
      });
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Unable to start Telegram connection right now.");
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectMutation.mutateAsync();
      setPendingConnectState(null);
      setActionError(null);
      setActionSuccess(null);
      setHasRefetchedAfterConnect(false);
      await queryClient.invalidateQueries({
        queryKey: getGetTelegramIntegrationStateIntegrationsTelegramGetQueryKey(),
      });
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Unable to disconnect Telegram right now.");
    }
  };

  const handleSendTestNotification = async () => {
    try {
      const response = await testNotificationMutation.mutateAsync();
      setActionError(null);
      setActionSuccess(response.message);
      await notificationsQuery.refetch();
    } catch (error) {
      setActionSuccess(null);
      setActionError(
        error instanceof Error
          ? error.message
          : "Unable to send a Telegram test notification right now."
      );
    }
  };

  const handleCopyCode = async () => {
    if (!effectiveState.fallback_code) {
      return;
    }

    try {
      await navigator.clipboard.writeText(effectiveState.fallback_code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      setActionError("Clipboard access is unavailable. Copy the code manually instead.");
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
                  <BreadcrumbPage className="text-sm font-semibold">Integrations</BreadcrumbPage>
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
                onClick={() => void refresh()}
                disabled={integrationQuery.isFetching || notificationsQuery.isFetching}
                aria-label="Refresh integrations"
              >
                <RefreshCw
                  className={cn(
                    "size-4",
                    (integrationQuery.isFetching || notificationsQuery.isFetching) && "animate-spin"
                  )}
                />
              </Button>
            </div>
          </div>
        </header>

        <div className="@container/main flex min-h-[calc(100svh-4rem)] flex-col bg-[radial-gradient(circle_at_top_left,_rgba(34,197,94,0.08),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(14,165,233,0.08),_transparent_24%),linear-gradient(to_bottom,_rgba(255,255,255,0.02),_rgba(255,255,255,0))]">
          <div className="flex flex-1 flex-col gap-4 px-4 py-4 lg:px-6 md:gap-6 md:py-6">
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
              <Card className="border-border/30 bg-card/70 backdrop-blur-sm">
                <CardHeader className="gap-5">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <CardTitle className="flex items-center gap-3 text-balance">
                        <span className="flex size-10 items-center justify-center rounded-full border border-emerald-500/25 bg-emerald-500/10 text-emerald-600">
                          <Bot className="size-4" />
                        </span>
                        Telegram connection
                      </CardTitle>
                      <CardDescription className="mt-2 max-w-2xl leading-6">
                        Link one Telegram account to your current MarketPulse user, then let alert delivery flow through the bot.
                      </CardDescription>
                    </div>
                    <StateBadge state={effectiveState.state} />
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {actionError ? (
                    <div
                      role="alert"
                      className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
                    >
                      {actionError}
                    </div>
                  ) : null}
                  {actionSuccess ? (
                    <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700">
                      {actionSuccess}
                    </div>
                  ) : null}

                  {integrationQuery.isLoading ? (
                    <div className="space-y-3">
                      <Skeleton className="h-28 rounded-3xl" />
                      <Skeleton className="h-12 rounded-2xl" />
                    </div>
                  ) : integrationQuery.isError ? (
                    <EmptyState
                      title="Telegram integration is taking a moment"
                      description={
                        integrationQuery.error instanceof Error
                          ? integrationQuery.error.message
                          : "We couldn’t load the current Telegram state right now."
                      }
                    />
                  ) : effectiveState.state === "connected" ? (
                    <div className="space-y-4 rounded-3xl border border-emerald-500/20 bg-emerald-500/5 p-5">
                      <div className="flex items-start gap-3">
                        <CheckCircle2 className="mt-0.5 size-5 text-emerald-600" />
                        <div className="space-y-1">
                          <p className="font-medium text-foreground">Telegram is connected</p>
                          <p className="text-sm leading-6 text-muted-foreground">
                            {effectiveState.connection?.telegram_username
                              ? `Linked as @${effectiveState.connection.telegram_username}`
                              : "Your Telegram account is actively linked."}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-3">
                        <Button
                          className="gap-2"
                          onClick={() => void handleSendTestNotification()}
                          disabled={testNotificationMutation.isPending}
                        >
                          <Send className="size-4" />
                          {testNotificationMutation.isPending
                            ? "Sending test..."
                            : "Send Test Notification"}
                        </Button>
                        <Button
                          variant="outline"
                          className="gap-2"
                          onClick={() => void handleDisconnect()}
                          disabled={disconnectMutation.isPending}
                        >
                          <Link2Off className="size-4" />
                          Disconnect
                        </Button>
                      </div>
                    </div>
                  ) : effectiveState.state === "token_ready" ? (
                    <div className="space-y-4 rounded-3xl border border-sky-500/20 bg-sky-500/5 p-5">
                      <div className="flex items-start gap-3">
                        <Zap className="mt-0.5 size-5 text-sky-600" />
                        <div className="space-y-1">
                          <p className="font-medium text-foreground">Linking token is ready</p>
                          <p className="text-sm leading-6 text-muted-foreground">
                            Open the bot from the generated deep link, or copy the fallback code and finish the `/start` flow there.
                          </p>
                        </div>
                      </div>
                      <div className="rounded-2xl border border-border/40 bg-background/70 p-4">
                        <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                          Fallback code
                        </p>
                        <p className="mt-2 break-all font-mono text-sm text-foreground">
                          {effectiveState.fallback_code}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-3">
                        <Button asChild className="gap-2">
                          <a href={effectiveState.deep_link ?? "#"} target="_blank" rel="noreferrer">
                            <ExternalLink className="size-4" />
                            Open bot
                          </a>
                        </Button>
                        <Button variant="outline" className="gap-2" onClick={() => void handleCopyCode()}>
                          <Copy className="size-4" />
                          {copied ? "Copied" : "Copy code"}
                        </Button>
                        <Button variant="ghost" className="gap-2" onClick={() => void handleConnect()}>
                          <RefreshCw className={cn("size-4", connectMutation.isPending && "animate-spin")} />
                          Regenerate token
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4 rounded-3xl border border-border/30 bg-background/40 p-5">
                      <div className="flex items-start gap-3">
                        <ShieldAlert className="mt-0.5 size-5 text-muted-foreground" />
                        <div className="space-y-1">
                          <p className="font-medium text-foreground">No Telegram account linked yet</p>
                          <p className="text-sm leading-6 text-muted-foreground">
                            Start from the web app so ownership stays bound to your authenticated MarketPulse account before the bot confirms it.
                          </p>
                        </div>
                      </div>
                      <Button className="gap-2" onClick={() => void handleConnect()} disabled={connectMutation.isPending}>
                        <Bot className="size-4" />
                        {connectMutation.isPending ? "Preparing..." : "Connect Telegram"}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="border-border/30 bg-card/70 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-lg">Telegram delivery history</CardTitle>
                  <CardDescription>
                    Recent Telegram alert outcomes stay scoped to your authenticated account only.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {notificationsQuery.isLoading ? (
                    <>
                      <Skeleton className="h-20 rounded-2xl" />
                      <Skeleton className="h-20 rounded-2xl" />
                    </>
                  ) : notificationsQuery.isError ? (
                    <EmptyState
                      title="Notification history is unavailable"
                      description={
                        notificationsQuery.error instanceof Error
                          ? notificationsQuery.error.message
                          : "We couldn’t load Telegram delivery records right now."
                      }
                    />
                  ) : telegramNotifications.length === 0 ? (
                    <EmptyState
                      title="No Telegram deliveries yet"
                      description="Once an eligible alert sends through Telegram, its safe delivery outcome will appear here."
                    />
                  ) : (
                    telegramNotifications.slice(0, 5).map((item) => (
                      <div
                        key={item.id}
                        className="rounded-2xl border border-border/30 bg-background/60 px-4 py-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium text-foreground">{item.message_summary}</p>
                            <p className="mt-1 text-sm text-muted-foreground">
                              {item.safe_error_message ??
                                (item.delivery_status === "delivered"
                                  ? "Delivered to the linked Telegram chat."
                                  : "Pending background delivery.")}
                            </p>
                          </div>
                          <Badge
                            variant={item.delivery_status === "delivered" ? "default" : "secondary"}
                            className={cn(
                              item.delivery_status === "failed" && "bg-destructive/10 text-destructive"
                            )}
                          >
                            {item.delivery_status}
                          </Badge>
                        </div>
                      </div>
                    ))
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

function StateBadge({ state }: { state: "not_connected" | "token_ready" | "connected" | "error" }) {
  if (state === "connected") {
    return <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">Connected</Badge>;
  }

  if (state === "token_ready") {
    return <Badge className="bg-sky-600 text-white hover:bg-sky-600">Token ready</Badge>;
  }

  if (state === "error") {
    return <Badge variant="destructive">Error</Badge>;
  }

  return <Badge variant="secondary">Not connected</Badge>;
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-3xl border border-dashed border-border/50 bg-background/40 px-5 py-6">
      <p className="font-medium text-foreground">{title}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
    </div>
  );
}
