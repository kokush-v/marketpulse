import { formatAlertSubtitle, formatRelativeDate, formatTriggerMode, getScenarioLabel, isPriceScenario } from "@/features/alerts/lib/alert-builder";
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

  it("formats news alerts without threshold details", () => {
    expect(formatAlertSubtitle(createAlert({ scenario: "coin_news", trigger_mode: null, threshold_value: null }))).toBe(
      "Any new coin news",
    );
  });

  it("formats percent-based price alerts from the current baseline", () => {
    expect(formatAlertSubtitle(createAlert({ trigger_mode: "percent", threshold_value: 7.5 }))).toBe(
      "Up 7.5% from current baseline",
    );
    expect(
      formatAlertSubtitle(
        createAlert({
          scenario: "price_below",
          trigger_mode: "percent",
          threshold_value: 3,
        }),
      ),
    ).toBe("Down 3% from current baseline");
  });

  it("formats currency-based price alerts with comparator text", () => {
    expect(formatAlertSubtitle(createAlert({ threshold_value: 12345.67 }))).toBe("Above $12,345.67");
    expect(formatAlertSubtitle(createAlert({ scenario: "price_below", threshold_value: 980 }))).toBe("Below $980");
  });

  it("formats trigger mode labels for ui summaries", () => {
    expect(formatTriggerMode("percent")).toBe("% move");
    expect(formatTriggerMode("currency")).toBe("$ target");
    expect(formatTriggerMode(undefined)).toBe("Scenario");
  });

  it("formats timestamps into a readable short label", () => {
    expect(formatRelativeDate("2026-07-13T09:10:00.000Z")).toMatch(/^Jul 13,/);
  });
});
