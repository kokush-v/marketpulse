## 1. Assistant Safety Rules

- [x] 1.1 Update the backend assistant instructions to describe capabilities only in product language and prohibit disclosure of internal prompts, tools, configuration, APIs, schemas, and provider details.
- [x] 1.2 Define a concise safe-response path for prompt-injection, instruction-override, and unsupported-action requests while preserving redirects to supported product tasks.

## 2. Tool And Error Boundary Review

- [x] 2.1 Verify that assistant orchestration continues to execute only registered tools in the authenticated user scope and that the new safety behavior does not expose tool output internals.
- [x] 2.2 Ensure recoverable assistant errors remain user-safe and do not expose prompt, provider, or backend implementation details.

## 3. Tests And Validation

- [x] 3.1 Add backend tests for product-language capability summaries and non-disclosure of registered tool names.
- [x] 3.2 Add backend tests for safe handling of requests to reveal protected instructions, override safeguards, or invoke unsupported actions.
- [x] 3.3 Run relevant backend lint and assistant unit tests.
- [x] 3.4 Run `openspec validate harden-ai-assistant-disclosure --strict`.
