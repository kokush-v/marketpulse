import type { AlertResponse } from "@/src/api/generated/models/alertResponse";
import type { AlertResponseScenario } from "@/src/api/generated/models/alertResponseScenario";
import type { AlertResponseTriggerMode } from "@/src/api/generated/models/alertResponseTriggerMode";

export type PriceScenario = "price_above" | "price_below";
export type AlertScenario = AlertResponseScenario;
export type TriggerMode = AlertResponseTriggerMode;

export function formatRelativeDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function getScenarioLabel(scenario: AlertScenario): string {
  switch (scenario) {
    case "price_above":
      return "Price above";
    case "price_below":
      return "Price below";
    case "coin_news":
      return "News";
  }
}

export function isPriceScenario(scenario: AlertScenario): scenario is PriceScenario {
  return scenario === "price_above" || scenario === "price_below";
}

export function formatAlertSubtitle(alert: AlertResponse): string {
  if (alert.scenario === "coin_news") {
    return "Any new coin news";
  }

  if (alert.trigger_mode === "percent") {
    const direction = alert.scenario === "price_above" ? "Up" : "Down";
    return `${direction} ${alert.threshold_value ?? 0}% from current baseline`;
  }

  const comparator = alert.scenario === "price_above" ? "Above" : "Below";
  return `${comparator} $${Number(alert.threshold_value ?? 0).toLocaleString()}`;
}

export function formatTriggerMode(mode?: TriggerMode): string {
  if (mode === "percent") {
    return "% move";
  }
  if (mode === "currency") {
    return "$ target";
  }
  return "Scenario";
}
