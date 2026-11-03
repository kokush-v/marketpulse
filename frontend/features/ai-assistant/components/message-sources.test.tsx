import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MessageSources } from "./message-sources";

describe("MessageSources", () => {
  it("is collapsed by default with unique labels and the source count", async () => {
    render(
      <MessageSources
        sources={[
          { kind: "news", label: "newsBTC", title: "First", url: "https://example.com/1", updated_at: null, stale: false },
          { kind: "news", label: "Crypto Briefing", title: "Second", url: "https://example.com/2", updated_at: null, stale: false },
          { kind: "news", label: "newsBTC", title: "Third", url: "https://example.com/3", updated_at: null, stale: true },
        ]}
      />,
    );

    const toggle = screen.getByRole("button", { name: /Sources/ });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(toggle).toHaveTextContent("newsBTC · Crypto Briefing");
    expect(toggle).toHaveTextContent("(3)");
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.queryByText("May be outdated")).not.toBeInTheDocument();

    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getAllByRole("link")).toHaveLength(3);
    expect(screen.getByText("May be outdated")).toBeInTheDocument();

    await userEvent.click(toggle);
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("renders news sources with a link that opens in a new tab", async () => {
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
    await userEvent.click(screen.getByRole("button", { name: /Sources/ }));
    expect(screen.getByText("Example News")).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /Bitcoin update/ });
    expect(link).toHaveAttribute("href", "https://example.com/bitcoin");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.queryByText("May be outdated")).not.toBeInTheDocument();
  });

  it("renders MarketPulse sources without a link and marks stale data", async () => {
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

    expect(screen.getByRole("button", { name: /Sources/ })).toHaveTextContent("MarketPulse knowledge");
    expect(screen.getByRole("button", { name: /Sources/ })).toHaveTextContent("(1)");
    await userEvent.click(screen.getByRole("button", { name: /Sources/ }));
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
