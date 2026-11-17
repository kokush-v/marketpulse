import { ArrowDownRight, ArrowUpRight, Newspaper } from "lucide-react";

import type { AlertScenario } from "@/features/alerts/lib/alert-builder";
import { getScenarioLabel } from "@/features/alerts/lib/alert-builder";
import { cn } from "@/shared/lib";

function getScenarioIcon(scenario: AlertScenario) {
  if (scenario === "price_above") {
    return <ArrowUpRight className="size-4" />;
  }
  if (scenario === "price_below") {
    return <ArrowDownRight className="size-4" />;
  }
  return <Newspaper className="size-4" />;
}

function getScenarioTone(scenario: AlertScenario) {
  if (scenario === "price_above") {
    return "border-emerald-500/25 bg-emerald-500/10 text-emerald-400";
  }
  if (scenario === "price_below") {
    return "border-rose-500/25 bg-rose-500/10 text-rose-400";
  }
  return "border-sky-500/25 bg-sky-500/10 text-sky-400";
}

export function ScenarioIcon({ scenario, className }: { scenario: AlertScenario; className?: string }) {
  return (
    <span
      title={getScenarioLabel(scenario)}
      className={cn(
        "flex size-9 shrink-0 items-center justify-center rounded-xl border",
        getScenarioTone(scenario),
        className
      )}
    >
      {getScenarioIcon(scenario)}
      <span className="sr-only">{getScenarioLabel(scenario)}</span>
    </span>
  );
}
