import {
  buildAlertSummary,
  getChartDomain,
  getProjectedPrice,
  priceFromChartY,
  thresholdInputFromPrice,
} from "@/features/alerts/lib/alert-draft";

describe("getChartDomain", () => {
  it("fits the axis to the price range with padding instead of starting at zero", () => {
    const domain = getChartDomain([68000, 70000, 72000]);

    expect(domain).not.toBeNull();
    const [low, high] = domain as [number, number];
    expect(low).toBeLessThan(68000);
    expect(low).toBeGreaterThan(60000);
    expect(high).toBeGreaterThan(72000);
    expect(high).toBeLessThan(80000);
  });

  it("handles a flat series and empty data", () => {
    const [low, high] = getChartDomain([100, 100]) as [number, number];
    expect(low).toBeLessThan(100);
    expect(high).toBeGreaterThan(100);
    expect(getChartDomain([])).toBeNull();
  });
});

describe("priceFromChartY", () => {
  const domain: [number, number] = [100, 200];

  it("maps the plot top and bottom to the domain edges", () => {
    expect(priceFromChartY({ chartY: 10, plotTop: 10, plotBottom: 110, domain })).toBe(200);
    expect(priceFromChartY({ chartY: 110, plotTop: 10, plotBottom: 110, domain })).toBe(100);
    expect(priceFromChartY({ chartY: 60, plotTop: 10, plotBottom: 110, domain })).toBe(150);
  });

  it("clamps clicks outside the plot area", () => {
    expect(priceFromChartY({ chartY: 0, plotTop: 10, plotBottom: 110, domain })).toBe(200);
    expect(priceFromChartY({ chartY: 500, plotTop: 10, plotBottom: 110, domain })).toBe(100);
  });
});

describe("thresholdInputFromPrice", () => {
  it("returns the price in currency mode and the distance from current in percent mode", () => {
    expect(thresholdInputFromPrice(70123.4, "currency", 68000)).toBe("70123");
    expect(thresholdInputFromPrice(1.234, "currency", 1)).toBe("1.23");
    expect(thresholdInputFromPrice(110, "percent", 100)).toBe("10.00");
    expect(thresholdInputFromPrice(90, "percent", 100)).toBe("10.00");
  });

  it("rejects invalid input", () => {
    expect(thresholdInputFromPrice(-1, "currency", 100)).toBeNull();
    expect(thresholdInputFromPrice(100, "percent", 0)).toBeNull();
  });
});

describe("getProjectedPrice", () => {
  it("projects percent triggers from the current price", () => {
    expect(getProjectedPrice({ currentPrice: 100, scenario: "price_above", triggerMode: "percent", thresholdValue: 10 })).toBeCloseTo(110);
    expect(getProjectedPrice({ currentPrice: 100, scenario: "price_below", triggerMode: "percent", thresholdValue: 10 })).toBeCloseTo(90);
    expect(getProjectedPrice({ currentPrice: 100, scenario: "coin_news", triggerMode: "percent", thresholdValue: 10 })).toBeNull();
  });
});

describe("buildAlertSummary", () => {
  const base = {
    symbol: "BTC",
    scenario: "price_above" as const,
    triggerMode: "currency" as const,
    thresholdValue: 70000,
    projectedPrice: 70000,
    timeBehavior: "one_time" as const,
  };

  it("describes a one-time price alert on one line", () => {
    expect(buildAlertSummary(base)).toBe("Notify me when BTC rises above $70,000, once.");
  });

  it("prompts for a trigger value when none is set", () => {
    expect(buildAlertSummary({ ...base, thresholdValue: null, projectedPrice: null })).toBe(
      "Choose a trigger value, or click the chart.",
    );
  });

  it("describes news alerts without a trigger", () => {
    expect(buildAlertSummary({ ...base, scenario: "coin_news", thresholdValue: null, projectedPrice: null })).toBe(
      "Notify me about any new BTC article, once.",
    );
  });

  it("includes the daily range", () => {
    expect(
      buildAlertSummary({
        ...base,
        timeBehavior: "daily_recurring",
        recurringStart: new Date(2026, 5, 4),
        recurringEnd: new Date(2026, 5, 30),
      }),
    ).toBe("Notify me when BTC rises above $70,000, daily, Jun 4 – Jun 30, 2026.");
  });

  it("guides the user while the coin is not chosen", () => {
    expect(buildAlertSummary({ ...base, symbol: null })).toBe("Choose a coin to get started.");
  });
});
