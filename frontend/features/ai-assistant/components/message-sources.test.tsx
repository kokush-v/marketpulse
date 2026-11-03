import { render, screen } from "@testing-library/react";

import { MessageSources } from "./message-sources";

describe("MessageSources", () => {
  it("renders news sources with a link that opens in a new tab", () => {
    render(
      <MessageSources
        sources={[
          {
            kind: "news",
            label: "Example News",
            title: "Bitcoin update",
            url: "https://example.com/bitcoin",
            updated_at: "2026-11-03T08:00:00Z",
            stale: false,
          },
        ]}
      />,
    );

    expect(screen.getByRole("region", { name: "Sources" })).toBeInTheDocument();
    expect(screen.getByText("Example News")).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /Bitcoin update/ });
    expect(link).toHaveAttribute("href", "https://example.com/bitcoin");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.queryByText("May be outdated")).not.toBeInTheDocument();
  });

  it("renders MarketPulse sources without a link and marks stale data", () => {
    render(
      <MessageSources
        sources={[
          {
            kind: "marketpulse",
            label: "MarketPulse knowledge",
            title: "Bitcoin (BTC) market data",
            url: null,
            updated_at: "2026-11-03T07:00:00Z",
            stale: true,
          },
        ]}
      />,
    );

    expect(screen.getByText("MarketPulse knowledge")).toBeInTheDocument();
    expect(screen.getByText("Bitcoin (BTC) market data")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByText("May be outdated")).toBeInTheDocument();
  });

  it("renders nothing when there are no sources", () => {
    const { container } = render(<MessageSources sources={[]} />);

    expect(container).toBeEmptyDOMElement();
  });
});
