"use client";

import * as React from "react";
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import {
  formatCurrency,
  getChartDomain,
  priceFromChartY,
  type ChartScope,
} from "@/features/alerts/lib/alert-draft";
import type { CryptoChartPointResponse } from "@/src/api/generated/models/cryptoChartPointResponse";
import { cn } from "@/shared/lib/utils";

const CHART_HEIGHT = 300;
const MARGIN = { top: 12, right: 12, bottom: 0, left: 0 };
const X_AXIS_HEIGHT = 28;
const Y_AXIS_WIDTH = 72;
const SCOPES: ChartScope[] = ["1D", "1W", "1M"];

const TONES = {
  price_above: "#10b981",
  price_below: "#f43f5e",
} as const;

function formatChartTick(value: string): string {
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(new Date(value));
}

function formatChartTooltip(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function AlertPriceChart({
  data,
  scope,
  onScopeChange,
  scenario,
  triggerPrice,
  onPickPrice,
}: {
  data: CryptoChartPointResponse[];
  scope: ChartScope;
  onScopeChange: (scope: ChartScope) => void;
  scenario: "price_above" | "price_below";
  triggerPrice: number | null;
  onPickPrice: (price: number) => void;
}) {
  const color = TONES[scenario];
  const domain = React.useMemo(() => getChartDomain(data.map((point) => point.price)), [data]);
  const isTriggerVisible = triggerPrice !== null && domain !== null && triggerPrice >= domain[0] && triggerPrice <= domain[1];

  const handleClick = (state: unknown) => {
    if (!domain) {
      return;
    }

    const { chartY, activePayload } = (state ?? {}) as {
      chartY?: number;
      activePayload?: Array<{ payload?: { price?: number } }>;
    };

    const price =
      typeof chartY === "number"
        ? priceFromChartY({
            chartY,
            plotTop: MARGIN.top,
            plotBottom: CHART_HEIGHT - X_AXIS_HEIGHT - MARGIN.bottom,
            domain,
          })
        : (activePayload?.[0]?.payload?.price ?? null);

    if (typeof price === "number" && Number.isFinite(price) && price > 0) {
      onPickPrice(price);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">Click the chart to set the trigger level.</p>
        <div role="group" aria-label="Chart range" className="inline-flex rounded-md border border-border/40 p-0.5">
          {SCOPES.map((item) => (
            <button
              key={item}
              type="button"
              aria-pressed={scope === item}
              onClick={() => onScopeChange(item)}
              className={cn(
                "rounded px-2.5 py-1 text-xs font-semibold transition-colors",
                scope === item ? "bg-sky-500/15 text-sky-400" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <div className="w-full cursor-crosshair" style={{ height: CHART_HEIGHT }}>
        {data.length > 0 && domain ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} onClick={handleClick} margin={MARGIN}>
              <defs>
                <linearGradient id="alert-panel-fill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(148,163,184,0.15)" vertical={false} />
              <XAxis
                dataKey="time"
                tickFormatter={formatChartTick}
                axisLine={false}
                tickLine={false}
                minTickGap={32}
                height={X_AXIS_HEIGHT}
                tick={{ fill: "rgba(148,163,184,0.8)", fontSize: 11 }}
              />
              <YAxis
                domain={domain}
                type="number"
                allowDataOverflow
                axisLine={false}
                tickLine={false}
                width={Y_AXIS_WIDTH}
                tickCount={5}
                tickFormatter={(value) => formatCurrency(Number(value))}
                tick={{ fill: "rgba(148,163,184,0.8)", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: "8px",
                  borderColor: "rgba(148,163,184,0.25)",
                  backgroundColor: "rgba(10,14,20,0.96)",
                }}
                formatter={(value) => formatCurrency(Number(value))}
                labelFormatter={(value) => formatChartTooltip(String(value))}
              />
              {isTriggerVisible ? (
                <ReferenceLine
                  y={triggerPrice}
                  stroke={color}
                  strokeDasharray="6 6"
                  label={{
                    value: `Trigger ${formatCurrency(triggerPrice)}`,
                    position: "insideTopRight",
                    fill: color,
                    fontSize: 12,
                  }}
                />
              ) : null}
              <Area dataKey="price" type="monotone" stroke={color} strokeWidth={2.2} fill="url(#alert-panel-fill)" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-border/40 text-sm text-muted-foreground">
            Chart data is not available for this coin right now.
          </div>
        )}
      </div>

      {triggerPrice !== null && domain !== null && !isTriggerVisible ? (
        <p className="text-xs text-muted-foreground">
          The trigger ({formatCurrency(triggerPrice)}) is outside the visible range of this chart.
        </p>
      ) : null}
    </div>
  );
}
