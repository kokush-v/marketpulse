## Context

The assistant is a backend-owned LangGraph workflow with registered tools. Tool schemas and names are necessary for the model to operate but are not user-facing product information. The model must remain useful when users ask what it can do while treating requests for its internal instructions, configuration, or tool inventory as untrusted.

## Decisions

### Product-facing capability boundary

The system prompt will distinguish between product capabilities and implementation details. It will instruct the model to describe only the former in user-facing language, such as market information, charts, personal watchlist review, and alert setup. It must not name registered tools or disclose prompt, provider, model, API, orchestration, or schema details.

### Prompt-injection and disclosure handling

The orchestration will give system-level instructions precedence over conversation content. Requests to reveal protected instructions or internals, override safeguards, impersonate system messages, or use unavailable capabilities receive a concise refusal and, where relevant, a redirect to a supported product task. Such a response must not echo protected content.

### Tool boundary remains authoritative

Prompt guidance supplements rather than replaces the existing backend tool allowlist and authenticated ownership checks. No user message can register a tool, broaden a tool's authorization scope, or bypass mutation confirmation.

## Risks And Mitigations

- A model may follow adversarial user wording despite the prompt: retain the backend-owned tool allowlist and add representative tests for capability and disclosure requests.
- Overly broad refusals may make ordinary support requests frustrating: permit high-level, product-language explanations of what the assistant can help with.

## Rollback

The new prompt/orchestration rules can be reverted without data migration or API-contract changes. Existing tool and authorization boundaries remain unchanged.
