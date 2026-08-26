"use client";

import * as React from "react";
import Link from "next/link";
import { startTransition } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { format, isSameDay } from "date-fns";
import type { DateRange } from "react-day-picker";
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import ReactFlow, { Background, type Edge, type Node, useNodesState } from "reactflow";
import {
	ArrowLeft,
	CalendarClock,
	Coins,
	Newspaper,
	Sparkles,
	TrendingDown,
	TrendingUp,
} from "lucide-react";
import "reactflow/dist/style.css";

import {
	FLOW_STAGE_ORDER,
	type FlowStage,
	type FlowStageStatus,
	getStageFromStep,
	getStageLabel,
	getStepFromStage,
	stageNodeTypes,
	type StageNodeData,
} from "@/features/alerts/components/alerts-flow";
import { AlertFlowReview, AlertFlowStageSummary } from "@/features/alerts/components/alerts-flow-summary";
import { isPriceScenario, type TriggerMode } from "@/features/alerts/lib/alert-builder";
import { AppSidebar } from "@/features/market-dashboard/components/app-sidebar";
import {
	getListAlertsAlertsGetQueryKey,
	useCreateAlertAlertsPost,
	useListAlertsAlertsGet,
	useUpdateAlertAlertsAlertIdPut,
} from "@/src/api/generated/alerts/alerts";
import type { CreateAlertRequestScenario } from "@/src/api/generated/models/createAlertRequestScenario";
import type { CryptoChartPointResponse } from "@/src/api/generated/models/cryptoChartPointResponse";
import {
	getGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGetQueryKey,
	useGetStarredWatchlistAssetContextWatchlistsStarredAssetsAssetIdContextGet,
	useGetStarredWatchlistWatchlistsStarredGet,
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
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import {
	Combobox,
	ComboboxContent,
	ComboboxEmpty,
	ComboboxInput,
	ComboboxItem,
	ComboboxList,
} from "@/shared/components/ui/combobox";
import { Input } from "@/shared/components/ui/input";
import { Separator } from "@/shared/components/ui/separator";
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetHeader,
	SheetTitle,
} from "@/shared/components/ui/sheet";
import { SidebarInset, SidebarTrigger } from "@/shared/components/ui/sidebar";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { cn } from "@/shared/lib/utils";

type ChartScope = "1D" | "1W" | "1M";
type AlertTimeBehavior = "one_time" | "daily_recurring";

const DEFAULT_NODE_POSITIONS: Record<string, { x: number; y: number }> = {
	coin: { x: 40, y: 280 },
	scenario: { x: 420, y: 80 },
	timing: { x: 1160, y: 250 },
	review: { x: 1540, y: 280 },
};

const SCENARIOS: Array<{
	id: CreateAlertRequestScenario;
	title: string;
	icon: typeof TrendingUp;
}> = [
	{
		id: "price_above",
		title: "Price above",
		icon: TrendingUp,
	},
	{
		id: "price_below",
		title: "Price below",
		icon: TrendingDown,
	},
	{
		id: "coin_news",
		title: "News",
		icon: Newspaper,
	},
];

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
		return "Any new article.";
	}

	if (!scenario || !isPriceScenario(scenario) || !thresholdValue) {
		return "Set trigger.";
	}

	if (triggerMode === "percent" && projectedPrice) {
		return `${thresholdValue}% to ${formatCurrency(projectedPrice)}.`;
	}

	return `${scenario === "price_above" ? "Above" : "Below"} ${formatCurrency(thresholdValue)}.`;
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
	const [scenarioQuery, setScenarioQuery] = React.useState("");
	const [formError, setFormError] = React.useState<string | null>(null);
	const [requestError, setRequestError] = React.useState<string | null>(null);
	const [isRecurringCalendarOpen, setIsRecurringCalendarOpen] = React.useState(false);
	const [flowNodes, setFlowNodes, onNodesChange] = useNodesState<StageNodeData>([]);
	const hydratedEditRef = React.useRef(false);

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
	const alertsQuery = useListAlertsAlertsGet(undefined, {
		query: {
			enabled: isEditing,
			staleTime: 30_000,
			retry: 1,
		},
	});
	const createAlertMutation = useCreateAlertAlertsPost();
	const updateAlertMutation = useUpdateAlertAlertsAlertIdPut();

	const watchlistAssets = watchlistQuery.data?.assets ?? [];
	const selectedAsset = React.useMemo(
		() => watchlistAssets.find((asset) => asset.asset_id === selectedAssetId) ?? null,
		[selectedAssetId, watchlistAssets],
	);
	const filteredWatchlistAssets = React.useMemo(() => {
		const query = searchQuery.trim().toLowerCase();
		if (!query) {
			return watchlistAssets;
		}

		return watchlistAssets.filter((asset) => {
			const symbol = asset.symbol.toLowerCase();
			const name = asset.name.toLowerCase();
			return symbol.includes(query) || name.includes(query);
		});
	}, [searchQuery, watchlistAssets]);
	const selectedScenarioOption = React.useMemo(
		() => SCENARIOS.find((item) => item.id === scenario) ?? null,
		[scenario],
	);
	const filteredScenarioOptions = React.useMemo(() => {
		const query = scenarioQuery.trim().toLowerCase();
		if (!query) {
			return SCENARIOS;
		}

		return SCENARIOS.filter((item) => item.title.toLowerCase().includes(query));
	}, [scenarioQuery]);
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
	const hasValidConfiguration =
		scenario === "coin_news" ||
		Boolean(scenario && isPriceScenario(scenario) && thresholdValue && thresholdValue > 0);
	const maxUnlockedStep = hasValidTiming ? 4 : hasValidConfiguration ? 3 : selectedAssetId ? 2 : 1;
	const isSaving = createAlertMutation.isPending || updateAlertMutation.isPending;

	const handleSelectCoin = (assetId: string) => {
		startTransition(() => {
			setSelectedAssetId(assetId);
			setSearchQuery("");
			setFormError(null);
			setRequestError(null);
			if (activeStep < 2) {
				setActiveStep(2);
			}
		});
	};

	const handleScenarioSelect = (nextScenario: CreateAlertRequestScenario) => {
		setScenario(nextScenario);
		setScenarioQuery("");
		setFormError(null);
		if (nextScenario === "coin_news") {
			setTriggerMode("currency");
			setThresholdInput("");
		}
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
		if (range?.from && range?.to && range.to >= range.from) {
			setIsRecurringCalendarOpen(false);
		}
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
			if (scenario !== "coin_news" && (!thresholdValue || thresholdValue <= 0)) {
				setFormError("Enter a positive trigger value for this price alert.");
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
			setActiveStep(2);
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
			<div className="space-y-3 rounded-2xl border border-border/40 bg-background/45 p-3">
				<div className="flex items-center justify-between gap-3">
					<div className="flex min-w-0 items-center gap-2">
						<span className="flex size-8 items-center justify-center rounded-xl border border-sky-500/20 bg-sky-500/10 text-sky-700 dark:text-sky-200">
							<Coins className="size-4" />
						</span>
						<div className="min-w-0">
							<p className="truncate text-sm font-semibold">
								{selectedAsset ? `${selectedAsset.symbol} · ${selectedAsset.name}` : "Choose coin"}
							</p>
						</div>
					</div>
					<Badge variant="secondary" className="gap-1.5 px-2.5 py-1 text-xs">
						{watchlistAssets.length}
					</Badge>
				</div>

				{watchlistAssets.length === 0 ? (
					<div className="rounded-2xl border border-dashed border-border/50 bg-background/40 px-4 py-8 text-center">
						<p className="text-sm font-medium">Watchlist is empty</p>
					</div>
				) : (
					<div className="space-y-2">
						<Combobox
							items={watchlistAssets}
							filteredItems={filteredWatchlistAssets}
							value={selectedAsset}
							inputValue={searchQuery}
							onInputValueChange={setSearchQuery}
							onValueChange={(nextAsset) => {
								if (nextAsset) {
									handleSelectCoin(nextAsset.asset_id);
								}
							}}
							itemToStringLabel={(asset) => `${asset.symbol} · ${asset.name}`}
							itemToStringValue={(asset) => asset.asset_id}
							isItemEqualToValue={(item, value) => item.asset_id === value.asset_id}>
							<ComboboxInput
								placeholder="Search watchlist"
								className="w-full"
								showClear={searchQuery.trim().length > 0}
							/>
							<ComboboxContent
								sideOffset={8}
								className="rounded-2xl border border-border/40 bg-popover/95 p-1 backdrop-blur-sm">
								<ComboboxEmpty>No matching watchlist coin</ComboboxEmpty>
								<ComboboxList>
									{filteredWatchlistAssets.map((asset) => (
										<ComboboxItem
											key={asset.asset_id}
											value={asset}
											className="rounded-xl px-3 py-2.5">
											<div className="min-w-0">
												<p className="truncate text-sm font-semibold">{asset.symbol}</p>
												<p className="truncate text-xs text-muted-foreground">{asset.name}</p>
											</div>
										</ComboboxItem>
									))}
								</ComboboxList>
							</ComboboxContent>
						</Combobox>
						{selectedAsset ? (
							<div className="flex items-center justify-between rounded-xl border border-sky-500/20 bg-sky-500/10 px-3 py-2">
								<div className="min-w-0">
									<p className="truncate text-sm font-semibold">{selectedAsset.symbol}</p>
									<p className="truncate text-xs text-muted-foreground">{selectedAsset.name}</p>
								</div>
								<Badge variant="outline" className="rounded-full border-sky-500/30 text-sky-700">
									Selected
								</Badge>
							</div>
						) : null}
					</div>
				)}
			</div>
		);
	};

	const renderScenarioStep = () => (
		<div className="flex h-full flex-col gap-3 rounded-2xl border border-border/40 bg-background/45 p-3">
			<div className="flex items-center justify-between gap-3">
				<div>
					<p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">Scenario</p>
				</div>
				<Badge variant="outline" className="rounded-full px-2.5 py-1 text-xs">
					{getScenarioLabel(scenario)}
				</Badge>
			</div>
			<Combobox
				items={SCENARIOS}
				filteredItems={filteredScenarioOptions}
				value={selectedScenarioOption}
				inputValue={scenarioQuery}
				onInputValueChange={setScenarioQuery}
				onValueChange={(nextScenario) => {
					if (nextScenario) {
						handleScenarioSelect(nextScenario.id);
					}
				}}
				itemToStringLabel={(item) => item.title}
				itemToStringValue={(item) => item.id}
				isItemEqualToValue={(item, value) => item.id === value.id}>
				<ComboboxInput
					placeholder="Choose scenario"
					className="w-full"
					showClear={scenarioQuery.trim().length > 0}
				/>
				<ComboboxContent
					sideOffset={8}
					className="rounded-2xl border border-border/40 bg-popover/95 p-1 backdrop-blur-sm">
					<ComboboxEmpty>No matching scenario</ComboboxEmpty>
					<ComboboxList>
						{filteredScenarioOptions.map((item) => {
							const Icon = item.icon;
							return (
								<ComboboxItem key={item.id} value={item} className="rounded-xl px-3 py-2.5">
									<div className="flex items-center gap-2">
										<Icon className="size-4" />
										<span className="text-sm font-semibold">{item.title}</span>
									</div>
								</ComboboxItem>
							);
						})}
					</ComboboxList>
				</ComboboxContent>
			</Combobox>
			<div className="min-h-0 flex-1 overflow-y-auto pr-1">
				{scenario ? (
					scenario === "coin_news" ? (
						renderNewsConfigurator()
					) : (
						renderPriceConfigurator()
					)
				) : (
					<div className="flex h-full min-h-[18rem] items-center justify-center rounded-2xl border border-dashed border-border/40 bg-background/35 px-4 text-center text-sm text-muted-foreground">
						Choose a scenario to configure the alert rule here.
					</div>
				)}
			</div>
		</div>
	);

	const renderTimingStep = () => (
		<div className="space-y-3 rounded-2xl border border-border/40 bg-background/45 p-3">
			<div className="flex items-center justify-between gap-3">
				<div>
					<p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">Timing</p>
				</div>
				<Badge variant="outline" className="rounded-full px-2.5 py-1 text-xs">
					{getTimeBehaviorLabel(timeBehavior)}
				</Badge>
			</div>
			<div className="grid gap-2 md:grid-cols-2">
						{[
							{
								id: "one_time" as const,
								title: "One-time",
							},
							{
								id: "daily_recurring" as const,
								title: "Daily recurring",
							},
						].map((option) => {
							const isActive = timeBehavior === option.id;
							return (
								<button
									key={option.id}
									type="button"
									onClick={() => handleTimeBehaviorSelect(option.id)}
									className={cn(
										"rounded-2xl border px-3 py-3 text-left transition-all duration-200",
										isActive
											? "border-sky-500/50 bg-sky-500/10 shadow-[0_12px_30px_rgba(14,165,233,0.1)]"
											: "border-border/40 bg-background/45 hover:border-sky-500/30",
									)}>
									<div className="flex items-center gap-2">
										<CalendarClock className="size-4 text-sky-500" />
										<p className="text-[13px] font-semibold">{option.title}</p>
									</div>
								</button>
							);
						})}
			</div>

			{timeBehavior === "daily_recurring" ? (
				<div className="space-y-3">
					<div className="flex flex-wrap items-center gap-2">
						<Button
							type="button"
							variant="outline"
							className="h-9 rounded-full px-4 text-xs"
							onClick={() => setIsRecurringCalendarOpen(true)}>
							Start: {formatDateFieldValue(recurringStartDate)}
						</Button>
						<Button
							type="button"
							variant="outline"
							className="h-9 rounded-full px-4 text-xs"
							onClick={() => setIsRecurringCalendarOpen(true)}>
							End: {formatDateFieldValue(recurringEndDate)}
						</Button>
					</div>
					<p className="text-xs text-muted-foreground">
						Open the calendar to choose the recurring active window.
					</p>
				</div>
			) : null}
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
			<div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
				<Card className="border-border/30 bg-card/70 backdrop-blur-sm">
					<CardHeader className="gap-4">
						<div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
							<div>
								<div className="flex items-center gap-2">
									<Badge className={cn("border text-xs", tone.badge)}>{getScenarioLabel(scenario)}</Badge>
									<Badge variant="outline" className="border-border/50">
										{selectedAsset?.symbol}
									</Badge>
								</div>
								<CardTitle className="mt-3 text-lg">
									{selectedAssetContextQuery.data?.summary.name}
								</CardTitle>
								<p className="mt-1 text-sm font-medium text-muted-foreground">{formatCurrency(currentPrice)}</p>
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
									<p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Trigger</p>
									<p className="mt-1 text-base font-semibold">
										{projectedPrice ? formatCurrency(projectedPrice) : "Choose a value"}
									</p>
								</div>
							</div>
							<div className="h-[330px] w-full">
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
						<CardTitle className="text-base">Trigger controls</CardTitle>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="space-y-2">
							<p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">Trigger value</p>
							<div className="flex items-center gap-2 rounded-xl border border-border/40 bg-background/55 p-2">
								<Input
									inputMode="decimal"
									value={thresholdInput}
									onChange={(event) => setThresholdInput(event.target.value)}
									placeholder={triggerMode === "currency" ? "100000" : "12.5"}
									className="h-9 border-0 bg-transparent px-2 text-sm shadow-none focus-visible:ring-0"
								/>
								<div className="inline-flex rounded-full border border-border/40 bg-background/70 p-1">
									<button
										type="button"
										onClick={() => setTriggerMode("percent")}
										className={cn(
											"rounded-full px-3 py-1 text-xs font-semibold transition",
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
											"rounded-full px-3 py-1 text-xs font-semibold transition",
											triggerMode === "currency"
												? "bg-sky-500 text-white"
												: "text-muted-foreground hover:text-foreground",
										)}>
										$
									</button>
								</div>
							</div>
						</div>

						<div className="rounded-2xl border border-border/40 bg-background/45 p-3">
							<p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">Preview</p>
							<p className="mt-1 text-[13px] font-semibold leading-5">
								{getPreviewText({ scenario, triggerMode, thresholdValue, projectedPrice })}
							</p>
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
		<div className="space-y-3 rounded-2xl border border-border/40 bg-background/45 p-3">
			<div className="flex items-center gap-2">
				<span className="flex size-8 items-center justify-center rounded-xl border border-sky-500/25 bg-sky-500/12 text-sky-300">
					<Newspaper className="size-4" />
				</span>
				<div>
					<p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">News rule</p>
					<p className="text-sm font-medium">Any new article for {selectedAsset?.symbol ?? "this coin"}.</p>
				</div>
			</div>
			<div className="grid gap-2 md:grid-cols-3">
				<MetricTile label="Scenario" value="News" />
				<MetricTile label="Coin" value={selectedAsset?.symbol ?? "Not selected"} />
				<MetricTile label="Timing" value={getTimeBehaviorLabel(timeBehavior)} />
			</div>
			<div className="rounded-2xl border border-border/40 bg-background/45 px-3 py-3">
				<p className="text-sm font-semibold">Any new article</p>
			</div>
		</div>
	);

	const renderNodeSummary = (stage: FlowStage) => {
		const coinValue = selectedAsset?.symbol ?? "Choose from watchlist";
		const scenarioValue = getScenarioLabel(scenario);
		const timingValue = getTimeBehaviorLabel(timeBehavior);
		const triggerValue =
			scenario === "coin_news"
				? "Any new article"
				: thresholdValue
					? triggerMode === "percent"
						? `${thresholdValue}%`
						: formatCurrency(thresholdValue)
					: "Not set yet";
		const windowValue =
			timeBehavior === "daily_recurring"
				? recurringStartDate && recurringEndDate
					? `${formatShortDate(recurringStartDate)} - ${formatShortDate(recurringEndDate)}`
					: "Select both dates"
				: undefined;

		switch (stage) {
			case "coin":
				return (
					<AlertFlowStageSummary
						stage="coin"
						coinValue={coinValue}
						scenarioValue={scenarioValue}
						timingValue={timingValue}
						triggerValue={triggerValue}
						coinName={selectedAsset?.name ?? "Choose from watchlist"}
						coinMeta={selectedAsset?.symbol ?? `${watchlistAssets.length} saved watchlist coin${watchlistAssets.length === 1 ? "" : "s"}`}
					/>
				);
			case "scenario":
				return (
					<AlertFlowStageSummary
						stage="scenario"
						coinValue={coinValue}
						scenarioValue={scenarioValue}
						timingValue={timingValue}
						triggerValue={triggerValue}
						scenarioSummary={
							<div className="space-y-2">
								<div className="rounded-2xl border border-border/40 bg-background/45 px-3 py-2.5">
									<p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Scenario</p>
									<p className="mt-1 text-[13px] font-semibold leading-5">{scenarioValue}</p>
								</div>
								<div className="rounded-2xl border border-border/40 bg-background/45 px-3 py-2.5">
									<p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Trigger</p>
									<p className="mt-1 text-[13px] font-semibold leading-5">{triggerValue}</p>
								</div>
							</div>
						}
					/>
				);
			case "timing":
				return (
					<AlertFlowStageSummary
						stage="timing"
						coinValue={coinValue}
						scenarioValue={scenarioValue}
						timingValue={timingValue}
						triggerValue={triggerValue}
						windowValue={windowValue}
					/>
				);
			case "review":
				return (
					<AlertFlowStageSummary
						stage="review"
						coinValue={coinValue}
						scenarioValue={scenarioValue}
						timingValue={timingValue}
						triggerValue={triggerValue}
					/>
				);
		}
	};

	const renderReviewNode = () => (
		<AlertFlowReview
			coinValue={selectedAsset?.symbol ?? "Choose from watchlist"}
			scenarioValue={getScenarioLabel(scenario)}
			timingValue={getTimeBehaviorLabel(timeBehavior)}
			triggerValue={
				scenario === "coin_news"
					? "Any new article"
					: thresholdValue
						? triggerMode === "percent"
							? `${thresholdValue}%`
							: formatCurrency(thresholdValue)
						: "Not set yet"
			}
			onBack={goToPreviousStep}
			onSave={() => void saveAlert()}
			isSaving={isSaving}
			saveLabel={isEditing ? "Save alert" : "Create alert"}
			saveDisabled={isSaving || !selectedAssetId || !scenario || !hasValidConfiguration || !hasValidTiming}
		/>
	);

	const getStageStatus = (step: number): FlowStageStatus => {
		if (step === 4 && requestError) {
			return "error";
		}
		if (step === activeStep && formError) {
			return "error";
		}
		if (step > maxUnlockedStep) {
			return "locked";
		}
		if (step === activeStep) {
			return "active";
		}
		if (step < activeStep) {
			return "complete";
		}
		return "ready";
	};

	const triggerValue =
		scenario === "coin_news"
			? "Any new article"
			: thresholdValue
				? triggerMode === "percent"
					? `${thresholdValue}%`
					: formatCurrency(thresholdValue)
				: "Not set yet";

	const desiredFlowNodes = React.useMemo<Node<StageNodeData>[]>(
		() => [
			{
				id: "coin",
				type: "stage",
				position: DEFAULT_NODE_POSITIONS.coin,
				data: {
					stage: "coin",
					title: selectedAsset?.symbol ?? "Choose coin",
					status: getStageStatus(1),
					badge: selectedAsset?.symbol,
					onSelect: () => setActiveStep(1),
					body: activeStep === 1 ? renderCoinStep() : renderNodeSummary("coin"),
				},
			},
			{
				id: "scenario",
				type: "stage",
				position: DEFAULT_NODE_POSITIONS.scenario,
				data: {
					stage: "scenario",
					title: scenario ? `${getScenarioLabel(scenario)} rule` : "Choose scenario",
					status: getStageStatus(2),
					badge: scenario ? getScenarioLabel(scenario) : undefined,
					onSelect: () => {
						if (maxUnlockedStep >= 2) {
							setActiveStep(2);
						}
					},
					body: activeStep === 2 ? renderScenarioStep() : renderNodeSummary("scenario"),
					footer:
						activeStep === 2 ? (
							<div className="flex flex-col gap-3 sm:flex-row">
								<Button type="button" variant="outline" className="h-9 rounded-full px-4" onClick={goToPreviousStep}>
									Back
								</Button>
								<Button type="button" className="h-9 rounded-full px-5" onClick={goToNextStep} disabled={isSaving}>
									Continue
								</Button>
							</div>
						) : undefined,
				},
			},
			{
				id: "timing",
				type: "stage",
				position: DEFAULT_NODE_POSITIONS.timing,
				data: {
					stage: "timing",
					title: getTimeBehaviorLabel(timeBehavior),
					status: getStageStatus(3),
					badge: getTimeBehaviorLabel(timeBehavior),
					onSelect: () => {
						if (maxUnlockedStep >= 3) {
							setActiveStep(3);
						}
					},
					body: activeStep === 3 ? renderTimingStep() : renderNodeSummary("timing"),
					footer:
						activeStep === 3 ? (
							<div className="flex flex-col gap-3 sm:flex-row">
								<Button type="button" variant="outline" className="h-9 rounded-full px-4" onClick={goToPreviousStep}>
									Back
								</Button>
								<Button type="button" className="h-9 rounded-full px-5" onClick={goToNextStep} disabled={isSaving}>
									Continue
								</Button>
							</div>
						) : undefined,
				},
			},
			{
				id: "review",
				type: "stage",
				position: DEFAULT_NODE_POSITIONS.review,
				data: {
					stage: "review",
					title: isEditing ? "Review changes" : "Review alert",
					status: getStageStatus(4),
					badge: maxUnlockedStep >= 4 ? "Ready" : "Locked",
					onSelect: () => {
						if (maxUnlockedStep >= 4) {
							setActiveStep(4);
						}
					},
					body: activeStep === 4 ? renderReviewNode() : renderNodeSummary("review"),
				},
			},
		],
		[
			activeStep,
			formError,
			isEditing,
			maxUnlockedStep,
			recurringEndDate,
			recurringStartDate,
			requestError,
			scenario,
			selectedAsset,
			thresholdValue,
			timeBehavior,
			triggerValue,
			triggerMode,
			watchlistAssets.length,
		],
	);

	React.useEffect(() => {
		setFlowNodes((current) => {
			const positionById = new Map(current.map((node) => [node.id, node.position]));
			return desiredFlowNodes.map((node) => ({
				...node,
				position: positionById.get(node.id) ?? node.position,
			}));
		});
	}, [desiredFlowNodes, setFlowNodes]);

	const flowEdges: Edge[] = [
		{
			id: "coin-scenario",
			source: "coin",
			target: "scenario",
			type: "default",
			animated: true,
			style: { stroke: "#7dd3fc", strokeWidth: 2.25 },
		},
		{
			id: "scenario-timing",
			source: "scenario",
			target: "timing",
			type: "default",
			animated: true,
			style: { stroke: "#7dd3fc", strokeWidth: 2.25 },
		},
		{
			id: "timing-review",
			source: "timing",
			target: "review",
			type: "default",
			animated: true,
			style: { stroke: "#7dd3fc", strokeWidth: 2.25 },
		},
	];

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
							Flow
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
							<section className="pb-24">
								<Card className="overflow-hidden border-border/30 bg-card/65 backdrop-blur-sm">
									<CardHeader className="gap-5 border-b border-border/30 pb-6">
										<div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
											<div className="flex-1">
												<div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between xl:gap-6">
													<div>
														<CardTitle className="text-2xl">
															{isEditing ? "Refine your alert" : "Create a focused alert"}
														</CardTitle>
													</div>
													<Badge variant="secondary" className="w-fit gap-2 self-start px-3 py-1.5">
														<Sparkles className="size-3.5 text-sky-400" />
														Canvas
													</Badge>
												</div>
											</div>
										</div>
										<div className="flex flex-wrap gap-2">
											{FLOW_STAGE_ORDER.map((stage) => {
												const stageStep = getStepFromStage(stage);
												const canSelect = stageStep <= maxUnlockedStep;
												const isCurrent = getStageFromStep(activeStep) === stage;
												return (
													<button
														key={stage}
														type="button"
														onClick={() => {
															if (canSelect) {
																setActiveStep(stageStep);
															}
														}}
														className={cn(
															"rounded-full border px-3 py-1.5 text-xs font-semibold transition",
															isCurrent
																? "border-sky-500/50 bg-sky-500/10 text-sky-700"
																: canSelect
																	? "border-border/40 bg-background/55 text-muted-foreground hover:text-foreground"
																	: "border-border/30 bg-background/35 text-muted-foreground/70 opacity-70",
														)}>
														{getStageLabel(stage)}
													</button>
												);
											})}
											<Button
												type="button"
												variant="ghost"
												size="sm"
												className="rounded-full"
												onClick={() => {
													setFlowNodes((current) =>
														current.map((node) => ({
															...node,
															position: DEFAULT_NODE_POSITIONS[node.id] ?? node.position,
														})),
													);
												}}>
												Reset layout
											</Button>
										</div>
									</CardHeader>

									<CardContent className="p-0">
										{formError ? (
											<div className="border-b border-destructive/20 bg-destructive/10 px-6 py-3 text-sm text-destructive">
												{formError}
											</div>
										) : null}
										{requestError ? (
											<div className="border-b border-destructive/20 bg-destructive/10 px-6 py-3 text-sm text-destructive">
												{requestError}
											</div>
										) : null}
										<div className="h-[920px] w-full bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.08),transparent_26%),linear-gradient(to_bottom,rgba(255,255,255,0.9),rgba(248,250,252,0.9))] dark:bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.08),transparent_26%),linear-gradient(to_bottom,rgba(15,23,42,0.88),rgba(2,6,23,0.95))]">
											<ReactFlow
												nodes={flowNodes}
												onNodesChange={onNodesChange}
												edges={flowEdges}
												nodeTypes={stageNodeTypes}
												nodesDraggable
												nodesConnectable={false}
												elementsSelectable={false}
												zoomOnScroll
												zoomOnPinch
												panOnDrag
												preventScrolling={false}
												fitView
												fitViewOptions={{ padding: 0.2 }}
												minZoom={0.55}
												maxZoom={1.4}
												proOptions={{ hideAttribution: true }}
												className="bg-transparent">
												<Background color="rgba(148,163,184,0.18)" gap={24} size={1} />
											</ReactFlow>
										</div>
									</CardContent>
								</Card>
							</section>
						</div>
					</div>
				</div>
			</SidebarInset>
			<Sheet open={isRecurringCalendarOpen} onOpenChange={setIsRecurringCalendarOpen}>
				<SheetContent side="bottom" className="rounded-t-[28px] border-border/40 px-4 pb-6 pt-10 sm:px-6">
					<SheetHeader>
						<SheetTitle>Choose recurring dates</SheetTitle>
						<SheetDescription>
							Select the start and end date for the recurring alert window.
						</SheetDescription>
					</SheetHeader>
					<div className="mt-6 rounded-3xl border border-border/40 bg-card/80 px-3 py-4">
						<Calendar
							mode="range"
							numberOfMonths={1}
							selected={recurringRange}
							onSelect={handleRecurringRangeChange}
							disabled={{ before: new Date() }}
							className="relative mx-auto w-fit max-w-full [--cell-size:2.35rem] sm:[--cell-size:2.6rem]"
							classNames={{
								root: "relative mx-auto w-fit",
								months: "flex w-fit",
								month: "w-fit min-w-0",
								nav: "absolute left-1/2 top-1 flex w-[calc(var(--cell-size)*7+1.2rem)] max-w-full -translate-x-1/2 items-center justify-between px-2",
								month_caption: "flex h-9 items-center justify-center px-10 text-sm",
								weekday: "w-9 text-center text-[0.72rem] sm:w-10",
								week: "mt-1.5 flex w-fit gap-0",
							}}
						/>
					</div>
				</SheetContent>
			</Sheet>
		</>
	);
}

function MetricTile({ label, value }: { label: string; value: string }) {
	return (
		<div className="rounded-3xl border border-border/40 bg-background/45 p-3">
			<p className="text-xs text-muted-foreground">{label}</p>
			<p className="mt-1.5 text-sm font-semibold">{value}</p>
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
