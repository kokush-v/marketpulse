import { LayoutGrid, List, Search } from "lucide-react";

import { getScenarioLabel } from "@/features/alerts/lib/alert-builder";
import type { AlertsView } from "@/features/alerts/hooks/use-alerts-view-preference";
import type { AlertFilters, ScenarioFilter, StatusFilter } from "@/features/alerts/lib/alert-filters";
import type { AlertStatusCounts } from "@/src/api/generated/models/alertStatusCounts";
import { Input } from "@/shared/components/ui/input";
import { cn } from "@/shared/lib";

const STATUS_TABS: Array<{ value: StatusFilter; label: string }> = [
  { value: "all", label: "All" },
  { value: "active", label: "Active" },
  { value: "paused", label: "Paused" },
];

const SCENARIO_OPTIONS: ScenarioFilter[] = ["all", "price_above", "price_below", "coin_news"];

function getScenarioFilterLabel(value: ScenarioFilter): string {
  return value === "all" ? "All types" : getScenarioLabel(value);
}

export function AlertsFilterBar({
  filters,
  counts,
  onChange,
}: {
  filters: AlertFilters;
  counts: AlertStatusCounts | undefined;
  onChange: (filters: AlertFilters) => void;
}) {
  return (
    <div className="space-y-3">
      <div role="tablist" aria-label="Filter alerts by status" className="flex gap-1 border-b border-border/40">
        {STATUS_TABS.map((tab) => {
          const isSelected = filters.status === tab.value;
          return (
            <button
              key={tab.value}
              type="button"
              role="tab"
              aria-selected={isSelected}
              onClick={() => onChange({ ...filters, status: tab.value })}
              className={cn(
                "-mb-px inline-flex items-center gap-2 border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                isSelected
                  ? "border-sky-500 text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {tab.label}
              <span className="rounded bg-muted px-1.5 py-0.5 text-xs tabular-nums text-muted-foreground">
                {counts ? counts[tab.value] : "–"}
              </span>
            </button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[200px] flex-1 sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={filters.search}
            onChange={(event) => onChange({ ...filters, search: event.target.value })}
            placeholder="Search coin"
            aria-label="Search alerts by coin name or symbol"
            className="h-9 rounded-md pl-9"
            maxLength={100}
          />
        </div>

        <div
          role="group"
          aria-label="Filter alerts by scenario"
          className="inline-flex divide-x divide-border/40 overflow-hidden rounded-md border border-border/40"
        >
          {SCENARIO_OPTIONS.map((option) => {
            const isSelected = filters.scenario === option;
            return (
              <button
                key={option}
                type="button"
                aria-pressed={isSelected}
                onClick={() => onChange({ ...filters, scenario: option })}
                className={cn(
                  "h-9 px-3 text-sm font-medium transition-colors",
                  isSelected
                    ? "bg-sky-500/15 text-sky-400"
                    : "text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                )}
              >
                {getScenarioFilterLabel(option)}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export function AlertsViewSwitcher({
  view,
  onChange,
}: {
  view: AlertsView;
  onChange: (view: AlertsView) => void;
}) {
  const options: Array<{ value: AlertsView; label: string; icon: typeof List }> = [
    { value: "list", label: "List view", icon: List },
    { value: "cards", label: "Card view", icon: LayoutGrid },
  ];

  return (
    <div
      role="group"
      aria-label="Alerts view"
      className="inline-flex divide-x divide-border/40 overflow-hidden rounded-md border border-border/40"
    >
      {options.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          type="button"
          aria-label={label}
          aria-pressed={view === value}
          onClick={() => onChange(value)}
          className={cn(
            "inline-flex size-9 items-center justify-center transition-colors",
            view === value ? "bg-sky-500/15 text-sky-400" : "text-muted-foreground hover:bg-muted/40 hover:text-foreground"
          )}
        >
          <Icon className="size-4" />
        </button>
      ))}
    </div>
  );
}
