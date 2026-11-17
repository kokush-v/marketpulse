"use client";

import { format } from "date-fns";
import type { DateRange } from "react-day-picker";

import type { AlertTimeBehavior } from "@/features/alerts/lib/alert-draft";
import { Calendar } from "@/shared/components/ui/calendar";
import { cn } from "@/shared/lib/utils";

const OPTIONS: Array<{ value: AlertTimeBehavior; label: string }> = [
  { value: "one_time", label: "Once" },
  { value: "daily_recurring", label: "Daily within dates" },
];

export function AlertRepeatControl({
  timeBehavior,
  range,
  onTimeBehaviorChange,
  onRangeChange,
}: {
  timeBehavior: AlertTimeBehavior;
  range: DateRange | undefined;
  onTimeBehaviorChange: (value: AlertTimeBehavior) => void;
  onRangeChange: (range: DateRange | undefined) => void;
}) {
  return (
    <div className="space-y-3">
      <div role="group" aria-label="Repeat" className="inline-flex divide-x divide-border/40 overflow-hidden rounded-md border border-border/40">
        {OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            aria-pressed={timeBehavior === option.value}
            onClick={() => onTimeBehaviorChange(option.value)}
            className={cn(
              "h-9 px-3 text-sm font-medium transition-colors",
              timeBehavior === option.value
                ? "bg-sky-500/15 text-sky-400"
                : "text-muted-foreground hover:bg-muted/40 hover:text-foreground",
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      {timeBehavior === "daily_recurring" ? (
        <div className="space-y-2 rounded-lg border border-border/40 p-3">
          <p className="text-sm text-muted-foreground">
            {range?.from && range?.to
              ? `${format(range.from, "MMM d, yyyy")} – ${format(range.to, "MMM d, yyyy")}`
              : range?.from
                ? `From ${format(range.from, "MMM d, yyyy")} — pick an end date`
                : "Pick a start and an end date"}
          </p>
          <Calendar
            mode="range"
            numberOfMonths={1}
            selected={range}
            onSelect={onRangeChange}
            disabled={{ before: new Date() }}
            className="mx-auto w-fit max-w-full"
          />
        </div>
      ) : null}
    </div>
  );
}
