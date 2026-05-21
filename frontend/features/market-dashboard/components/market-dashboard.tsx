"use client";

import * as React from "react";
import Link from "next/link";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";
import {
	Activity,
	ArrowRight,
	BarChart3,
	BriefcaseBusiness,
	CircleAlert,
	Clock3,
	ExternalLink,
	LineChart,
	LockKeyhole,
	RefreshCw,
	TrendingDown,
	TrendingUp,
} from "lucide-react";

import { AppSidebar } from "@/features/market-dashboard/components/app-sidebar";
import { useMarketOverview } from "@/features/market-dashboard/hooks/use-market-overview";
import type { FeaturedCard, MarketChartPoint, MarketMover } from "@/features/market-dashboard/lib/types";
import { Badge } from "@/shared/components/ui/badge";
import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from "@/shared/components/ui/breadcrumb";
import { Button } from "@/shared/components/ui/button";
import {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "@/shared/components/ui/card";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/shared/components/ui/chart";
import { Separator } from "@/shared/components/ui/separator";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { Spinner } from "@/shared/components/ui/spinner";
import { SidebarInset, SidebarTrigger } from "@/shared/components/ui/sidebar";
import { hasSession } from "@/shared/lib/auth";
import { cn } from "@/shared/lib/utils";

export function MarketDashboard() {
	const { data, isLoading, isError, error, refetch, isFetching } = useMarketOverview();
	const isAuthenticated = typeof window !== "undefined" && hasSession();

	return (
		<>
			<AppSidebar />
			<SidebarInset>
				{/* Header */}
				<header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b border-border/40 bg-background/95 backdrop-blur-sm">
					<div className="flex w-full items-center gap-3 px-4 lg:px-6">
						<SidebarTrigger className="-ml-1" />
						<Separator orientation="vertical" className="h-6 bg-border" />
						<Breadcrumb>
							<BreadcrumbList>
								<BreadcrumbItem>
									<BreadcrumbPage className="text-sm font-semibold">Market Overview</BreadcrumbPage>
								</BreadcrumbItem>
							</BreadcrumbList>
						</Breadcrumb>
						<div className="ml-auto flex items-center gap-3">
							<Button
								variant="ghost"
								size="sm"
								className="h-9 w-9 p-0"
								onClick={() => void refetch()}
								disabled={isFetching}>
								<RefreshCw className={cn("size-4", isFetching && "animate-spin")} />
							</Button>
						</div>
					</div>
				</header>

				{/* Content */}
				<div className="@container/main relative flex flex-1 flex-col gap-2 bg-gradient-to-b from-background via-background to-background/80">
					<div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
						{isLoading && <DashboardLoadingState />}

						{isError && (
							<DashboardErrorState
								message={error instanceof Error ? error.message : "Unable to load market overview."}
								onRetry={() => void refetch()}
								isRefreshing={isFetching}
							/>
						)}

						{!isLoading && !isError && data && (
							<>
								{/* Stat cards */}
								<div className="grid grid-cols-1 gap-4 px-4 lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
									<StatCard
										label="Tracked universe"
										value="Top 10"
										badge="By market cap"
										footer="Large-cap public assets"
										footerDetail={data.ranking_basis}
										icon={<BarChart3 className="size-4" />}
										trend="up"
									/>
									<StatCard
										label="Lead asset"
										value={data.featured_assets[0]?.symbol ?? "N/A"}
										badge={
											data.featured_assets[0]
												? `${data.featured_assets[0].price_change_percentage_24h >= 0 ? "+" : ""}${data.featured_assets[0].price_change_percentage_24h.toFixed(2)}%`
												: "—"
										}
										footer={data.featured_assets[0]?.name ?? "Hero chart and tape"}
										footerDetail="Featured in the main chart"
										icon={<Activity className="size-4" />}
										trend={data.featured_assets[0]?.price_change_percentage_24h >= 0 ? "up" : "down"}
									/>
									<StatCard
										label="Last refresh"
										value={formatTimestamp(data.generated_at)}
										badge="On-demand"
										footer="Market snapshot"
										footerDetail={new Date(data.generated_at).toLocaleDateString()}
								icon={<Clock3 className="size-4" />}
								trend="up"
							/>
							<StatCard
								label="Watchlist"
								value={isAuthenticated ? "Ready" : "Sign in"}
								badge="Core feature"
								footer="Track your own assets"
								footerDetail="Pin coins and build personal lists"
								icon={<LockKeyhole className="size-4" />}
								trend="up"
								href={isAuthenticated ? "/dashboard" : "/sign-in"}
								interactive
								ctaLabel={isAuthenticated ? "Open your workspace" : "Unlock watchlists"}
							/>
						</div>

								{/* Hero chart */}
								<div className="px-4 lg:px-6">
									<HeroChart featured={data.featured_assets[0]} chart={data.hero_chart ?? []} />
								</div>

								{/* Top assets + Activity */}
								<div className="grid gap-4 px-4 lg:px-6 xl:grid-cols-[minmax(0,1.3fr)_420px]">
									<Card className="border-border/30 bg-card/50 backdrop-blur-sm">
										<CardHeader>
											<CardTitle className="flex items-center gap-2">
												<BarChart3 className="size-5 text-muted-foreground/60" />
												Top assets
											</CardTitle>
											<CardDescription className="pb-2">
												Large-cap crypto assets tracked in this public overview.
											</CardDescription>
										</CardHeader>
										<CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-3">
											{data.featured_assets.map((card) => (
												<FeaturedAssetCard key={card.id} card={card} />
											))}
										</CardContent>
									</Card>
									<ActivityCard
										generatedAt={data.generated_at}
										source={data.source}
										rankingBasis={data.ranking_basis}
										gainers={data.top_gainers}
										losers={data.top_losers}
									/>
								</div>

								{/* Movers + Coin board */}
								<div className="grid gap-4 px-4 lg:px-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
									<MoversTable gainers={data.top_gainers} losers={data.top_losers} />
									<CoinBoard cards={data.featured_assets.slice(0, 3)} />
								</div>
							</>
						)}
					</div>
				</div>
			</SidebarInset>
		</>
	);
}

// ─── Stat card (matches shadcn dashboard SectionCards style) ───────────────

function StatCard({
	label,
	value,
	badge,
	footer,
	footerDetail,
	icon,
	trend,
	href,
	interactive = false,
	ctaLabel,
}: {
	label: string;
	value: string;
	badge: string;
	footer: string;
	footerDetail: string;
	icon: React.ReactNode;
	trend: "up" | "down";
	href?: string;
	interactive?: boolean;
	ctaLabel?: string;
}) {
	const Icon = trend === "up" ? TrendingUp : TrendingDown;
	const badgeColor =
		trend === "up"
			? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900/50"
			: "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-900/50";

	const content = (
		<Card
			className={cn(
				"@container/card border-border/30 bg-card/50 backdrop-blur-sm transition-colors duration-200",
				interactive && "border-emerald-500/15 bg-card/70 group-hover:border-emerald-500/30 group-hover:bg-card/90",
			)}>
			<CardHeader
				className={cn(
					interactive && "transition-transform duration-200 ease-out group-hover:translate-y-[-1px]",
				)}>
				<div className="flex items-center gap-2">
					<div
						className={cn(
							"rounded-lg bg-muted/60 p-2 text-muted-foreground/70 transition-colors duration-200",
							interactive && "group-hover:bg-emerald-500/10 group-hover:text-emerald-500",
						)}>
						{icon}
					</div>
					<CardDescription className="text-xs">{label}</CardDescription>
				</div>
				<CardTitle className="text-2xl font-bold tabular-nums @[250px]/card:text-3xl mt-3">{value}</CardTitle>
				<CardAction>
					<Badge variant="outline" className={cn("gap-1", badgeColor)}>
						<Icon
							className={cn(
								"size-3",
								trend === "up"
									? "text-emerald-600 dark:text-emerald-400"
									: "text-amber-600 dark:text-amber-400",
							)}
						/>
						<span className="text-xs">{badge}</span>
					</Badge>
				</CardAction>
			</CardHeader>
			<CardFooter className="flex-col items-start gap-1.5 text-sm">
				<div className="flex items-center gap-2 font-medium">
					{footer}
					{interactive ? (
						<ArrowRight className="size-4 text-emerald-600 transition-transform duration-200 ease-out group-hover:translate-x-0.5 dark:text-emerald-400" />
					) : (
						<Icon
							className={cn(
								"size-4",
								trend === "up" ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400",
							)}
						/>
					)}
				</div>
				<div className="text-xs text-muted-foreground">{footerDetail}</div>
				{interactive && ctaLabel ? (
					<div className="mt-3 flex items-center gap-2 text-xs font-medium text-emerald-600 transition-colors duration-200 group-hover:text-emerald-500 dark:text-emerald-400">
						<span>{ctaLabel}</span>
						<ArrowRight className="size-3.5 transition-transform duration-200 ease-out group-hover:translate-x-0.5" />
					</div>
				) : null}
			</CardFooter>
		</Card>
	);

	if (!interactive || !href) {
		return content;
	}

	return (
		<Link
			href={href}
			className="group block rounded-xl outline-none transition-all duration-200 ease-out hover:-translate-y-0.5 hover:shadow-[0_16px_32px_-24px_rgba(16,185,129,0.32)] focus-visible:ring-2 focus-visible:ring-primary/40">
			<div className="rounded-xl bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.10),transparent_38%)]">
				{content}
			</div>
		</Link>
	);
}

// ─── Hero chart ────────────────────────────────────────────────────────────

const heroChartConfig = {
	price: { label: "Price", color: "hsl(var(--primary))" },
} satisfies ChartConfig;

function HeroChart({ featured, chart }: { featured?: FeaturedCard; chart: MarketChartPoint[] }) {
	if (!featured) {
		return (
			<Card className="border-dashed border-border/30 bg-card/50">
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<LineChart className="size-5 text-muted-foreground/60" />
						Market snapshot unavailable
					</CardTitle>
					<CardDescription>
						Featured quote modules will appear here as soon as market data is available.
					</CardDescription>
				</CardHeader>
			</Card>
		);
	}

	const isPositive = featured.price_change_percentage_24h >= 0;
	const chartData = chart.map((p) => ({ time: p.time, price: p.price }));

	return (
		<Card className="border-border/30 bg-gradient-to-br from-card to-card/50 backdrop-blur-sm">
			<CardHeader>
				<div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
					<div className="flex items-start gap-4">
						<LogoMark symbol={featured.symbol} logoUrl={featured.image_url} />
						<div>
							<CardDescription className="text-xs uppercase tracking-wider">Lead asset</CardDescription>
							<CardTitle className="mt-1 text-2xl font-bold flex items-center gap-2">
								{featured.symbol}
								<BarChart3 className="size-5 text-muted-foreground/50" />
							</CardTitle>
							<p className="mt-1 text-sm text-muted-foreground">
								{featured.name} · Rank #{featured.market_cap_rank}
								{featured.categories[0] ? ` · ${featured.categories[0]}` : ""}
							</p>
						</div>
					</div>

					<div
						className={cn(
							"rounded-xl border px-5 py-4 sm:text-right backdrop-blur-sm",
							isPositive
								? "bg-emerald-500/8 border-emerald-300/20 dark:border-emerald-800/30"
								: "bg-amber-500/8 border-amber-300/20 dark:border-amber-800/30",
						)}>
						<p className="text-xs uppercase tracking-wider text-muted-foreground">Current price</p>
						<p className="mt-1 text-3xl font-bold tabular-nums">${formatPrice(featured.current_price)}</p>
						<p
							className={cn(
								"mt-0.5 text-sm font-semibold",
								isPositive ? "text-emerald-700 dark:text-emerald-400" : "text-amber-700 dark:text-amber-400",
							)}>
							{formatSignedPrice(featured.price_change_24h)} ({formatSignedPercent(featured.price_change_percentage_24h)})
						</p>
					</div>
				</div>
			</CardHeader>
			<CardContent className="pt-2">
				{chartData.length > 0 ? (
					<ChartContainer config={heroChartConfig} className="h-[200px] w-full">
						<AreaChart data={chartData} margin={{ left: 10, right: 4, top: 4, bottom: 0 }}>
							<defs>
								<linearGradient id="heroGrad" x1="0" y1="0" x2="0" y2="1">
									<stop
										offset="5%"
										stopColor={isPositive ? "hsl(142.71deg 76.46% 36.27%)" : "hsl(38.63deg 92.16% 50.39%)"}
										stopOpacity={0.15}
									/>
									<stop
										offset="95%"
										stopColor={isPositive ? "hsl(142.71deg 76.46% 36.27%)" : "hsl(38.63deg 92.16% 50.39%)"}
										stopOpacity={0}
									/>
								</linearGradient>
							</defs>
							<CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-muted-foreground/20" />
							<XAxis
								dataKey="time"
								tickLine={false}
								axisLine={false}
								tickMargin={8}
								minTickGap={40}
								tickFormatter={(v: string) => {
									const d = new Date(v);
									return isNaN(d.getTime())
										? v
										: d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
								}}
							/>
							<YAxis
								tickLine={false}
								axisLine={false}
								tickMargin={8}
								width={72}
								tickFormatter={(v: number) => `$${v.toFixed(0)}`}
							/>
							<ChartTooltip
								cursor={false}
								content={
									<ChartTooltipContent
										labelFormatter={(v: unknown) => {
											const d = new Date(v as string);
											return isNaN(d.getTime())
												? String(v)
												: d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
										}}
										formatter={(v) => [`$${Number(v).toFixed(2)}`, "Price"]}
									/>
								}
							/>
							<Area
								dataKey="price"
								type="natural"
								fill="url(#heroGrad)"
								stroke={isPositive ? "hsl(142.71deg 76.46% 36.27%)" : "hsl(38.63deg 92.16% 50.39%)"}
								strokeWidth={2}
							/>
						</AreaChart>
					</ChartContainer>
				) : (
					<div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed border-border/30 text-sm text-muted-foreground/60">
						<BarChart3 className="size-4 mr-2" />
						Chart unavailable
					</div>
				)}

				<div className="mt-4 grid gap-3 sm:grid-cols-4">
					<MetricTile label="Market cap" value={`$${formatCompactNumber(featured.market_cap)}`} />
					<MetricTile label="Volume" value={`$${formatCompactNumber(featured.total_volume)}`} />
					<MetricTile label="24h high" value={`$${formatPrice(featured.high_24h)}`} />
					<MetricTile label="24h low" value={`$${formatPrice(featured.low_24h)}`} />
				</div>
			</CardContent>
		</Card>
	);
}

// ─── Featured asset card ───────────────────────────────────────────────────

function FeaturedAssetCard({ card }: { card: FeaturedCard }) {
	const isPositive = card.price_change_percentage_24h >= 0;
	return (
		<div className="rounded-lg border border-border/30 bg-card/60 p-3 transition-colors hover:bg-card/80 backdrop-blur-sm">
			<div className="flex items-start justify-between gap-2">
				<div className="flex items-center gap-2">
					<LogoMark symbol={card.symbol} logoUrl={card.image_url} small />
					<div>
						<p className="text-sm font-bold">{card.symbol}</p>
						<p className="line-clamp-1 text-xs text-muted-foreground/70">{card.name}</p>
					</div>
				</div>
				<Badge
					variant="outline"
					className={cn(
						"text-xs",
						isPositive
							? "bg-emerald-500/12 text-emerald-700 dark:text-emerald-300 border-emerald-300/20 dark:border-emerald-800/30"
							: "bg-amber-500/12 text-amber-700 dark:text-amber-300 border-amber-300/20 dark:border-amber-800/30",
					)}>
					{formatSignedPercent(card.price_change_percentage_24h)}
				</Badge>
			</div>

			<div className="mt-3">
				<p className="text-xl font-bold tabular-nums">${formatPrice(card.current_price)}</p>
				<p
					className={cn(
						"text-sm font-medium",
						isPositive ? "text-emerald-700 dark:text-emerald-400" : "text-amber-700 dark:text-amber-400",
					)}>
					{formatSignedPrice(card.price_change_24h)}
				</p>
			</div>

			<div className="mt-3 grid grid-cols-2 gap-2 text-xs">
				<div>
					<p className="text-muted-foreground">Market cap</p>
					<p className="font-medium">{formatCompactNumber(card.market_cap)}</p>
				</div>
				<div>
					<p className="text-muted-foreground">24h volume</p>
					<p className="font-medium">{formatCompactNumber(card.total_volume)}</p>
				</div>
			</div>
		</div>
	);
}

// ─── Activity card ─────────────────────────────────────────────────────────

function ActivityCard({
	generatedAt,
	source,
	rankingBasis,
	gainers,
	losers,
}: {
	generatedAt: string;
	source: string;
	rankingBasis: string;
	gainers: MarketMover[];
	losers: MarketMover[];
}) {
	const best = gainers[0];
	const worst = losers[0];

	return (
		<Card className="border-border/30 bg-card/50 backdrop-blur-sm">
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<Activity className="size-5 text-muted-foreground/60" />
					Activity
				</CardTitle>
				<CardDescription className="pb-2">Operational context and tape leaders.</CardDescription>
			</CardHeader>
			<CardContent className="space-y-4">
				<div className="grid gap-3">
					<InfoTile label="Source" value={source} />
					<InfoTile label="Updated" value={new Date(generatedAt).toLocaleString("en-GB")} />
					<InfoTile label="Universe" value={rankingBasis} />
				</div>

				<Separator className="bg-border/20" />

				<div className="space-y-3">
					<p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Tape leaders</p>
					{best && (
						<div className="flex items-center justify-between">
							<div className="flex items-center gap-2">
								<TrendingUp className="size-4 text-emerald-700 dark:text-emerald-400" />
								<div>
									<p className="text-sm font-medium">{best.symbol}</p>
									<p className="text-xs text-muted-foreground">{best.name}</p>
								</div>
							</div>
							<Badge
								variant="outline"
								className="bg-emerald-500/12 text-emerald-700 dark:text-emerald-300 border-emerald-300/20 dark:border-emerald-800/30">
								{formatSignedPercent(best.price_change_percentage_24h)}
							</Badge>
						</div>
					)}
					{worst && (
						<div className="flex items-center justify-between">
							<div className="flex items-center gap-2">
								<TrendingDown className="size-4 text-amber-700 dark:text-amber-300" />
								<div>
									<p className="text-sm font-medium">{worst.symbol}</p>
									<p className="text-xs text-muted-foreground/70">{worst.name}</p>
								</div>
							</div>
							<Badge
								variant="outline"
								className="bg-amber-500/12 text-amber-700 dark:text-amber-300 border-amber-300/20 dark:border-amber-800/30">
								{formatSignedPercent(worst.price_change_percentage_24h)}
							</Badge>
						</div>
					)}
				</div>
			</CardContent>
		</Card>
	);
}

// ─── Movers table ──────────────────────────────────────────────────────────

function MoversTable({ gainers, losers }: { gainers: MarketMover[]; losers: MarketMover[] }) {
	const rows = [
		...gainers.slice(0, 4).map((item) => ({ ...item, side: "Gainer" as const })),
		...losers.slice(0, 4).map((item) => ({ ...item, side: "Loser" as const })),
	];

	return (
		<Card className="border-border/30 bg-card/50 backdrop-blur-sm">
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<TrendingUp className="size-5 text-muted-foreground/60" />
					Top movers
				</CardTitle>
				<CardDescription className="pb-2">Daily winners and losers from the large-cap universe.</CardDescription>
			</CardHeader>
			<CardContent>
				<div className="overflow-hidden rounded-lg border border-border/30">
					<table className="w-full text-sm">
						<thead>
							<tr className="border-b border-border/20 bg-muted/20 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground/70">
								<th className="px-4 py-3">Side</th>
								<th className="px-4 py-3">Symbol</th>
								<th className="px-4 py-3 text-right">Price</th>
								<th className="px-4 py-3 text-right">Change</th>
							</tr>
						</thead>
						<tbody>
							{rows.map((row) => (
								<tr
									key={`${row.side}-${row.symbol}`}
									className="border-b border-border/20 transition-colors last:border-0 hover:bg-muted/30">
									<td className="px-4 py-3">
										<Badge
											variant="outline"
											className={cn(
												"text-xs",
												row.side === "Gainer"
													? "bg-emerald-500/12 text-emerald-700 dark:text-emerald-300 border-emerald-300/20 dark:border-emerald-800/30"
													: "bg-amber-500/12 text-amber-700 dark:text-amber-300 border-amber-300/20 dark:border-amber-800/30",
											)}>
											{row.side}
										</Badge>
									</td>
									<td className="px-4 py-3">
										<p className="font-semibold">{row.symbol}</p>
										<p className="truncate text-xs text-muted-foreground/70">{row.name}</p>
									</td>
									<td className="px-4 py-3 text-right font-medium tabular-nums">
										${formatPrice(row.current_price)}
									</td>
									<td
										className={cn(
											"px-4 py-3 text-right font-semibold tabular-nums",
											row.price_change_24h >= 0
												? "text-emerald-700 dark:text-emerald-300"
												: "text-amber-700 dark:text-amber-300",
										)}>
										{formatSignedPercent(row.price_change_percentage_24h)}
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</CardContent>
		</Card>
	);
}

// ─── Coin board ─────────────────────────────────────────────────────────

function CoinBoard({ cards }: { cards: FeaturedCard[] }) {
	return (
		<Card className="border-border/30 bg-card/50 backdrop-blur-sm">
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<BriefcaseBusiness className="size-5 text-muted-foreground/60" />
					Coin board
				</CardTitle>
				<CardDescription className="pb-2">Coin context for highlighted assets.</CardDescription>
			</CardHeader>
			<CardContent className="space-y-3">
				{cards.map((card) => (
					<div
						key={card.symbol}
						className="flex items-center justify-between gap-3 rounded-lg border border-border/30 bg-card/60 p-2.5 transition-colors hover:bg-card/80 backdrop-blur-sm">
						<div className="flex items-center gap-3">
							<LogoMark symbol={card.symbol} logoUrl={card.image_url} small />
							<div>
								<p className="text-sm font-semibold">{card.symbol}</p>
								<p className="text-xs text-muted-foreground/70">{card.categories[0] || card.name}</p>
							</div>
						</div>
						<div className="flex items-center gap-2">
							<Badge
								variant="outline"
								className={cn(
									"text-xs",
									card.price_change_24h >= 0
										? "bg-emerald-500/12 text-emerald-700 dark:text-emerald-300 border-emerald-300/20 dark:border-emerald-800/30"
										: "bg-amber-500/12 text-amber-700 dark:text-amber-300 border-amber-300/20 dark:border-amber-800/30",
								)}>
								{formatSignedPercent(card.price_change_percentage_24h)}
							</Badge>
							{card.homepage && (
								<a
									href={card.homepage}
									target="_blank"
									rel="noreferrer"
									className="text-muted-foreground hover:text-foreground">
									<ExternalLink className="size-3.5" />
								</a>
							)}
						</div>
					</div>
				))}
			</CardContent>
		</Card>
	);
}

// ─── Watchlist card ────────────────────────────────────────────────────────

// ─── Loading / Error states ────────────────────────────────────────────────

function DashboardLoadingState() {
	return (
		<div className="flex flex-1 flex-col items-center justify-center min-h-[400px]">
			<div className="flex flex-col items-center gap-3">
				<Spinner className="size-6 text-muted-foreground" />
				<div className="flex flex-col items-center gap-0.5">
					<p className="text-sm font-medium text-foreground">Loading market data</p>
					<p className="text-xs text-muted-foreground/70">Please wait...</p>
				</div>
			</div>
		</div>
	);
}

function DashboardErrorState({
	message,
	onRetry,
	isRefreshing,
}: {
	message: string;
	onRetry: () => void;
	isRefreshing: boolean;
}) {
	return (
		<div className="px-4 lg:px-6">
			<Card className="border-dashed border-destructive/30 bg-card/50 backdrop-blur-sm">
				<CardContent className="flex flex-col gap-4 py-6 sm:flex-row sm:items-center sm:justify-between">
					<div className="flex items-start gap-4">
						<div className="inline-flex size-12 items-center justify-center rounded-full border border-destructive/15 bg-destructive/5">
							<CircleAlert
								className={cn("size-6 text-destructive/60", isRefreshing && "animate-pulse")}
								strokeWidth={1.5}
							/>
						</div>
						<div className="space-y-1.5">
							<p className="text-sm font-semibold text-foreground">
								{isRefreshing ? "Refreshing market data" : "Market data temporarily unavailable"}
							</p>
							<p className="text-sm text-muted-foreground">
								{isRefreshing
									? "Attempting to restore the public crypto snapshot."
									: message.includes("403")
										? "This provider plan cannot return the requested market data right now."
										: message || "The dashboard shell is still available while the data feed recovers."}
							</p>
							<p className="text-xs text-muted-foreground/70">
								Navigation and dashboard layout remain available during provider issues.
							</p>
						</div>
					</div>
					<Button onClick={onRetry} disabled={isRefreshing} className="gap-2 self-start sm:self-center">
						{isRefreshing ? (
							<>
								<RefreshCw className="size-4 animate-spin" />
								Checking...
							</>
						) : (
							<>
								<RefreshCw className="size-4" />
								Try again
							</>
						)}
					</Button>
				</CardContent>
			</Card>
		</div>
	);
}

// ─── Small primitives ──────────────────────────────────────────────────────

function MetricTile({ label, value }: { label: string; value: string }) {
	return (
		<div className="rounded-lg border border-border/30 bg-card/60 px-4 py-3 backdrop-blur-sm">
			<p className="text-xs uppercase tracking-wider text-muted-foreground/70">{label}</p>
			<p className="mt-1.5 text-base font-bold tabular-nums">{value}</p>
		</div>
	);
}

function InfoTile({ label, value }: { label: string; value: string }) {
	return (
		<div className="rounded-lg border border-border/30 bg-card/60 px-4 py-3 backdrop-blur-sm">
			<div className="flex items-start justify-between gap-3">
				<p className="text-xs uppercase tracking-wider text-muted-foreground/70">{label}</p>
				<Badge variant="outline" className="shrink-0 text-[10px] text-muted-foreground/70">
					Live
				</Badge>
			</div>
			<p className="mt-2 text-sm font-medium leading-snug text-foreground/90">{value}</p>
		</div>
	);
}

function LogoMark({ symbol, logoUrl, small = false }: { symbol: string; logoUrl?: string; small?: boolean }) {
	const sz = small ? "size-9 rounded-lg text-xs" : "size-12 rounded-xl text-sm";

	if (logoUrl) {
		return (
			<div className={cn("overflow-hidden border border-border/30 bg-card/60 backdrop-blur-sm", sz)}>
				<img src={logoUrl} alt={`${symbol} logo`} className="h-full w-full object-contain p-1.5" />
			</div>
		);
	}

	return (
		<div
			className={cn(
				"flex items-center justify-center border border-border/30 bg-muted/40 font-bold text-muted-foreground/70",
				sz,
			)}>
			{symbol.slice(0, 2)}
		</div>
	);
}

// ─── Formatters ────────────────────────────────────────────────────────────

function formatPrice(value: number) {
	return value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatSignedPrice(value: number) {
	return `${value >= 0 ? "+" : "-"}$${formatPrice(Math.abs(value))}`;
}

function formatSignedPercent(value: number) {
	const abs = Math.abs(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
	return `${value >= 0 ? "+" : "-"}${abs}%`;
}

function formatCompactNumber(value: number) {
	return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

function formatTimestamp(value: string) {
	return new Date(value).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}
