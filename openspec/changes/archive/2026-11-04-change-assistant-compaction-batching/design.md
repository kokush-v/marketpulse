## Context

`_compact_conversation_if_needed` builds the recent window with `select_recent_messages` over the full history plus the pending message and summarizes any out-of-window messages with `sequence > summarized_through_sequence`. `_get_graph_response` passes the full history to the graph, and `AssistantGraph._bounded_messages` keeps the last messages within the limits. Because the window slides, almost every message after the window fills causes a compaction.

## Decisions

### Context messages

The context is the user and assistant messages with `sequence > summarized_through_sequence` (all of them when there is no summary), plus the pending user message. `_get_graph_response` passes only these messages to the graph. `_bounded_messages` stays as a safety cap for a single oversized exchange and for tool messages inside a graph run.

### Trigger

Compact when the context including the pending message has more than `assistant_max_context_messages` messages or more than `assistant_max_context_characters` characters.

### What is summarized

The retained exchange is the stored messages from the latest stored user message onward. Everything in the context before it is summarized together with the previous summary, `summarized_through_sequence` advances to the last summarized message, and one marker is recorded. If nothing precedes the retained exchange, no compaction runs.

After compaction the model sees the summary, the retained exchange, and the pending message, so the next compaction happens only after the context fills up again.

### Unchanged behavior

Summary prompt, pending confirmation context message, marker rows and display, and failure handling (no marker, previous summary kept, retry on a later message) stay as they are. When compaction fails, the graph still receives the unsummarized context bounded by `_bounded_messages`.

## Risks

- One compaction now summarizes up to a full context of messages in a single call, so that call is larger; it happens once per filled context instead of on every message.

## Rollback

Revert the service changes; stored summaries and markers remain compatible.
