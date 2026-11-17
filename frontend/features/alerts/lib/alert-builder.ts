import { format, parseISO } from "date-fns";

import type { AlertResponse } from "@/src/api/generated/models/alertResponse";
import type { AlertResponseScenario } from "@/src/api/generated/models/alertResponseScenario";
import type { AlertResponseTriggerMode } from "@/src/api/generated/models/alertResponseTriggerMode";

export type PriceScenario = "price_above" | "price_below";
export type AlertScenario = AlertResponseScenario;
export type TriggerMode = AlertResponseTriggerMode;

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

function formatTimingDate(value: Date, withYear: boolean): string {
  return format(value, withYear ? "MMM d, yyyy" : "MMM d");
}

export function formatAlertTiming(alert: AlertResponse): string {
  if (alert.time_behavior === "daily_recurring" && alert.recurring_start_date && alert.recurring_end_date) {
    const start = parseISO(alert.recurring_start_date);
    const end = parseISO(alert.recurring_end_date);
    const sameYear = start.getFullYear() === end.getFullYear();

    return `Daily · ${formatTimingDate(start, !sameYear)} – ${formatTimingDate(end, true)}`;
  }

  return "One-time";
}
