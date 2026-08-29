import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => children,
}));
jest.mock("remark-gfm", () => ({ __esModule: true, default: jest.fn() }));

import { ChatMessage } from "./assistant-chat";
import { PendingActionCard } from "./pending-action-card";

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

describe("ChatMessage", () => {
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
});
