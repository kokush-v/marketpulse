import * as React from "react";

export type AlertsView = "list" | "cards";

export const ALERTS_VIEW_STORAGE_KEY = "marketpulse.alerts.view";
const DEFAULT_VIEW: AlertsView = "list";

function isAlertsView(value: string | null): value is AlertsView {
  return value === "list" || value === "cards";
}

export function readStoredAlertsView(): AlertsView {
  try {
    const stored = window.localStorage.getItem(ALERTS_VIEW_STORAGE_KEY);
    return isAlertsView(stored) ? stored : DEFAULT_VIEW;
  } catch {
    // Browser storage can be blocked or unavailable; fall back to the default view.
    return DEFAULT_VIEW;
  }
}

export function useAlertsViewPreference(): [AlertsView, (view: AlertsView) => void] {
  const [view, setView] = React.useState<AlertsView>(DEFAULT_VIEW);

  React.useEffect(() => {
    setView(readStoredAlertsView());
  }, []);

  const updateView = React.useCallback((next: AlertsView) => {
    setView(next);
    try {
      window.localStorage.setItem(ALERTS_VIEW_STORAGE_KEY, next);
    } catch {
      // Ignore storage failures; the choice still applies for this visit.
    }
  }, []);

  return [view, updateView];
}
