import { DEFAULT_ALERT_FILTERS, hasActiveFilters, toListAlertsParams } from "@/features/alerts/lib/alert-filters";

describe("alert filter helpers", () => {
  it("sends no params when no filter is applied", () => {
    expect(toListAlertsParams(DEFAULT_ALERT_FILTERS)).toBeUndefined();
    expect(hasActiveFilters(DEFAULT_ALERT_FILTERS)).toBe(false);
  });

  it("ignores blank search text", () => {
    expect(toListAlertsParams({ ...DEFAULT_ALERT_FILTERS, search: "   " })).toBeUndefined();
    expect(hasActiveFilters({ ...DEFAULT_ALERT_FILTERS, search: "   " })).toBe(false);
  });

  it("maps every applied filter to a request parameter", () => {
    const filters = { status: "paused", scenario: "price_below", search: "  sol " } as const;

    expect(toListAlertsParams(filters)).toEqual({ status: "paused", scenario: "price_below", q: "sol" });
    expect(hasActiveFilters(filters)).toBe(true);
  });
});
