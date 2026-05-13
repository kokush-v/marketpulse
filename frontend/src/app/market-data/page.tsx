"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import type { AxiosError } from "axios";
import {
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Loader2,
  Search,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  type HistoryPoint,
  type SymbolSearchResult,
  useGetMarketDataHistory,
  useGetMarketDataQuote,
  useSearchMarketDataSymbols,
} from "@/generated/market-data/market-data";
import { cn } from "@/lib/utils";

const tickerSchema = z.object({
  symbol: z
    .string()
    .trim()
    .min(1, "Enter a ticker symbol.")
    .max(12, "Use 12 characters or fewer.")
    .regex(/^[A-Za-z][A-Za-z0-9.-]*$/, "Use letters, numbers, dots, or dashes."),
});

type TickerFormValues = z.infer<typeof tickerSchema>;
type RangeOption = "1M" | "3M" | "1Y";

const rangeOptions: RangeOption[] = ["1M", "3M", "1Y"];

function normalizeSymbol(value: string) {
  return value.trim().toUpperCase();
}

function formatCurrency(value?: number | null, currency = "USD") {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }

  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatTimestamp(value?: number | string | null) {
  if (!value) {
    return "Timestamp unavailable";
  }

  const date =
    typeof value === "number"
      ? new Date(value < 10_000_000_000 ? value * 1000 : value)
      : new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Timestamp unavailable";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatProviderError(error: unknown) {
  const status = (error as AxiosError | undefined)?.response?.status;

  if (status === 404) {
    return "No quote is available for that ticker.";
  }

  if (status === 401 || status === 403) {
    return "Market data requires an active authenticated session.";
  }

  if (status === 429) {
    return "The market-data provider is rate limited. Try again shortly.";
  }

  if (status && status >= 500) {
    return "The market-data provider is temporarily unavailable.";
  }

  return "Market data is unavailable right now.";
}

function getChangeTone(value?: number | null) {
  if (typeof value !== "number") {
    return "text-muted-foreground";
  }

  return value >= 0 ? "text-emerald-400" : "text-red-400";
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="border-t border-border px-0 py-4">
      <dt className="text-xs font-medium uppercase text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-base font-semibold text-foreground">{value}</dd>
    </div>
  );
}

function SymbolResult({
  result,
  onSelect,
}: {
  result: SymbolSearchResult;
  onSelect: (symbol: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(result.symbol)}
      className="flex w-full items-center justify-between gap-4 border-t border-border py-3 text-left transition-colors hover:text-primary"
    >
      <span>
        <span className="block text-sm font-semibold">{result.symbol}</span>
        <span className="block text-xs text-muted-foreground">
          {result.description ?? result.display_symbol ?? "Company name unavailable"}
        </span>
      </span>
      <span className="shrink-0 text-xs text-muted-foreground">
        {result.type ?? ""}
      </span>
    </button>
  );
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value?: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="rounded-md border bg-card px-3 py-2 text-xs shadow-sm">
      <div className="font-medium text-foreground">{label}</div>
      <div className="text-muted-foreground">Close {formatCurrency(payload[0]?.value)}</div>
    </div>
  );
}

function toChartData(points?: HistoryPoint[]) {
  return (points ?? []).map((point) => {
    const date = new Date(point.timestamp);

    return {
      date: Number.isNaN(date.getTime())
        ? String(point.timestamp)
        : new Intl.DateTimeFormat("en-US", {
            month: "short",
            day: "numeric",
          }).format(date),
      close: point.close_price,
      volume: point.volume,
    };
  });
}

export default function MarketDataPage() {
  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [range, setRange] = useState<RangeOption>("3M");
  const form = useForm<TickerFormValues>({
    resolver: zodResolver(tickerSchema),
    defaultValues: {
      symbol: "",
    },
  });

  const watchedSymbol = form.watch("symbol");
  const normalizedSearch = normalizeSymbol(watchedSymbol);
  const searchReady = normalizedSearch.length >= 1 && !form.formState.errors.symbol;

  const symbolSearch = useSearchMarketDataSymbols(
    { query: normalizedSearch },
    {
      query: {
        enabled: searchReady,
      },
    },
  );

  const quoteQuery = useGetMarketDataQuote(selectedSymbol, {
    query: {
      enabled: Boolean(selectedSymbol),
    },
  });

  const historyQuery = useGetMarketDataHistory(
    selectedSymbol,
    {
      range,
      resolution: "D",
    },
    {
      query: {
        enabled: Boolean(selectedSymbol) && quoteQuery.isSuccess,
      },
    },
  );

  const quote = quoteQuery.data;
  const chartData = useMemo(
    () => toChartData(historyQuery.data?.points),
    [historyQuery.data?.points],
  );
  const hasChart = chartData.length > 0;
  const currency = "USD";
  const changeTone = getChangeTone(quote?.daily_change);
  const isPositive = (quote?.daily_change ?? 0) >= 0;

  function submit(values: TickerFormValues) {
    const symbol = normalizeSymbol(values.symbol);
    form.setValue("symbol", symbol, {
      shouldValidate: true,
      shouldDirty: true,
    });
    setSelectedSymbol(symbol);
  }

  function selectSymbol(symbol: string) {
    form.setValue("symbol", symbol, {
      shouldValidate: true,
      shouldDirty: true,
    });
    setSelectedSymbol(symbol);
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="border-b bg-card">
        <div className="mx-auto flex min-h-[72px] w-full max-w-6xl flex-col justify-center gap-1 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">MarketPulse</p>
            <h1 className="text-2xl font-semibold tracking-normal">Market data</h1>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <BarChart3 className="h-4 w-4" aria-hidden="true" />
            Daily prices only
          </div>
        </div>
      </section>

      <section className="mx-auto grid w-full max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="space-y-6">
          <div className="rounded-lg border bg-card p-5 shadow-sm">
            <form className="space-y-3" onSubmit={form.handleSubmit(submit)}>
              <label htmlFor="symbol" className="text-sm font-medium">
                Ticker
              </label>
              <div className="flex gap-2">
                <div className="relative min-w-0 flex-1">
                  <Search
                    className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                    aria-hidden="true"
                  />
                  <input
                    id="symbol"
                    {...form.register("symbol")}
                    placeholder="AAPL"
                    autoCapitalize="characters"
                    className="h-10 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm font-medium uppercase outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-2 focus:ring-ring"
                  />
                </div>
                <Button type="submit" size="icon" aria-label="Get market data">
                  {quoteQuery.isFetching ? (
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  ) : (
                    <Search className="h-4 w-4" aria-hidden="true" />
                  )}
                </Button>
              </div>
              {form.formState.errors.symbol ? (
                <p className="text-sm text-red-300">{form.formState.errors.symbol.message}</p>
              ) : null}
            </form>

            <div className="mt-5">
              <div className="mb-2 flex items-center justify-between">
                <h2 className="text-sm font-semibold">Search results</h2>
                {symbolSearch.isFetching ? (
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" aria-hidden="true" />
                ) : null}
              </div>

              {!watchedSymbol.trim() ? (
                <p className="border-t border-border py-4 text-sm text-muted-foreground">
                  Search for a ticker to start.
                </p>
              ) : symbolSearch.isError ? (
                <p className="border-t border-border py-4 text-sm text-red-300">
                  Symbol lookup is unavailable.
                </p>
              ) : symbolSearch.data?.results.length ? (
                <div>
                  {symbolSearch.data.results.slice(0, 6).map((result) => (
                    <SymbolResult
                      key={`${result.symbol}-${result.display_symbol ?? ""}`}
                      result={result}
                      onSelect={selectSymbol}
                    />
                  ))}
                </div>
              ) : searchReady && !symbolSearch.isFetching ? (
                <p className="border-t border-border py-4 text-sm text-muted-foreground">
                  No matching symbols found.
                </p>
              ) : null}
            </div>
          </div>
        </aside>

        <div className="space-y-6">
          {!selectedSymbol ? (
            <div className="rounded-lg border bg-card p-8 shadow-sm">
              <div className="flex h-12 w-12 items-center justify-center rounded-md bg-secondary">
                <Search className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
              </div>
              <h2 className="mt-5 text-xl font-semibold">No ticker selected</h2>
              <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                Enter a stock ticker to view the latest backend-provided quote and daily history.
              </p>
            </div>
          ) : quoteQuery.isLoading ? (
            <div className="rounded-lg border bg-card p-8 shadow-sm">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden="true" />
              <h2 className="mt-5 text-xl font-semibold">Loading {selectedSymbol}</h2>
              <p className="mt-2 text-sm text-muted-foreground">Fetching the latest quote.</p>
            </div>
          ) : quoteQuery.isError ? (
            <div className="rounded-lg border bg-card p-8 shadow-sm">
              <div className="flex h-12 w-12 items-center justify-center rounded-md bg-secondary">
                <AlertCircle className="h-6 w-6 text-red-300" aria-hidden="true" />
              </div>
              <h2 className="mt-5 text-xl font-semibold">{selectedSymbol}</h2>
              <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                {formatProviderError(quoteQuery.error)}
              </p>
            </div>
          ) : quote ? (
            <>
              <section className="rounded-lg border bg-card p-5 shadow-sm">
                <div className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">{quote.symbol}</p>
                    <h2 className="mt-1 text-4xl font-semibold tracking-normal">
                      {formatCurrency(quote.current_price, currency)}
                    </h2>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {formatTimestamp(quote.quote_timestamp)}
                    </p>
                  </div>
                  <div className={cn("flex items-center gap-2 text-base font-semibold", changeTone)}>
                    {isPositive ? (
                      <ArrowUpRight className="h-5 w-5" aria-hidden="true" />
                    ) : (
                      <ArrowDownRight className="h-5 w-5" aria-hidden="true" />
                    )}
                    <span>
                      {formatCurrency(quote.daily_change, currency)}{" "}
                      {formatPercent(quote.daily_percent_change)}
                    </span>
                  </div>
                </div>

                <dl className="grid gap-x-6 sm:grid-cols-2 lg:grid-cols-4">
                  <Metric label="Open" value={formatCurrency(quote.open_price, currency)} />
                  <Metric label="High" value={formatCurrency(quote.high_price, currency)} />
                  <Metric label="Low" value={formatCurrency(quote.low_price, currency)} />
                  <Metric
                    label="Previous close"
                    value={formatCurrency(quote.previous_close, currency)}
                  />
                </dl>
              </section>

              <section className="rounded-lg border bg-card p-5 shadow-sm">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">Daily history</h2>
                    <p className="text-sm text-muted-foreground">
                      {historyQuery.data?.resolution ?? "D"} resolution
                    </p>
                  </div>
                  <div className="inline-flex w-fit rounded-md border border-input bg-background p-1">
                    {rangeOptions.map((option) => (
                      <button
                        key={option}
                        type="button"
                        onClick={() => setRange(option)}
                        className={cn(
                          "h-8 rounded px-3 text-sm font-medium transition-colors",
                          option === range
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:text-foreground",
                        )}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mt-5 h-[320px] w-full">
                  {historyQuery.isLoading ? (
                    <div className="flex h-full items-center justify-center rounded-md border border-dashed border-border">
                      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden="true" />
                    </div>
                  ) : historyQuery.isError || !hasChart ? (
                    <div className="flex h-full flex-col items-center justify-center rounded-md border border-dashed border-border px-6 text-center">
                      <BarChart3 className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
                      <h3 className="mt-4 text-base font-semibold">Chart unavailable</h3>
                      <p className="mt-2 max-w-md text-sm text-muted-foreground">
                        Latest quote data is still available. Daily historical candles may be blocked
                        by provider access, rate limits, or temporary provider issues.
                      </p>
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                        <CartesianGrid stroke="hsl(var(--border))" vertical={false} />
                        <XAxis
                          dataKey="date"
                          tickLine={false}
                          axisLine={false}
                          tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                          minTickGap={24}
                        />
                        <YAxis
                          tickLine={false}
                          axisLine={false}
                          tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                          width={64}
                          tickFormatter={(value) => formatNumber(Number(value))}
                        />
                        <Tooltip content={<ChartTooltip />} />
                        <Line
                          type="monotone"
                          dataKey="close"
                          stroke="hsl(var(--primary))"
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 4 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </section>
            </>
          ) : null}
        </div>
      </section>
    </main>
  );
}
