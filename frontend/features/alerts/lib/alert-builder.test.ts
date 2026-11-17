import { formatAlertTiming, getScenarioLabel, isPriceScenario } from "@/features/alerts/lib/alert-builder";
import type { AlertResponse } from "@/src/api/generated/models/alertResponse";

function createAlert(overrides: Partial<AlertResponse> = {}): AlertResponse {
  return {
    id: "alert-1",
    asset_id: "btc",
    symbol: "BTC",
    name: "Bitcoin",
    image_url: null,
    status: "active",
    scenario: "price_above",
    time_behavior: "one_time",
    trigger_mode: "currency",
    threshold_value: 12345,
    baseline_price: null,
    recurring_start_date: null,
    recurring_end_date: null,
    rule_summary: "Above $12,345",
    time_summary: "One-time",
    available_actions: ["edit", "pause", "delete"],
    created_at: "2026-07-13T09:10:00.000Z",
    updated_at: "2026-07-13T09:10:00.000Z",
    ...overrides,
  };
}

describe("alert-builder helpers", () => {
  it("returns readable labels for supported scenarios", () => {
    expect(getScenarioLabel("price_above")).toBe("Price above");
    expect(getScenarioLabel("price_below")).toBe("Price below");
    expect(getScenarioLabel("coin_news")).toBe("News");
  });

  it("identifies price scenarios correctly", () => {
    expect(isPriceScenario("price_above")).toBe(true);
    expect(isPriceScenario("price_below")).toBe(true);
    expect(isPriceScenario("coin_news")).toBe(false);
  });

  it("shows one-time alerts as one-time", () => {
    expect(formatAlertTiming(createAlert())).toBe("One-time");
  });

  it("formats recurring windows with readable dates instead of raw ISO dates", () => {
    const recurring = createAlert({
      time_behavior: "daily_recurring",
      recurring_start_date: "2026-06-04",
      recurring_end_date: "2026-06-30",
    });

    expect(formatAlertTiming(recurring)).toBe("Daily · Jun 4 – Jun 30, 2026");
  });

  it("includes both years when a recurring window crosses a year boundary", () => {
    const recurring = createAlert({
      time_behavior: "daily_recurring",
      recurring_start_date: "2026-12-20",
      recurring_end_date: "2027-01-05",
    });

    expect(formatAlertTiming(recurring)).toBe("Daily · Dec 20, 2026 – Jan 5, 2027");
  });
});
