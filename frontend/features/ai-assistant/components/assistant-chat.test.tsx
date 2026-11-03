import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { AssistantConversationResponse } from "@/src/api/generated/models/assistantConversationResponse";

jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => children,
}));
jest.mock("remark-gfm", () => ({ __esModule: true, default: jest.fn() }));

import { ChatMessage, CompactionDivider, getSuggestedReplyVisibleMessageIds } from "./assistant-chat";
import { PendingActionCard } from "./pending-action-card";

function conversationMessages(...messages: Array<Partial<AssistantConversationResponse["messages"][number]>>): AssistantConversationResponse["messages"] {
  return messages.map((message, index) => ({
    id: `message-${index + 1}`,
    role: "assistant",
    content: "Message",
    created_at: "2026-09-07T00:00:00Z",
    ...message,
  }));
}

describe("PendingActionCard", () => {
  it("uses chat guidance instead of confirmation controls for a pending action", () => {
    render(
      <PendingActionCard
        action={{
          id: "10000000-0000-4000-8000-000000000000",
          action_type: "create_alert",
          status: "pending",
          summary: {
            title: "Create alert for Solana (SOL)",
            details: ["Price above 150 USD"],
          },
        }}
      />,
    );

    expect(screen.getByText("Reply in chat to confirm or cancel this action.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /confirm/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /cancel/i })).not.toBeInTheDocument();
  });
});

describe("CompactionDivider", () => {
  it("renders a muted context compacted divider", () => {
    render(<CompactionDivider />);

    expect(screen.getByRole("separator", { name: "Context compacted" })).toHaveTextContent("Context compacted");
  });
});

describe("getSuggestedReplyVisibleMessageIds with compaction markers", () => {
  it("ignores markers when deciding which suggested replies stay visible", () => {
    const visible = getSuggestedReplyVisibleMessageIds(
      conversationMessages(
        { role: "user" },
        { role: "assistant", suggested_replies: ["Show news"] },
        { role: "compaction", content: "Context compacted" },
      ),
    );

    expect([...visible]).toEqual(["message-2"]);
  });
});

describe("ChatMessage", () => {
  it("hides earlier suggested replies after a later typed message", () => {
    const visibleMessageIds = getSuggestedReplyVisibleMessageIds(
      conversationMessages(
        { id: "assistant-1", suggested_replies: ["Tell me more"] },
        { id: "user-1", role: "user", content: "What about Bitcoin?" },
        { id: "assistant-2", suggested_replies: ["Show recent news"] },
      ),
    );

    expect(visibleMessageIds).toEqual(new Set(["assistant-2"]));
  });

  it("hides earlier suggested replies after a selected suggestion is recorded", () => {
    const visibleMessageIds = getSuggestedReplyVisibleMessageIds(
      conversationMessages(
        { id: "assistant-1", suggested_replies: ["Compare prices"] },
        { id: "user-1", role: "user", content: "Compare prices" },
      ),
    );

    expect(visibleMessageIds).toEqual(new Set());
  });

  it("sends a pending-action quick reply through the normal message callback", async () => {
    const user = userEvent.setup();
    const onSuggestedReply = jest.fn();

    render(
      <ChatMessage
        messageId="message-1"
        role="assistant"
        content="Please confirm the action."
        suggestedReplies={["Yes, confirm", "No, cancel"]}
        onSuggestedReply={onSuggestedReply}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Yes, confirm" }));

    expect(onSuggestedReply).toHaveBeenCalledWith("message-1", "Yes, confirm");
  });

  it("keeps the retry action with a failed user message", async () => {
    const user = userEvent.setup();
    const onRetry = jest.fn();

    render(
      <ChatMessage
        role="user"
        content="Yes, confirm"
        errorMessage="Unable to send the message."
        onRetry={onRetry}
      />,
    );

    await user.click(screen.getByRole("button", { name: /retry/i }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("shows a sources block under an assistant message with sources", () => {
    render(
      <ChatMessage
        role="assistant"
        content="Bitcoin trades at $100,000."
        sources={[
          {
            kind: "marketpulse",
            label: "MarketPulse knowledge",
            title: "Bitcoin (BTC) market data",
            url: null,
            updated_at: "2026-11-03T08:00:00Z",
            stale: false,
          },
        ]}
      />,
    );

    expect(screen.getByRole("region", { name: "Sources" })).toBeInTheDocument();
  });

  it("shows no sources block for an assistant message without sources", () => {
    render(<ChatMessage role="assistant" content="I can help with MarketPulse data." sources={[]} />);
    render(<ChatMessage role="assistant" content="An earlier persisted answer." />);

    expect(screen.queryByRole("region", { name: "Sources" })).not.toBeInTheDocument();
  });
});
