import type { AssistantConversationResponse } from "@/src/api/generated/models/assistantConversationResponse";

export function PendingActionCard({
  action,
}: {
  action: NonNullable<AssistantConversationResponse["messages"][number]["pending_action"]>;
}) {
  const isPending = action.status === "pending";

  return (
    <div className="mt-3 rounded-xl border border-border/70 bg-muted/30 p-3 text-sm">
      <p className="font-medium">{action.summary.title}</p>
      <ul className="mt-2 space-y-1 text-xs leading-5 text-muted-foreground">
        {action.summary.details.map((detail) => <li key={detail}>{detail}</li>)}
      </ul>
      {isPending ? (
        <p className="mt-3 text-xs text-muted-foreground">
          Reply in chat to confirm or cancel this action.
        </p>
      ) : (
        <p className="mt-3 text-xs text-muted-foreground">
          {action.status === "confirmed"
            ? "Confirmed"
            : action.status === "cancelled"
              ? "Cancelled"
              : "Expired"}
        </p>
      )}
    </div>
  );
}
