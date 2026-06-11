"use client";

import * as React from "react";
import Link from "next/link";
import { startTransition, useDeferredValue } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { format, isSameDay } from "date-fns";
import type { DateRange } from "react-day-picker";
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
	ArrowLeft,
	CalendarClock,
	Check,
	CheckCheck,
	Coins,
	LoaderCircle,
	Newspaper,
	Plus,
	Search,
	Sparkles,
	TrendingDown,
	TrendingUp,
} from "lucide-react";

import { isPriceScenario, type TriggerMode } from "@/features/alerts/lib/alert-builder";
import { AppSidebar } from "@/features/market-dashboard/components/app-sidebar";
import {
	getListAlertsAlertsGetQueryKey,
	useCreateAlertAlertsPost,
	useListAlertsAlertsGet,
	useUpdateAlertAlertsAlertIdPut,
} from "@/src/api/generated/alerts/alerts";
import type { AlertResponse } from "@/src/api/generated/models/alertResponse";
import type { CreateAlertRequestScenario } from "@/src/api/generated/models/createAlertRequestScenario";
import type { CryptoChartPointResponse } from "@/src/api/generated/models/cryptoChartPointResponse";
import type { WatchlistAssetResponse } from "@/src/api/generated/models/watchlistAssetResponse";
import type { WatchlistAssetSearchResult } from "@/src/api/generated/models/watchlistAssetSearchResult";
import {
	getGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGetQueryKey,
	getGetStarredWatchlistWatchlistsStarredGetQueryKey,
	useAddStarredWatchlistAssetWatchlistsStarredAssetsPost,
	useGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGet,
	useGetStarredWatchlistWatchlistsStarredGet,
	useSearchWatchlistAssetsWatchlistsAssetsSearchGet,
} from "@/src/api/generated/watchlists/watchlists";
import { Badge } from "@/shared/components/ui/badge";
import {
	Breadcrumb,
	BreadcrumbItem,
	BreadcrumbLink,
	BreadcrumbList,
	BreadcrumbPage,
} from "@/shared/components/ui/breadcrumb";
import { Button } from "@/shared/components/ui/button";
import { Calendar } from "@/shared/components/ui/calendar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { ScrollArea } from "@/shared/components/ui/scroll-area";
import { Separator } from "@/shared/components/ui/separator";
import { SidebarInset, SidebarTrigger } from "@/shared/components/ui/sidebar";
import { Skeleton } from "@/shared/components/ui/skeleton";
import {
	Stepper,
	StepperContent,
	StepperDescription,
	StepperIndicator,
	StepperItem,
	StepperNav,
	StepperPanel,
	StepperSeparator,
	StepperTitle,
	StepperTrigger,
} from "@/shared/components/reui/stepper";
import { cn } from "@/shared/lib/utils";

type ChartScope = "1D" | "1W" | "1M";
type AlertTimeBehavior = "one_time" | "daily_recurring";

const SCENARIOS: Array<{
	id: CreateAlertRequestScenario;
	title: string;
	description: string;
	icon: typeof TrendingUp;
}> = [
	{
		id: "price_above",
		title: "Price above",
		description: "Alert when the market breaks through your upside target.",
		icon: TrendingUp,
	},
	{
		id: "price_below",
		title: "Price below",
		description: "Alert when price slips under the support level you care about.",
		icon: TrendingDown,
	},
	{
		id: "coin_news",
		title: "News",
		description: "Alert as soon as a fresh article lands for this coin.",
		icon: Newspaper,
	},
];

const STEPS = [
	{ step: 1, title: "Coin", description: "Choose from watchlist" },
	{ step: 2, title: "Scenario", description: "Pick one clear trigger" },
	{ step: 3, title: "Timing", description: "Set alert duration" },
	{ step: 4, title: "Configure", description: "Set the final alert" },
] as const;

function formatCurrency(value: number): string {
	return new Intl.NumberFormat("en-US", {
		style: "currency",
		currency: "USD",
		maximumFractionDigits: value >= 1000 ? 0 : 2,
	}).format(value);
}

function formatPercent(value: number): string {
	return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatChartTick(value: string): string {
	return new Intl.DateTimeFormat("en-US", {
		month: "short",
		day: "numeric",
	}).format(new Date(value));
}

function formatChartTooltip(value: string): string {
	return new Intl.DateTimeFormat("en-US", {
		month: "short",
		day: "numeric",
		hour: "numeric",
		minute: "2-digit",
	}).format(new Date(value));
}

function formatShortDate(value: Date): string {
	return format(value, "MMM d, yyyy");
}

function formatDateFieldValue(value?: Date): string {
	return value ? format(value, "MMM d") : "Select";
}

function getScopeChartData(chart: CryptoChartPointResponse[], scope: ChartScope): CryptoChartPointResponse[] {
	if (chart.length === 0) {
		return [];
	}

	const timestamps = chart.map((point) => Date.parse(point.time));
	const hasValidTimestamps = timestamps.every((value) => Number.isFinite(value));
	if (!hasValidTimestamps) {
		if (scope === "1D") {
			return chart.slice(-Math.max(8, Math.ceil(chart.length / 7)));
		}
		return chart;
	}

	const lastTimestamp = timestamps.at(-1) ?? 0;
	const hoursByScope: Record<ChartScope, number> = {
		"1D": 24,
		"1W": 24 * 7,
		"1M": 24 * 30,
	};
	const cutoff = lastTimestamp - hoursByScope[scope] * 60 * 60 * 1000;
	const filtered = chart.filter((point) => Date.parse(point.time) >= cutoff);

	if (filtered.length >= 2) {
		return filtered;
	}

	return scope === "1D" ? chart.slice(-Math.max(8, Math.ceil(chart.length / 7))) : chart;
}

function getProjectedPrice(params: {
	currentPrice: number;
	scenario: CreateAlertRequestScenario | null;
	triggerMode: TriggerMode;
	thresholdValue: number | null;
}): number | null {
	const { currentPrice, scenario, triggerMode, thresholdValue } = params;
	if (!scenario || !isPriceScenario(scenario) || !thresholdValue || thresholdValue <= 0 || currentPrice <= 0) {
		return null;
	}

	if (triggerMode === "currency") {
		return thresholdValue;
	}

	return currentPrice * (scenario === "price_above" ? 1 + thresholdValue / 100 : 1 - thresholdValue / 100);
}

function getScenarioTone(scenario: CreateAlertRequestScenario | null) {
	if (scenario === "price_above") {
		return {
			badge: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
			icon: "border-emerald-500/25 bg-emerald-500/12 text-emerald-300",
			line: "#10b981",
			fill: "from-emerald-500/20 via-emerald-500/8 to-transparent",
		};
	}
	if (scenario === "price_below") {
		return {
			badge: "border-rose-500/30 bg-rose-500/10 text-rose-300",
			icon: "border-rose-500/25 bg-rose-500/12 text-rose-300",
			line: "#f43f5e",
			fill: "from-rose-500/20 via-rose-500/8 to-transparent",
		};
	}
	return {
		badge: "border-sky-500/30 bg-sky-500/10 text-sky-300",
		icon: "border-sky-500/25 bg-sky-500/12 text-sky-300",
		line: "#38bdf8",
		fill: "from-sky-500/20 via-sky-500/8 to-transparent",
	};
}

function getScenarioLabel(scenario: CreateAlertRequestScenario | null): string {
	switch (scenario) {
		case "price_above":
			return "Price above";
		case "price_below":
			return "Price below";
		case "coin_news":
			return "News";
		default:
			return "Choose a scenario";
	}
}

function getTimeBehaviorLabel(timeBehavior: AlertTimeBehavior): string {
	return timeBehavior === "daily_recurring" ? "Daily recurring" : "One-time";
}

function getTimingPreview(params: {
	timeBehavior: AlertTimeBehavior;
	recurringStartDate?: Date;
	recurringEndDate?: Date;
}): string {
	const { timeBehavior, recurringStartDate, recurringEndDate } = params;
	if (timeBehavior === "one_time") {
		return "Runs once, then the alert pauses after it eventually triggers.";
	}
	if (recurringStartDate && recurringEndDate) {
		return `Can trigger multiple times from ${formatShortDate(recurringStartDate)} to ${formatShortDate(recurringEndDate)} whenever new eligible moves or articles appear.`;
	}
	return "Choose a start and end date for the recurring active window.";
}

function getPreviewText(params: {
	scenario: CreateAlertRequestScenario | null;
	triggerMode: TriggerMode;
	thresholdValue: number | null;
	projectedPrice: number | null;
}): string {
	const { scenario, triggerMode, thresholdValue, projectedPrice } = params;

	if (scenario === "coin_news") {
		return "Every new article for this coin will land in notification history once delivery work ships.";
	}

	if (!scenario || !isPriceScenario(scenario) || !thresholdValue) {
		return "Pick a direction and define the trigger to preview how this alert will behave.";
	}

	if (triggerMode === "percent" && projectedPrice) {
		return `${scenario === "price_above" ? "Moves up" : "Drops down"} ${thresholdValue}% from the captured baseline, targeting about ${formatCurrency(projectedPrice)}.`;
	}

	return `${scenario === "price_above" ? "Breaks above" : "Falls below"} ${formatCurrency(thresholdValue)}.`;
}

export function AlertsEditor({
	alertId,
	initialAssetId,
}: {
	alertId?: string;
	initialAssetId?: string;
}) {
	const router = useRouter();
	const queryClient = useQueryClient();
	const isEditing = Boolean(alertId);
	const [activeStep, setActiveStep] = React.useState(1);
	const [selectedAssetId, setSelectedAssetId] = React.useState<string | null>(null);
	const [scenario, setScenario] = React.useState<CreateAlertRequestScenario | null>(null);
	const [timeBehavior, setTimeBehavior] = React.useState<AlertTimeBehavior>("one_time");
	const [recurringRange, setRecurringRange] = React.useState<DateRange | undefined>(undefined);
	const [triggerMode, setTriggerMode] = React.useState<TriggerMode>("currency");
	const [thresholdInput, setThresholdInput] = React.useState("");
	const [chartScope, setChartScope] = React.useState<ChartScope>("1W");
	const [searchQuery, setSearchQuery] = React.useState("");
	const [formError, setFormError] = React.useState<string | null>(null);
	const [requestError, setRequestError] = React.useState<string | null>(null);
	const hydratedEditRef = React.useRef(false);
	const deferredSearchQuery = useDeferredValue(searchQuery.trim());

	const watchlistQuery = useGetStarredWatchlistWatchlistsStarredGet(undefined, {
		query: {
			staleTime: 30_000,
			retry: 1,
		},
	});
	const selectedAssetContextQuery = useGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGet(
		selectedAssetId ?? "",
		undefined,
		{
			query: {
				enabled: Boolean(selectedAssetId),
				retry: 1,
			},
		},
	);
	const assetSearchQuery = useSearchWatchlistAssetsWatchlistsAssetsSearchGet(
		{ q: deferredSearchQuery || "btc" },
		{
			query: {
				enabled: deferredSearchQuery.length > 0,
				staleTime: 30_000,
				retry: 1,
			},
		},
	);
	const alertsQuery = useListAlertsAlertsGet(undefined, {
		query: {
			enabled: isEditing,
			staleTime: 30_000,
			retry: 1,
		},
	});
	const addAssetMutation = useAddStarredWatchlistAssetWatchlistsStarredAssetsPost();
	const createAlertMutation = useCreateAlertAlertsPost();
	const updateAlertMutation = useUpdateAlertAlertsAlertIdPut();

	const watchlistAssets = watchlistQuery.data?.assets ?? [];
	const selectedAsset = React.useMemo(
		() => watchlistAssets.find((asset) => asset.asset_id === selectedAssetId) ?? null,
		[selectedAssetId, watchlistAssets],
	);
	const targetAlert = React.useMemo(
		() => alertsQuery.data?.items.find((item) => item.id === alertId) ?? null,
		[alertId, alertsQuery.data?.items],
	);

	React.useEffect(() => {
		if (!isEditing || hydratedEditRef.current || !targetAlert) {
			return;
		}

		hydratedEditRef.current = true;
		setSelectedAssetId(targetAlert.asset_id);
		setScenario(targetAlert.scenario);
		setTimeBehavior(targetAlert.time_behavior);
		setRecurringRange({
			from: targetAlert.recurring_start_date ? new Date(targetAlert.recurring_start_date) : undefined,
			to: targetAlert.recurring_end_date ? new Date(targetAlert.recurring_end_date) : undefined,
		});
		setTriggerMode(targetAlert.trigger_mode ?? "currency");
		setThresholdInput(typeof targetAlert.threshold_value === "number" ? String(targetAlert.threshold_value) : "");
		setActiveStep(4);
	}, [isEditing, targetAlert]);

	React.useEffect(() => {
		if (isEditing || selectedAssetId || !initialAssetId || watchlistAssets.length === 0) {
			return;
		}

		const contextualAsset = watchlistAssets.find((asset) => asset.asset_id === initialAssetId);
		if (!contextualAsset) {
			return;
		}

		setSelectedAssetId(contextualAsset.asset_id);
	}, [initialAssetId, isEditing, selectedAssetId, watchlistAssets]);

	const currentPrice = selectedAssetContextQuery.data?.summary.current_price ?? 0;
	const thresholdValue = thresholdInput.trim() ? Number(thresholdInput) : null;
	const projectedPrice = getProjectedPrice({
		currentPrice,
		scenario,
		triggerMode,
		thresholdValue,
	});
	const chartData = getScopeChartData(selectedAssetContextQuery.data?.chart ?? [], chartScope);
	const recurringStartDate = recurringRange?.from;
	const recurringEndDate =
		recurringRange?.from && recurringRange?.to && isSameDay(recurringRange.from, recurringRange.to)
			? recurringRange.to
			: recurringRange?.to;
	const hasValidTiming =
		timeBehavior === "one_time" || Boolean(recurringStartDate && recurringEndDate && recurringEndDate >= recurringStartDate);
	const maxUnlockedStep = hasValidTiming ? 4 : scenario ? 3 : selectedAssetId ? 2 : 1;
	const isSaving = createAlertMutation.isPending || updateAlertMutation.isPending;

	const handleSelectCoin = (assetId: string) => {
		startTransition(() => {
			setSelectedAssetId(assetId);
			setFormError(null);
			setRequestError(null);
			if (activeStep < 2) {
				setActiveStep(2);
			}
		});
	};

	const handleAddAsset = async (asset: WatchlistAssetSearchResult) => {
		setRequestError(null);

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
			setSelectedAssetId(asset.asset_id);
			setActiveStep(2);
		} catch (error) {
			setRequestError(error instanceof Error ? error.message : "Unable to add this coin right now.");
		}
	};

	const handleScenarioSelect = (nextScenario: CreateAlertRequestScenario) => {
		setScenario(nextScenario);
		setFormError(null);
		if (nextScenario === "coin_news") {
			setTriggerMode("currency");
			setThresholdInput("");
		}
		setActiveStep(3);
	};

	const handleTimeBehaviorSelect = (nextBehavior: AlertTimeBehavior) => {
		setTimeBehavior(nextBehavior);
		setFormError(null);
		if (nextBehavior === "one_time") {
			setRecurringRange(undefined);
		}
	};

	const handleRecurringRangeChange = (range: DateRange | undefined) => {
		setRecurringRange(range);
		setFormError(null);
	};

	const goToPreviousStep = () => {
		setFormError(null);
		setRequestError(null);
		setActiveStep((current) => Math.max(1, current - 1));
	};

	const goToNextStep = () => {
		if (activeStep === 1) {
			if (!selectedAssetId) {
				setFormError("Choose a coin from your watchlist first.");
				return;
			}
			setFormError(null);
			setActiveStep(2);
			return;
		}

		if (activeStep === 2) {
			if (!scenario) {
				setFormError("Pick one of the three alert scenarios first.");
				return;
			}
			setFormError(null);
			setActiveStep(3);
			return;
		}

		if (activeStep === 3) {
			if (timeBehavior === "daily_recurring" && (!recurringStartDate || !recurringEndDate)) {
				setFormError("Choose both a start date and an end date for the recurring window.");
				return;
			}
			setFormError(null);
			setActiveStep(4);
		}
	};

	const handleChartClick = (event: unknown) => {
		if (!scenario || !isPriceScenario(scenario) || currentPrice <= 0) {
			return;
		}

		const clickedPrice = (event as { activePayload?: Array<{ payload?: { price?: number } }> } | undefined)
			?.activePayload?.[0]?.payload?.price;

		if (typeof clickedPrice !== "number" || !Number.isFinite(clickedPrice) || clickedPrice <= 0) {
			return;
		}

		if (triggerMode === "currency") {
			setThresholdInput(clickedPrice.toFixed(clickedPrice >= 1000 ? 0 : 2));
			return;
		}

		const deltaPercent = Math.abs(((clickedPrice - currentPrice) / currentPrice) * 100);
		setThresholdInput(deltaPercent.toFixed(2));
	};

	const saveAlert = async () => {
		if (!selectedAsset) {
			setFormError("Choose a coin from your watchlist before saving.");
			setActiveStep(1);
			return;
		}

		if (!scenario) {
			setFormError("Pick one of the three alert scenarios first.");
			setActiveStep(2);
			return;
		}

		if (timeBehavior === "daily_recurring" && (!recurringStartDate || !recurringEndDate)) {
			setFormError("Choose both a start date and an end date for the recurring window.");
			setActiveStep(3);
			return;
		}

		if (scenario !== "coin_news" && (!thresholdValue || thresholdValue <= 0)) {
			setFormError("Enter a positive trigger value for this price alert.");
			setActiveStep(4);
			return;
		}

		setFormError(null);
		setRequestError(null);

		const payload = {
			asset_id: selectedAsset.asset_id,
			symbol: selectedAsset.symbol,
			name: selectedAsset.name,
			image_url: selectedAsset.image_url,
			scenario,
			time_behavior: timeBehavior,
			recurring_start_date: timeBehavior === "daily_recurring" && recurringStartDate ? format(recurringStartDate, "yyyy-MM-dd") : undefined,
			recurring_end_date: timeBehavior === "daily_recurring" && recurringEndDate ? format(recurringEndDate, "yyyy-MM-dd") : undefined,
			trigger_mode: scenario === "coin_news" ? undefined : triggerMode,
			threshold_value: scenario === "coin_news" ? undefined : (thresholdValue ?? undefined),
		};

		try {
			if (isEditing && alertId) {
				await updateAlertMutation.mutateAsync({ alertId, data: payload });
			} else {
				await createAlertMutation.mutateAsync({ data: payload });
			}

			await queryClient.invalidateQueries({ queryKey: getListAlertsAlertsGetQueryKey() });
			if (selectedAssetId) {
				await queryClient.invalidateQueries({
					queryKey:
						getGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGetQueryKey(selectedAssetId),
				});
			}
			router.push("/alerts");
		} catch (error) {
			setRequestError(error instanceof Error ? error.message : "Unable to save this alert right now.");
		}
	};

	const renderCoinStep = () => {
		if (watchlistQuery.isLoading || (isEditing && alertsQuery.isLoading && !hydratedEditRef.current)) {
			return (
				<div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
					<Skeleton className="h-[420px] rounded-3xl" />
					<Skeleton className="h-[420px] rounded-3xl" />
				</div>
			);
		}

		if (watchlistQuery.isError) {
			return (
				<InlineState
					title="Watchlist unavailable"
					description={
						watchlistQuery.error instanceof Error
							? watchlistQuery.error.message
							: "We could not load your saved coins right now."
					}
					actionLabel="Retry"
					onAction={() => void watchlistQuery.refetch()}
				/>
			);
		}

		if (isEditing && alertsQuery.isSuccess && !targetAlert) {
			return (
				<InlineState
					title="Alert not found"
					description="This alert could not be loaded. It may have been removed already."
					actionLabel="Back to alerts"
					href="/alerts"
				/>
			);
		}

		return (
			<div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)]">
				<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
					<CardHeader className="gap-3">
						<div className="flex items-center justify-between gap-3">
							<div>
								<CardTitle className="text-lg">Choose the coin</CardTitle>
								<CardDescription className="mt-1">
									Start from your watchlist so alerts stay anchored to the assets you already track.
								</CardDescription>
							</div>
							<Badge variant="secondary" className="gap-1.5 px-3 py-1.5">
								<Coins className="size-3.5 text-amber-400" />
								{watchlistAssets.length}
							</Badge>
						</div>
					</CardHeader>
					<CardContent className="space-y-4">
						{watchlistAssets.length > 0 && !selectedAssetId ? (
							<div className="rounded-3xl border border-dashed border-sky-500/25 bg-sky-500/5 px-4 py-3.5">
								<p className="text-sm font-medium text-foreground">Select one coin to unlock the next step</p>
								<p className="mt-1 text-sm leading-6 text-muted-foreground">
									The New alert flow starts in a neutral state, so nothing is chosen until you explicitly pick a saved coin.
								</p>
							</div>
						) : null}
						{watchlistAssets.length === 0 ? (
							<div className="rounded-3xl border border-dashed border-border/50 bg-background/40 px-6 py-12 text-center">
								<div className="mx-auto flex size-14 items-center justify-center rounded-full border border-border/50 bg-muted/30 text-muted-foreground">
									<Coins className="size-6" />
								</div>
								<p className="mt-5 text-lg font-semibold">Your watchlist is empty</p>
								<p className="mt-2 text-sm leading-6 text-muted-foreground">
									Add a coin below and it will become instantly available for this alert flow.
								</p>
							</div>
						) : (
							<div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
								{watchlistAssets.map((asset) => {
									const isActive = asset.asset_id === selectedAssetId;
									return (
										<button
											key={asset.asset_id}
											type="button"
											onClick={() => handleSelectCoin(asset.asset_id)}
											className={cn(
												"group rounded-2xl border px-4 py-4 text-left transition-all duration-200",
												isActive
													? "border-sky-500/60 bg-sky-500/10 shadow-[0_0_0_1px_rgba(56,189,248,0.18)]"
													: "border-border/40 bg-background/40 hover:border-sky-500/30 hover:bg-muted/30",
											)}>
											<div className="flex items-start justify-between gap-3">
												<div>
													<p className="text-sm font-semibold">{asset.symbol}</p>
													<p className="mt-1 text-sm text-muted-foreground">{asset.name}</p>
												</div>
												<span
													className={cn(
														"flex size-8 items-center justify-center rounded-full border transition",
														isActive
															? "border-sky-500/40 bg-sky-500 text-white"
															: "border-border/50 bg-muted/20 text-muted-foreground group-hover:border-sky-500/30",
													)}>
													{isActive ? <CheckCheck className="size-4" /> : <Plus className="size-4" />}
												</span>
											</div>
										</button>
									);
								})}
							</div>
						)}
					</CardContent>
				</Card>

				<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
					<CardHeader className="gap-3">
						<CardTitle className="flex items-center gap-2 text-lg">
							<span className="flex size-8 items-center justify-center rounded-full border border-sky-500/25 bg-sky-500/10 text-sky-300">
								<Search className="size-4" />
							</span>
							Add another coin
						</CardTitle>
						<CardDescription>
							Need something outside the current watchlist? Search and save it here without leaving the flow.
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="relative">
							<Search className="pointer-events-none absolute left-3 top-3.5 size-4 text-muted-foreground" />
							<Input
								value={searchQuery}
								onChange={(event) => setSearchQuery(event.target.value)}
								placeholder="Search BTC, ETH, Solana..."
								className="h-11 rounded-2xl border-border/40 bg-background/50 pl-10"
							/>
						</div>
						<ScrollArea className="h-[280px] rounded-2xl border border-border/40 bg-background/40">
							<div className="space-y-2 p-3">
								{deferredSearchQuery.length === 0 ? (
									<SearchHint />
								) : assetSearchQuery.isLoading ? (
									<SearchHint loading />
								) : assetSearchQuery.isError ? (
									<SearchHint
										message={
											assetSearchQuery.error instanceof Error
												? assetSearchQuery.error.message
												: "Search is unavailable right now."
										}
									/>
								) : assetSearchQuery.data?.items.length ? (
									assetSearchQuery.data.items.map((asset) => {
										const alreadySaved = watchlistAssets.some((item) => item.asset_id === asset.asset_id);
										return (
											<div
												key={asset.asset_id}
												className="flex items-center justify-between gap-3 rounded-2xl border border-border/40 bg-background/60 px-3 py-3">
												<div className="min-w-0">
													<p className="truncate text-sm font-semibold">{asset.symbol}</p>
													<p className="truncate text-sm text-muted-foreground">{asset.name}</p>
												</div>
												{alreadySaved ? (
													<Button
														type="button"
														variant="outline"
														size="sm"
														className="rounded-full"
														onClick={() => handleSelectCoin(asset.asset_id)}>
														Select
													</Button>
												) : (
													<Button
														type="button"
														variant="outline"
														size="sm"
														className="rounded-full"
														onClick={() => void handleAddAsset(asset)}
														disabled={addAssetMutation.isPending}>
														{addAssetMutation.isPending ? (
															<LoaderCircle className="size-4 animate-spin" />
														) : (
															<Plus className="size-4" />
														)}
														Add
													</Button>
												)}
											</div>
										);
									})
								) : (
									<SearchHint message="No coins matched this search yet." />
								)}
							</div>
						</ScrollArea>
					</CardContent>
				</Card>
			</div>
		);
	};

	const renderScenarioStep = () => (
		<div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)]">
			<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
				<CardHeader className="gap-3">
					<CardTitle className="text-lg">Choose the scenario</CardTitle>
					<CardDescription>
						Keep it simple: pick just one clear trigger for {selectedAsset?.name ?? "this coin"}.
					</CardDescription>
				</CardHeader>
				<CardContent className="grid gap-3 md:grid-cols-3">
					{SCENARIOS.map((item) => {
						const isActive = scenario === item.id;
						const Icon = item.icon;
						const tone = getScenarioTone(item.id);
						return (
							<button
								key={item.id}
								type="button"
								onClick={() => handleScenarioSelect(item.id)}
								className={cn(
									"rounded-3xl border p-5 text-left transition-all duration-200",
									isActive
										? "border-sky-500/50 bg-sky-500/10 shadow-[0_0_0_1px_rgba(56,189,248,0.18)]"
										: "border-border/40 bg-background/45 hover:border-sky-500/30 hover:bg-muted/30",
								)}>
								<span className={cn("flex size-11 items-center justify-center rounded-2xl border", tone.icon)}>
									<Icon className="size-5" />
								</span>
								<p className="mt-5 text-base font-semibold">{item.title}</p>
								<p className="mt-2 text-sm leading-6 text-muted-foreground">{item.description}</p>
							</button>
						);
					})}
				</CardContent>
			</Card>

			<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
				<CardHeader className="gap-3">
					<CardTitle className="text-lg">Current selection</CardTitle>
					<CardDescription>
						The rest of the flow updates instantly as you move from one scenario to another.
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="rounded-3xl border border-border/40 bg-background/45 p-4">
						<p className="text-sm text-muted-foreground">Coin</p>
						<p className="mt-1 text-lg font-semibold">{selectedAsset?.name ?? "No coin selected"}</p>
						<p className="text-sm text-muted-foreground">
							{selectedAsset?.symbol ?? "Pick from watchlist first"}
						</p>
					</div>
					<div className="rounded-3xl border border-border/40 bg-background/45 p-4">
						<p className="text-sm text-muted-foreground">Scenario</p>
						<p className="mt-1 text-lg font-semibold">{getScenarioLabel(scenario)}</p>
						<p className="mt-2 text-sm leading-6 text-muted-foreground">
							Price flows open the chart-first authoring screen. News keeps the final step light and focused.
						</p>
					</div>
				</CardContent>
			</Card>
		</div>
	);

	const renderTimingStep = () => (
		<div className="grid gap-4 xl:grid-cols-[minmax(320px,0.9fr)_minmax(0,1.1fr)]">
			<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
				<CardHeader className="gap-3">
					<CardTitle className="text-lg">Choose alert timing</CardTitle>
					<CardDescription>
						Decide whether this alert should fire once or stay eligible throughout a fixed recurring window.
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid gap-3 md:grid-cols-2">
						{[
							{
								id: "one_time" as const,
								title: "One-time",
								description: "Best for a single price target or one news event that should pause after the first trigger.",
							},
							{
								id: "daily_recurring" as const,
								title: "Daily recurring",
								description: "Allows multiple fresh triggers inside a date range when new price moves or articles appear.",
							},
						].map((option) => {
							const isActive = timeBehavior === option.id;
							return (
								<button
									key={option.id}
									type="button"
									onClick={() => handleTimeBehaviorSelect(option.id)}
									className={cn(
										"rounded-3xl border p-5 text-left transition-all duration-200",
										isActive
											? "border-sky-500/50 bg-sky-500/10 shadow-[0_0_0_1px_rgba(56,189,248,0.18)]"
											: "border-border/40 bg-background/45 hover:border-sky-500/30 hover:bg-muted/30",
									)}>
									<span className="flex size-11 items-center justify-center rounded-2xl border border-sky-500/25 bg-sky-500/12 text-sky-300">
										<CalendarClock className="size-5" />
									</span>
									<p className="mt-5 text-base font-semibold">{option.title}</p>
									<p className="mt-2 text-sm leading-6 text-muted-foreground">{option.description}</p>
								</button>
							);
						})}
					</div>

					{timeBehavior === "daily_recurring" ? (
						<div>
							<div className="flex flex-wrap items-start gap-2.5 rounded-3xl border border-border/40 bg-background/45 px-4 py-3.5">
								<Badge variant="outline" className="rounded-full border-border/50 px-3 py-1.5">
									Start: {formatDateFieldValue(recurringStartDate)}
								</Badge>
								<Badge variant="outline" className="rounded-full border-border/50 px-3 py-1.5">
									End: {formatDateFieldValue(recurringEndDate)}
								</Badge>
								<p className="basis-full text-sm leading-6 text-muted-foreground">
									Inside this range, the alert stays active and can trigger again whenever a new qualifying move or article appears.
								</p>
							</div>
						</div>
					) : (
						<div className="rounded-3xl border border-border/40 bg-background/45 p-5">
							<p className="text-sm font-medium">One-time behavior</p>
							<p className="mt-2 text-sm leading-6 text-muted-foreground">
								This alert will stay active until its first future trigger, then pause immediately after that delivery.
							</p>
						</div>
					)}
				</CardContent>
			</Card>

			<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
				<CardHeader className="gap-3">
					<CardTitle className="text-lg">Recurring window</CardTitle>
					<CardDescription>
						{timeBehavior === "daily_recurring"
							? "Pick the calendar range in which this alert stays eligible for fresh recurring triggers."
							: "Switch to daily recurring if you want to open a calendar-based schedule window."}
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-3">
					{timeBehavior === "daily_recurring" ? (
						<>
							<div className="flex justify-center xl:justify-end">
								<p className="max-w-xl text-center text-sm text-muted-foreground xl:text-right">
									{getTimingPreview({ timeBehavior, recurringStartDate, recurringEndDate })}
								</p>
							</div>
							<div className="rounded-[28px] border border-border/40 bg-card/80 px-3 py-2 sm:px-4 sm:py-3">
								<Calendar
									mode="range"
									numberOfMonths={1}
									selected={recurringRange}
									onSelect={handleRecurringRangeChange}
									disabled={{ before: new Date() }}
									className="relative mx-auto w-fit max-w-full [--cell-size:2.75rem] sm:[--cell-size:3rem]"
									classNames={{
										root: "relative mx-auto w-fit",
										months: "flex w-fit",
										month: "w-fit min-w-0",
										nav: "absolute left-1/2 top-1 flex w-[calc(var(--cell-size)*7+1.5rem)] max-w-full -translate-x-1/2 items-center justify-between px-2",
										month_caption: "flex h-10 items-center justify-center px-12",
										weekday: "w-11 text-center text-[0.8rem] sm:w-12",
										week: "mt-2 flex w-fit gap-0",
									}}
								/>
							</div>
						</>
					) : (
						<div className="flex min-h-[380px] flex-col items-center justify-center rounded-[28px] border border-dashed border-border/40 bg-background/35 px-6 text-center">
							<div className="flex size-14 items-center justify-center rounded-full border border-border/50 bg-muted/30 text-muted-foreground">
								<CalendarClock className="size-5" />
							</div>
							<p className="mt-5 text-lg font-semibold">Calendar unlocks for recurring alerts</p>
							<p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
								Keep this alert one-time, or switch the timing mode to daily recurring when you need a date range.
							</p>
						</div>
					)}
				</CardContent>
			</Card>
		</div>
	);

	const renderPriceConfigurator = () => {
		const tone = getScenarioTone(scenario);

		if (selectedAssetContextQuery.isLoading) {
			return <Skeleton className="h-[560px] rounded-3xl" />;
		}

		if (selectedAssetContextQuery.isError) {
			return (
				<InlineState
					title="Price context unavailable"
					description={
						selectedAssetContextQuery.error instanceof Error
							? selectedAssetContextQuery.error.message
							: "We could not load chart data for this coin right now."
					}
					actionLabel="Retry"
					onAction={() => void selectedAssetContextQuery.refetch()}
				/>
			);
		}

		return (
			<div className="grid gap-4 xl:grid-cols-[minmax(0,1.22fr)_minmax(320px,0.78fr)]">
				<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
					<CardHeader className="gap-5">
						<div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
							<div>
								<div className="flex items-center gap-2">
									<Badge className={cn("border text-xs", tone.badge)}>{getScenarioLabel(scenario)}</Badge>
									<Badge variant="outline" className="border-border/50">
										{selectedAsset?.symbol}
									</Badge>
								</div>
								<CardTitle className="mt-3 text-xl">
									{selectedAssetContextQuery.data?.summary.name} at {formatCurrency(currentPrice)}
								</CardTitle>
								<CardDescription className="mt-2">
									Click anywhere on the chart to snap the trigger, or type an exact value beside the `% / $`
									toggle.
								</CardDescription>
							</div>
							<div className="inline-flex rounded-full border border-border/40 bg-background/55 p-1">
								{(["1D", "1W", "1M"] as ChartScope[]).map((scope) => (
									<button
										key={scope}
										type="button"
										onClick={() => setChartScope(scope)}
										className={cn(
											"rounded-full px-3 py-1.5 text-xs font-semibold transition",
											chartScope === scope
												? "bg-sky-500 text-white"
												: "text-muted-foreground hover:text-foreground",
										)}>
										{scope}
									</button>
								))}
							</div>
						</div>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className={cn("rounded-[28px] border border-border/40 bg-gradient-to-b p-4", tone.fill)}>
							<div className="mb-4 flex items-center justify-between gap-3">
								<div>
									<p className="text-sm text-muted-foreground">Live trigger preview</p>
									<p className="mt-1 text-lg font-semibold">
										{projectedPrice ? formatCurrency(projectedPrice) : "Choose a value"}
									</p>
								</div>
								<p className="max-w-[26ch] text-right text-xs leading-5 text-muted-foreground">
									`1D / 1W / 1M` adapts to the current market snapshot history available for this coin.
								</p>
							</div>
							<div className="h-[360px] w-full">
								{chartData.length > 0 ? (
									<ResponsiveContainer width="100%" height="100%">
										<AreaChart
											data={chartData}
											onClick={handleChartClick}
											margin={{ left: 8, right: 12, top: 12 }}>
											<defs>
												<linearGradient id="alerts-trigger-fill" x1="0" x2="0" y1="0" y2="1">
													<stop offset="0%" stopColor={tone.line} stopOpacity={0.35} />
													<stop offset="100%" stopColor={tone.line} stopOpacity={0} />
												</linearGradient>
											</defs>
											<CartesianGrid stroke="rgba(148,163,184,0.15)" vertical={false} />
											<XAxis
												dataKey="time"
												tickFormatter={formatChartTick}
												axisLine={false}
												tickLine={false}
												minTickGap={24}
												tick={{ fill: "rgba(148,163,184,0.8)", fontSize: 12 }}
											/>
											<YAxis
												axisLine={false}
												tickLine={false}
												width={88}
												tickFormatter={(value) => formatCurrency(Number(value))}
												tick={{ fill: "rgba(148,163,184,0.8)", fontSize: 12 }}
											/>
											<Tooltip
												contentStyle={{
													borderRadius: "18px",
													borderColor: "rgba(148,163,184,0.25)",
													backgroundColor: "rgba(10,14,20,0.96)",
												}}
												formatter={(value) => formatCurrency(Number(value))}
												labelFormatter={(value) => formatChartTooltip(String(value))}
											/>
											{projectedPrice ? (
												<ReferenceLine
													y={projectedPrice}
													stroke={tone.line}
													strokeDasharray="6 6"
													label={{
														value: `Trigger ${formatCurrency(projectedPrice)}`,
														position: "insideTopRight",
														fill: tone.line,
														fontSize: 12,
													}}
												/>
											) : null}
											<Area
												dataKey="price"
												type="monotone"
												stroke={tone.line}
												strokeWidth={2.4}
												fill="url(#alerts-trigger-fill)"
											/>
										</AreaChart>
									</ResponsiveContainer>
								) : (
									<div className="flex h-full items-center justify-center rounded-[24px] border border-dashed border-border/40 text-sm text-muted-foreground">
										Chart data is not available for this coin right now.
									</div>
								)}
							</div>
						</div>
					</CardContent>
				</Card>

				<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
					<CardHeader className="gap-3">
						<CardTitle className="text-lg">Trigger controls</CardTitle>
						<CardDescription>
							Keep the value simple. Switch the scope of the threshold without leaving the chart.
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-5">
						<div className="space-y-2">
							<p className="text-sm font-medium">Trigger value</p>
							<div className="flex items-center gap-3 rounded-2xl border border-border/40 bg-background/55 p-2">
								<Input
									inputMode="decimal"
									value={thresholdInput}
									onChange={(event) => setThresholdInput(event.target.value)}
									placeholder={triggerMode === "currency" ? "100000" : "12.5"}
									className="h-12 border-0 bg-transparent px-3 text-lg shadow-none focus-visible:ring-0"
								/>
								<div className="inline-flex rounded-full border border-border/40 bg-background/70 p-1">
									<button
										type="button"
										onClick={() => setTriggerMode("percent")}
										className={cn(
											"rounded-full px-3 py-2 text-sm font-semibold transition",
											triggerMode === "percent"
												? "bg-sky-500 text-white"
												: "text-muted-foreground hover:text-foreground",
										)}>
										%
									</button>
									<button
										type="button"
										onClick={() => setTriggerMode("currency")}
										className={cn(
											"rounded-full px-3 py-2 text-sm font-semibold transition",
											triggerMode === "currency"
												? "bg-sky-500 text-white"
												: "text-muted-foreground hover:text-foreground",
										)}>
										$
									</button>
								</div>
							</div>
						</div>

						<div className="rounded-3xl border border-border/40 bg-background/45 p-4">
							<p className="text-sm text-muted-foreground">Live interpretation</p>
							<p className="mt-2 text-base font-semibold">
								{getPreviewText({ scenario, triggerMode, thresholdValue, projectedPrice })}
							</p>
							{triggerMode === "percent" ? (
								<p className="mt-3 text-sm leading-6 text-muted-foreground">
									The backend captures the current market price as the baseline when you save this alert.
								</p>
							) : (
								<p className="mt-3 text-sm leading-6 text-muted-foreground">
									The trigger line on the chart shows the exact price level your alert will watch.
								</p>
							)}
						</div>

						<div className="grid grid-cols-2 gap-3">
							<MetricTile
								label="24h move"
								value={formatPercent(selectedAssetContextQuery.data?.summary.price_change_percentage_24h ?? 0)}
							/>
							<MetricTile
								label="Market cap"
								value={formatCurrency(selectedAssetContextQuery.data?.summary.market_cap ?? 0)}
							/>
						</div>
					</CardContent>
				</Card>
			</div>
		);
	};

	const renderNewsConfigurator = () => (
		<div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(300px,0.9fr)]">
			<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
				<CardHeader className="gap-3">
					<div className="flex items-center gap-3">
						<span className="flex size-11 items-center justify-center rounded-2xl border border-sky-500/25 bg-sky-500/12 text-sky-300">
							<Newspaper className="size-5" />
						</span>
						<div>
							<CardTitle className="text-lg">News alert for {selectedAsset?.name}</CardTitle>
							<CardDescription className="mt-1">
								This is the lightest flow: no chart, no threshold, just fresh coin coverage.
							</CardDescription>
						</div>
					</div>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="rounded-3xl border border-border/40 bg-background/45 p-5">
						<p className="text-sm text-muted-foreground">What will happen</p>
						<p className="mt-2 text-lg font-semibold">Any new article for {selectedAsset?.symbol}</p>
						<p className="mt-3 text-sm leading-6 text-muted-foreground">
							The first delivery version targets notification history only, so this alert is ready for future
							dispatch without extra setup here.
						</p>
					</div>
				</CardContent>
			</Card>

			<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
				<CardHeader className="gap-3">
					<CardTitle className="text-lg">Quick preview</CardTitle>
					<CardDescription>Keep the final subscription setup light, then define its time behavior separately.</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<MetricTile label="Scenario" value="News" />
					<MetricTile label="Coin" value={selectedAsset?.symbol ?? "Not selected"} />
					<MetricTile label="Timing" value={getTimeBehaviorLabel(timeBehavior)} />
				</CardContent>
			</Card>
		</div>
	);

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
									<BreadcrumbLink asChild>
										<Link href="/alerts">Alerts</Link>
									</BreadcrumbLink>
								</BreadcrumbItem>
								<BreadcrumbItem>
									<BreadcrumbPage>{isEditing ? "Edit alert" : "New alert"}</BreadcrumbPage>
								</BreadcrumbItem>
							</BreadcrumbList>
						</Breadcrumb>
						<Badge variant="outline" className="hidden border-sky-500/20 text-sky-700 md:inline-flex">
							Guided flow
						</Badge>
						<div className="ml-auto">
							<Button asChild variant="ghost" size="sm" className="gap-2">
								<Link href="/alerts">
									<ArrowLeft className="size-4" />
									Back to alerts
								</Link>
							</Button>
						</div>
					</div>
				</header>

				<div className="flex h-[calc(100svh-4rem)] flex-col bg-background">
					<div className="@container/main min-h-0 flex-1 overflow-y-auto">
						<div className="flex flex-col gap-4 px-4 pt-4 lg:px-6 md:gap-6 md:pt-6">
							<section className="grid items-start gap-4 pb-24 xl:grid-cols-[minmax(0,1.35fr)_340px]">
								<Card className="flex min-h-[920px] flex-col border-border/30 bg-card/65 backdrop-blur-sm">
									<Stepper
										value={activeStep}
										onValueChange={(step) => {
											if (step <= maxUnlockedStep) {
												setActiveStep(step);
											}
										}}
										indicators={{
											completed: <Check className="size-3.5" />,
											active: <span className="text-xs font-semibold">•</span>,
											loading: <LoaderCircle className="size-3.5 animate-spin" />,
										}}
										className="flex min-h-0 flex-1 flex-col">
										<CardHeader className="shrink-0 gap-5 border-b border-border/30 pb-6">
											<div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
												<div className="flex-1">
													<div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between xl:gap-6">
														<div>
															<CardTitle className="text-2xl">
																{isEditing ? "Refine your alert" : "Create a focused alert"}
															</CardTitle>
															<CardDescription className="mt-2 max-w-2xl leading-6">
																Move coin by coin, choose one clear trigger, and keep the chart visible
																whenever price is involved.
															</CardDescription>
														</div>
														<Badge variant="secondary" className="w-fit gap-2 self-start px-3 py-1.5">
															<Sparkles className="size-3.5 text-sky-400" />
															Exchange-inspired builder
														</Badge>
													</div>
												</div>
											</div>
											<StepperNav className="mx-auto inline-flex w-auto min-w-[920px] max-w-full justify-center">
												{STEPS.map((item, index) => (
													<StepperItem
														key={item.step}
														step={item.step}
														completed={item.step < activeStep}
														disabled={item.step > maxUnlockedStep}
														className="relative">
														<StepperTrigger className="flex w-full items-center justify-start gap-3 rounded-2xl px-0 py-0 text-left disabled:opacity-45">
															<StepperIndicator />
															<div className="space-y-1">
																<StepperTitle>{item.title}</StepperTitle>
																<StepperDescription>{item.description}</StepperDescription>
															</div>
														</StepperTrigger>
														{index < STEPS.length - 1 ? (
															<StepperSeparator className="mx-4 data-[state=completed]:bg-emerald-500/60" />
														) : null}
													</StepperItem>
												))}
											</StepperNav>
										</CardHeader>

										<CardContent className="flex-1 pt-6">
											<div className="flex flex-col gap-4">
												{formError ? (
													<div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
														{formError}
													</div>
												) : null}
												{requestError ? (
													<div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
														{requestError}
													</div>
												) : null}
												<StepperPanel>
													<StepperContent value={1} forceMount>
														<div className="animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
															{renderCoinStep()}
														</div>
													</StepperContent>
													<StepperContent value={2} forceMount>
														<div className="animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
															{renderScenarioStep()}
														</div>
													</StepperContent>
													<StepperContent value={3} forceMount>
														<div className="animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
															{renderTimingStep()}
														</div>
													</StepperContent>
													<StepperContent value={4} forceMount>
														<div className="animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
															{scenario && isPriceScenario(scenario)
																? renderPriceConfigurator()
																: renderNewsConfigurator()}
														</div>
													</StepperContent>
												</StepperPanel>
											</div>
										</CardContent>
									</Stepper>
								</Card>

								<div className="grid gap-4">
									<Card className="border-border/30 bg-card/65 backdrop-blur-sm">
										<CardHeader className="gap-3">
											<CardTitle className="text-lg">Alert preview</CardTitle>
											<CardDescription>Stay oriented while you move through the steps.</CardDescription>
										</CardHeader>
										<CardContent className="space-y-4">
											<PreviewRow label="Coin" value={selectedAsset?.symbol ?? "Choose from watchlist"} />
											<PreviewRow label="Scenario" value={getScenarioLabel(scenario)} />
											<PreviewRow label="Timing" value={getTimeBehaviorLabel(timeBehavior)} />
											{timeBehavior === "daily_recurring" ? (
												<PreviewRow
													label="Window"
													value={
														recurringStartDate && recurringEndDate
															? `${formatShortDate(recurringStartDate)} - ${formatShortDate(recurringEndDate)}`
															: "Select both dates"
													}
												/>
											) : null}
											<PreviewRow
												label="Trigger"
												value={
													scenario === "coin_news"
														? "Any new article"
														: thresholdValue
															? triggerMode === "percent"
																? `${thresholdValue}%`
																: formatCurrency(thresholdValue)
															: "Not set yet"
												}
											/>
											<div className="rounded-3xl border border-border/40 bg-background/45 p-4">
												<p className="text-sm font-medium">What this means</p>
												<p className="mt-2 text-sm leading-6 text-muted-foreground">
													{getPreviewText({ scenario, triggerMode, thresholdValue, projectedPrice })}
												</p>
											</div>
										</CardContent>
									</Card>

									<Card className="border-border/30 bg-card/65 backdrop-blur-sm">
										<CardHeader className="gap-3">
											<CardTitle className="text-lg">Compact guidance</CardTitle>
											<CardDescription>No bulky notes panel, just the reminders you need right now.</CardDescription>
										</CardHeader>
										<CardContent className="space-y-3">
											<GuidanceRow text="Coin selection stays scoped to your watchlist, so alerts mirror your saved universe." />
											<GuidanceRow text="Recurring alerts use a clear start and end date window, and can notify again after a fresh qualifying move or newer article appears." />
											<GuidanceRow text="Price alerts show the trigger directly on the chart, and the `% / $` toggle changes how the backend stores the rule." />
											<GuidanceRow text="News alerts skip chart noise entirely and go straight to a simple subscription-style save." />
										</CardContent>
									</Card>
								</div>
							</section>
						</div>
					</div>

					<div className="shrink-0 border-t border-border/40 bg-background/95 px-4 py-4 backdrop-blur-sm lg:px-6">
						<div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
							<div>
								<p className="text-sm font-medium">
									{selectedAsset?.symbol ?? "Choose a coin"} · {getScenarioLabel(scenario)}
								</p>
								<p className="text-xs text-muted-foreground">
									{getTimeBehaviorLabel(timeBehavior)} · full edits can still change the coin, scenario, duration, and trigger mode.
								</p>
							</div>
							<div className="flex items-center gap-3">
								<Button asChild type="button" variant="ghost" className="rounded-full">
									<Link href="/alerts">Cancel</Link>
								</Button>
								<Button
									type="button"
									variant="outline"
									className="rounded-full"
									onClick={goToPreviousStep}
									disabled={activeStep === 1 || isSaving}>
									Back
								</Button>
								{activeStep < 4 ? (
									<Button
										type="button"
										className="rounded-full px-6"
										onClick={goToNextStep}
										disabled={isSaving}>
										Continue
									</Button>
								) : (
									<Button
										type="button"
										className="rounded-full px-6"
										onClick={() => void saveAlert()}
										disabled={isSaving || !selectedAssetId || !scenario}>
										{isSaving ? <LoaderCircle className="size-4 animate-spin" /> : null}
										{isEditing ? "Save alert" : "Create alert"}
									</Button>
								)}
							</div>
						</div>
					</div>
				</div>
			</SidebarInset>
		</>
	);
}

function PreviewRow({ label, value }: { label: string; value: string }) {
	return (
		<div className="rounded-3xl border border-border/40 bg-background/45 p-4">
			<p className="text-sm text-muted-foreground">{label}</p>
			<p className="mt-1 text-base font-semibold">{value}</p>
		</div>
	);
}

function MetricTile({ label, value }: { label: string; value: string }) {
	return (
		<div className="rounded-3xl border border-border/40 bg-background/45 p-4">
			<p className="text-sm text-muted-foreground">{label}</p>
			<p className="mt-2 text-base font-semibold">{value}</p>
		</div>
	);
}

function GuidanceRow({ text }: { text: string }) {
	return (
		<div className="rounded-2xl border border-border/40 bg-background/45 px-4 py-3 text-sm leading-6 text-muted-foreground">
			{text}
		</div>
	);
}

function SearchHint({ loading = false, message }: { loading?: boolean; message?: string }) {
	return (
		<div className="flex h-full min-h-[220px] flex-col items-center justify-center rounded-2xl border border-dashed border-border/40 px-4 text-center">
			<span className="flex size-11 items-center justify-center rounded-full border border-border/50 bg-muted/20 text-muted-foreground">
				{loading ? <LoaderCircle className="size-5 animate-spin" /> : <Search className="size-5" />}
			</span>
			<p className="mt-4 text-sm font-medium">
				{message ?? "Search the broader market, then add the coin straight into your watchlist from here."}
			</p>
		</div>
	);
}

function InlineState({
	title,
	description,
	actionLabel,
	onAction,
	href,
}: {
	title: string;
	description: string;
	actionLabel: string;
	onAction?: () => void;
	href?: string;
}) {
	const action = href ? (
		<Button asChild className="rounded-full">
			<Link href={href}>{actionLabel}</Link>
		</Button>
	) : (
		<Button className="rounded-full" onClick={onAction}>
			{actionLabel}
		</Button>
	);

	return (
		<div className="flex min-h-[360px] flex-col items-center justify-center rounded-[32px] border border-dashed border-border/40 bg-background/35 px-6 text-center">
			<div className="flex size-14 items-center justify-center rounded-full border border-border/50 bg-muted/30 text-muted-foreground">
				<Sparkles className="size-5" />
			</div>
			<p className="mt-5 text-lg font-semibold">{title}</p>
			<p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>
			<div className="mt-6">{action}</div>
		</div>
	);
}
