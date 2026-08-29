import { render, screen } from "@testing-library/react";

import { PriceChartCard } from "./price-chart-card";

describe("PriceChartCard", () => {
  it("renders an accessible chart card for each returned series", () => {
    render(
      <PriceChartCard
        chart={{
          period: "7d",
          series: [
            {
              symbol: "BTC",
              name: "Bitcoin",
              points: [
                { time: "2026-08-28T00:00:00Z", price: 100000 },
                { time: "2026-08-29T00:00:00Z", price: 101000 },
              ],
            },
          ],
        }}
      />,
    );

    expect(screen.getByRole("region", { name: "Price chart for BTC" })).toBeInTheDocument();
    expect(screen.getByText("Price comparison")).toBeInTheDocument();
    expect(screen.getByText("7 days · USD")).toBeInTheDocument();
  });
});
