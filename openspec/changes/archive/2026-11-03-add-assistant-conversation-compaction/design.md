## Context

`AssistantService._get_graph_response` converts all stored user and assistant messages to LangChain messages, and `AssistantGraph._bounded_messages` keeps the last `ASSISTANT_MAX_CONTEXT_MESSAGES` (10) within `ASSISTANT_MAX_CONTEXT_CHARACTERS` (12 000). Older messages are dropped. Pending actions are stored in `assistant_pending_actions` with `expires_at`; yes/no decisions are resolved before the model is called. `AssistantMessageResponse.role` is `Literal["user", "assistant"]`.

## Decisions

### Persistence

- `assistant_conversations.context_summary` (nullable text) and `assistant_conversations.summarized_through_sequence` (nullable int): the summary covers all user and assistant messages with `sequence <= summarized_through_sequence`.
- Compaction markers are rows in `assistant_messages` with role `compaction` and fixed content; they are inserted at the point in history where compaction happened. They are owned through the conversation and deleted with it.

### When to compact

Before calling the graph in `send_message`, compute the user and assistant messages outside the recent window (the same window the graph uses). If any of them have `sequence > summarized_through_sequence`, run compaction:

1. Call the model with a summarization prompt, the previous summary, and the newly out-of-window messages.
2. Store the new summary and advance `summarized_through_sequence`.
3. Append a `compaction` marker message.

Compaction runs in the request path so the current response uses the new summary.

### Summary content

The summarization prompt asks for a concise English summary (max ~1 500 characters) with sections in this priority order:

1. coins the user interacted with and what was done or asked for each;
2. facts and preferences the user stated about themselves;
3. decisions and completed or declined actions;
4. open questions.

The summary must mark any prices or figures as historical. The summary is internal: never shown to the user.

### Context assembly

Model input order: system prompt; a system message with the summary (labeled as earlier conversation context, figures not current); a system message describing the current non-expired pending action (type and display summary) when one exists; the recent window messages. Compaction markers are excluded. The system prompt states that summary figures are historical and current data must come from tools (consistent with `add-assistant-response-sources`).

### Failure handling

If the summarization call fails or returns empty output, log the failure, keep the previous summary and `summarized_through_sequence`, add no marker, and continue with the user's request. The next request retries compaction.

### API and frontend

`AssistantMessageRole` becomes `Literal["user", "assistant", "compaction"]`. `assistant-chat.tsx` renders `compaction` messages as a muted divider ("Context compacted") without suggested replies, charts, sources, or actions. Suggested-reply visibility rules continue to consider only user and assistant messages.

## Risks

- Extra latency and Groq usage on requests that trigger compaction; bounded by summarizing only newly out-of-window messages.
- Summary quality depends on the model; eval scenarios cover recalling an early coin after compaction.

## Rollback

Stop compacting and ignore the summary; marker rows can be filtered out or removed by a down migration.
