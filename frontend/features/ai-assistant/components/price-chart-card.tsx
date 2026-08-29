"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  XAxis,
  YAxis,
} from "recharts";

import type { AssistantChartPayloadResponse } from "@/src/api/generated/models/assistantChartPayloadResponse";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/shared/components/ui/chart";

const SERIES_COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

type PriceChartCardProps = {
  chart: AssistantChartPayloadResponse;
};

export function PriceChartCard({ chart }: PriceChartCardProps) {
  const seriesKeys = chart.series.map((series, index) => `${series.symbol}-${index}`);
  const data = buildChartData(chart, seriesKeys);
  const chartConfig = Object.fromEntries(
    chart.series.map((series, index) => [
      seriesKeys[index],
      { label: `${series.name} (${series.symbol})`, color: SERIES_COLORS[index] },
    ]),
  ) satisfies ChartConfig;

  return (
    <section
      aria-label={`Price chart for ${chart.series.map((series) => series.symbol).join(", ")}`}
      className="mt-4 min-w-0 rounded-xl border border-border/30 bg-card/60 p-3 backdrop-blur-sm sm:p-4"
    >
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h3 className="text-sm font-semibold">Price comparison</h3>
        <span className="text-xs text-muted-foreground">{periodLabel(chart.period)} · USD</span>
      </div>
      <div className="h-60 min-w-0 sm:h-72">
        <ChartContainer config={chartConfig} className="h-full w-full">
          <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 4 }}>
            <CartesianGrid
              vertical={false}
              strokeDasharray="3 3"
              className="stroke-muted-foreground/20"
            />
            <XAxis
              dataKey="time"
              minTickGap={28}
              axisLine={false}
              tickLine={false}
              tickMargin={8}
              tick={{ fontSize: 11 }}
              tickFormatter={(value: string) => formatChartTime(value, chart.period)}
            />
            <YAxis
              width={88}
              axisLine={false}
              tickLine={false}
              tickMargin={10}
              tick={{ fontSize: 11 }}
              tickFormatter={formatPrice}
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  labelFormatter={(value) => new Date(String(value)).toLocaleString()}
                  formatter={(value, name) => [formatPrice(Number(value)), String(name)]}
                />
              }
            />
            <Legend wrapperStyle={{ fontSize: "0.75rem" }} />
            {chart.series.map((series, index) => (
              <Line
                key={seriesKeys[index]}
                type="monotone"
                dataKey={seriesKeys[index]}
                name={`${series.name} (${series.symbol})`}
                stroke={`var(--color-${seriesKeys[index]})`}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ChartContainer>
      </div>
    </section>
  );
}

function buildChartData(chart: AssistantChartPayloadResponse, seriesKeys: string[]) {
  const rows = new Map<string, Record<string, number | string>>();

  chart.series.forEach((series, index) => {
    series.points.forEach((point) => {
      const row = rows.get(point.time) ?? { time: point.time };
      row[seriesKeys[index]] = point.price;
      rows.set(point.time, row);
    });
  });

  return [...rows.values()].sort((left, right) =>
    String(left.time).localeCompare(String(right.time)),
  );
}

function periodLabel(period: AssistantChartPayloadResponse["period"]) {
  return { "24h": "24 hours", "7d": "7 days", "30d": "30 days", "1y": "1 year" }[period];
}

function formatChartTime(time: string, period: AssistantChartPayloadResponse["period"]) {
  const date = new Date(time);
  return period === "24h"
    ? date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : date.toLocaleDateString([], { month: "short", day: "numeric" });
}

function formatPrice(value: number) {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    notation: value >= 10_000 ? "compact" : "standard",
    maximumFractionDigits: value < 1 ? 4 : 2,
  }).format(value);
}
