import type { ListAlertsAlertsGetParams } from "@/src/api/generated/models/listAlertsAlertsGetParams";

import type { AlertScenario } from "./alert-builder";

export type StatusFilter = "all" | "active" | "paused";
export type ScenarioFilter = "all" | AlertScenario;

export interface AlertFilters {
  status: StatusFilter;
  scenario: ScenarioFilter;
  search: string;
}

export const DEFAULT_ALERT_FILTERS: AlertFilters = {
  status: "all",
  scenario: "all",
  search: "",
};

export function hasActiveFilters(filters: AlertFilters): boolean {
  return filters.status !== "all" || filters.scenario !== "all" || filters.search.trim().length > 0;
}

export function toListAlertsParams(filters: AlertFilters): ListAlertsAlertsGetParams | undefined {
  const params: ListAlertsAlertsGetParams = {};
  const search = filters.search.trim();

  if (filters.status !== "all") {
    params.status = filters.status;
  }
  if (filters.scenario !== "all") {
    params.scenario = filters.scenario;
  }
  if (search.length > 0) {
    params.q = search;
  }

  return Object.keys(params).length > 0 ? params : undefined;
}
