"use client";

import * as React from "react";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import {
  getGetConversationAssistantConversationsConversationIdGetQueryKey,
  useSubmitMessageFeedbackAssistantConversationsConversationIdMessagesMessageIdFeedbackPost,
} from "@/src/api/generated/ai-assistant/ai-assistant";
import type { AssistantConversationResponse } from "@/src/api/generated/models/assistantConversationResponse";
import type { AssistantMessageFeedbackResponse } from "@/src/api/generated/models/assistantMessageFeedbackResponse";
import type { SubmitAssistantMessageFeedbackRequestRating } from "@/src/api/generated/models/submitAssistantMessageFeedbackRequestRating";
import { ApiRequestError } from "@/src/api/http-client";
import { Button } from "@/shared/components/ui/button";
import { cn } from "@/shared/lib/utils";

type Rating = SubmitAssistantMessageFeedbackRequestRating;

const RATING_LABELS: Record<Rating, string> = {
  positive: "Helpful",
  negative: "Not helpful",
};

const REASON_MAX_LENGTH = 1000;

type MessageFeedbackProps = {
  conversationId: string;
  messageId: string;
  feedback?: AssistantMessageFeedbackResponse | null;
};

export function MessageFeedback({ conversationId, messageId, feedback }: MessageFeedbackProps) {
  const queryClient = useQueryClient();
  const submitFeedback = useSubmitMessageFeedbackAssistantConversationsConversationIdMessagesMessageIdFeedbackPost();
  const [submitted, setSubmitted] = React.useState<AssistantMessageFeedbackResponse | null>(null);
  const [selected, setSelected] = React.useState<Rating | null>(null);
  const [reason, setReason] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);

  const stored = feedback ?? submitted;
  if (stored) {
    const Icon = stored.rating === "positive" ? ThumbsUp : ThumbsDown;
    return (
      <p className="mt-2 inline-flex items-center gap-1.5 text-xs text-muted-foreground">
        <Icon className="size-3.5 fill-current text-foreground" aria-hidden="true" />
        You rated this response: {RATING_LABELS[stored.rating]}
      </p>
    );
  }

  const conversationQueryKey = getGetConversationAssistantConversationsConversationIdGetQueryKey(conversationId);

  const cancel = () => {
    setSelected(null);
    setReason("");
    setError(null);
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selected || submitFeedback.isPending) {
      return;
    }
    setError(null);
    try {
      const result = await submitFeedback.mutateAsync({
        conversationId,
        messageId,
        data: { rating: selected, reason: reason.trim() || null },
      });
      setSubmitted(result);
      queryClient.setQueryData<AssistantConversationResponse>(conversationQueryKey, (conversation) =>
        conversation
          ? {
              ...conversation,
              messages: conversation.messages.map((message) =>
                message.id === messageId ? { ...message, feedback: result } : message,
              ),
            }
          : conversation,
      );
    } catch (submitError) {
      if (submitError instanceof ApiRequestError && submitError.status === 409) {
        setError("This response has already been rated.");
        await queryClient.invalidateQueries({ queryKey: conversationQueryKey });
        return;
      }
      setError("Unable to submit your rating. Please try again.");
    }
  };

  return (
    <div className="mt-2">
      <div className="flex items-center gap-1" role="group" aria-label="Rate this response">
        {(["positive", "negative"] as const).map((rating) => {
          const Icon = rating === "positive" ? ThumbsUp : ThumbsDown;
          const isSelected = selected === rating;
          return (
            <Button
              key={rating}
              type="button"
              variant="ghost"
              size="icon"
              className={cn("size-7 text-muted-foreground", isSelected && "bg-accent text-foreground")}
              aria-label={RATING_LABELS[rating]}
              aria-pressed={isSelected}
              disabled={submitFeedback.isPending}
              onClick={() => {
                setSelected(rating);
                setError(null);
              }}
            >
              <Icon className={cn("size-3.5", isSelected && "fill-current")} />
            </Button>
          );
        })}
      </div>
      {selected ? (
        <form onSubmit={submit} className="mt-2 flex flex-col gap-2">
          <textarea
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            maxLength={REASON_MAX_LENGTH}
            rows={2}
            placeholder="Tell us why (optional)"
            aria-label="Reason for your rating (optional)"
            disabled={submitFeedback.isPending}
            className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-xs outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
          />
          {error ? (
            <p role="alert" className="text-xs text-destructive">
              {error}
            </p>
          ) : null}
          <div className="flex gap-2">
            <Button type="submit" size="sm" className="h-7 px-3 text-xs" disabled={submitFeedback.isPending}>
              {submitFeedback.isPending ? "Submitting…" : "Submit"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-3 text-xs"
              disabled={submitFeedback.isPending}
              onClick={cancel}
            >
              Cancel
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
