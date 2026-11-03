import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const mutateAsync = jest.fn();

jest.mock("@/src/api/http-client", () => ({
  ApiRequestError: class ApiRequestError extends Error {
    constructor(
      message: string,
      public readonly status: number,
    ) {
      super(message);
    }
  },
}));

jest.mock("@/src/api/generated/ai-assistant/ai-assistant", () => ({
  getGetConversationAssistantConversationsConversationIdGetQueryKey: (id: string) => [`/assistant/conversations/${id}`],
  useSubmitMessageFeedbackAssistantConversationsConversationIdMessagesMessageIdFeedbackPost: () => ({
    mutateAsync,
    isPending: false,
  }),
}));

import { ApiRequestError } from "@/src/api/http-client";
import { MessageFeedback } from "./message-feedback";

function renderFeedback(feedback?: { rating: "positive" | "negative"; reason?: string | null; created_at: string }) {
  const queryClient = new QueryClient();
  const invalidateQueries = jest.spyOn(queryClient, "invalidateQueries");
  render(
    <QueryClientProvider client={queryClient}>
      <MessageFeedback conversationId="conversation-1" messageId="message-1" feedback={feedback} />
    </QueryClientProvider>,
  );
  return { invalidateQueries };
}

describe("MessageFeedback", () => {
  beforeEach(() => {
    mutateAsync.mockReset();
  });

  it("submits the last selected rating with a trimmed reason and shows it read-only", async () => {
    const user = userEvent.setup();
    mutateAsync.mockResolvedValue({ rating: "negative", reason: "Wrong price", created_at: "2026-11-03T00:00:00Z" });
    renderFeedback();

    await user.click(screen.getByRole("button", { name: "Helpful" }));
    await user.click(screen.getByRole("button", { name: "Not helpful" }));
    expect(screen.getByRole("button", { name: "Not helpful" })).toHaveAttribute("aria-pressed", "true");
    await user.type(screen.getByRole("textbox", { name: /reason/i }), "  Wrong price  ");
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      conversationId: "conversation-1",
      messageId: "message-1",
      data: { rating: "negative", reason: "Wrong price" },
    });
    expect(await screen.findByText("You rated this response: Not helpful")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Helpful" })).not.toBeInTheDocument();
  });

  it("submits a rating without a reason", async () => {
    const user = userEvent.setup();
    mutateAsync.mockResolvedValue({ rating: "positive", reason: null, created_at: "2026-11-03T00:00:00Z" });
    renderFeedback();

    await user.click(screen.getByRole("button", { name: "Helpful" }));
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(mutateAsync).toHaveBeenCalledWith(expect.objectContaining({ data: { rating: "positive", reason: null } }));
  });

  it("keeps the draft and shows an error when submission fails", async () => {
    const user = userEvent.setup();
    mutateAsync.mockRejectedValue(new Error("network"));
    renderFeedback();

    await user.click(screen.getByRole("button", { name: "Not helpful" }));
    await user.type(screen.getByRole("textbox", { name: /reason/i }), "Outdated");
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to submit your rating");
    expect(screen.getByRole("textbox", { name: /reason/i })).toHaveValue("Outdated");
    expect(screen.getByRole("button", { name: "Not helpful" })).toHaveAttribute("aria-pressed", "true");
  });

  it("refreshes the conversation when the response was already rated", async () => {
    const user = userEvent.setup();
    mutateAsync.mockRejectedValue(new ApiRequestError("Already rated", 409));
    const { invalidateQueries } = renderFeedback();

    await user.click(screen.getByRole("button", { name: "Helpful" }));
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("already been rated");
    await waitFor(() =>
      expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["/assistant/conversations/conversation-1"] }),
    );
  });

  it("cancel clears the selection without submitting", async () => {
    const user = userEvent.setup();
    renderFeedback();

    await user.click(screen.getByRole("button", { name: "Helpful" }));
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it("shows an existing rating as read-only after reload", () => {
    renderFeedback({ rating: "positive", reason: null, created_at: "2026-11-03T00:00:00Z" });

    expect(screen.getByText("You rated this response: Helpful")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
