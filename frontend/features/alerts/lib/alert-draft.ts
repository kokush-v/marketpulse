import { format } from "date-fns";

import { isPriceScenario, type AlertScenario, type TriggerMode } from "@/features/alerts/lib/alert-builder";
import type { CryptoChartPointResponse } from "@/src/api/generated/models/cryptoChartPointResponse";

export type ChartScope = "1D" | "1W" | "1M";
export type AlertTimeBehavior = "one_time" | "daily_recurring";

export const CHART_DOMAIN_PADDING = 0.08;

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: value >= 1000 ? 0 : 2,
  }).format(value);
}

export function getScopeChartData(chart: CryptoChartPointResponse[], scope: ChartScope): CryptoChartPointResponse[] {
  if (chart.length === 0) {
    return [];
  }

  const timestamps = chart.map((point) => Date.parse(point.time));
  if (!timestamps.every((value) => Number.isFinite(value))) {
    return scope === "1D" ? chart.slice(-Math.max(8, Math.ceil(chart.length / 7))) : chart;
  }

  const hoursByScope: Record<ChartScope, number> = { "1D": 24, "1W": 24 * 7, "1M": 24 * 30 };
  const cutoff = (timestamps.at(-1) ?? 0) - hoursByScope[scope] * 60 * 60 * 1000;
  const filtered = chart.filter((point) => Date.parse(point.time) >= cutoff);

  if (filtered.length >= 2) {
    return filtered;
  }

  return scope === "1D" ? chart.slice(-Math.max(8, Math.ceil(chart.length / 7))) : chart;
}

/** Fits the vertical axis to the displayed prices, with padding, instead of starting at zero. */
export function getChartDomain(prices: number[]): [number, number] | null {
  const valid = prices.filter((price) => Number.isFinite(price));
  if (valid.length === 0) {
    return null;
  }

  const min = Math.min(...valid);
  const max = Math.max(...valid);
  const padding = max === min ? Math.max(Math.abs(max) * 0.02, 0.01) : (max - min) * CHART_DOMAIN_PADDING;

  return [min - padding, max + padding];
}

/** Maps a click's vertical position inside the plot area to a price on the fitted axis. */
export function priceFromChartY(params: {
  chartY: number;
  plotTop: number;
  plotBottom: number;
  domain: [number, number];
}): number | null {
  const { chartY, plotTop, plotBottom, domain } = params;
  const plotHeight = plotBottom - plotTop;
  if (!Number.isFinite(chartY) || plotHeight <= 0) {
    return null;
  }

  const ratio = Math.min(1, Math.max(0, (chartY - plotTop) / plotHeight));
  return domain[1] - ratio * (domain[1] - domain[0]);
}

export function getProjectedPrice(params: {
  currentPrice: number;
  scenario: AlertScenario | null;
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

/** Converts a clicked price into the trigger input text for the selected `%` or `$` mode. */
export function thresholdInputFromPrice(price: number, triggerMode: TriggerMode, currentPrice: number): string | null {
  if (!Number.isFinite(price) || price <= 0) {
    return null;
  }

  if (triggerMode === "currency") {
    return price.toFixed(price >= 1000 ? 0 : 2);
  }

  if (currentPrice <= 0) {
    return null;
  }

  return Math.abs(((price - currentPrice) / currentPrice) * 100).toFixed(2);
}

function describeRepeat(params: {
  timeBehavior: AlertTimeBehavior;
  recurringStart?: Date;
  recurringEnd?: Date;
}): string {
  const { timeBehavior, recurringStart, recurringEnd } = params;
  if (timeBehavior === "one_time") {
    return "once";
  }

  if (recurringStart && recurringEnd) {
    return `daily, ${format(recurringStart, "MMM d")} – ${format(recurringEnd, "MMM d, yyyy")}`;
  }

  return "daily (choose dates)";
}

export function buildAlertSummary(params: {
  symbol: string | null;
  scenario: AlertScenario | null;
  triggerMode: TriggerMode;
  thresholdValue: number | null;
  projectedPrice: number | null;
  timeBehavior: AlertTimeBehavior;
  recurringStart?: Date;
  recurringEnd?: Date;
}): string {
  const { symbol, scenario, triggerMode, thresholdValue, projectedPrice } = params;

  if (!symbol) {
    return "Choose a coin to get started.";
  }
  if (!scenario) {
    return `Choose when to notify you about ${symbol}.`;
  }

  const repeat = describeRepeat(params);

  if (scenario === "coin_news") {
    return `Notify me about any new ${symbol} article, ${repeat}.`;
  }

  if (!thresholdValue || thresholdValue <= 0) {
    return "Choose a trigger value, or click the chart.";
  }

  const direction = scenario === "price_above" ? "rises above" : "falls below";
  if (triggerMode === "percent") {
    const target = projectedPrice ? ` (about ${formatCurrency(projectedPrice)})` : "";
    return `Notify me when ${symbol} ${scenario === "price_above" ? "rises" : "falls"} ${thresholdValue}% from the current price${target}, ${repeat}.`;
  }

  return `Notify me when ${symbol} ${direction} ${formatCurrency(thresholdValue)}, ${repeat}.`;
}
