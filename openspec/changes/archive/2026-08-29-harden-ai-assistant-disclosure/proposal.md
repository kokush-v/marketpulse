## Summary

Harden the AI assistant's conversational security so it describes capabilities in product language and refuses requests to reveal internal implementation details or override its operating instructions.

## Problem

The assistant can currently expose registered tool names and other implementation-oriented details in normal conversation. This leaks unnecessary information about the application's internal surface and makes social-engineering and prompt-injection attempts easier to pursue.

## Proposed Solution

Add assistant response-safety requirements that require product-language descriptions of capabilities, prohibit disclosure of internal prompts, tool names, configuration, and implementation details, and define a safe response to prompt-injection or instruction-override attempts. The assistant will redirect the user to supported product tasks without revealing protected internals.

## Scope

Affected domain: `ai-assistant`.

This change covers:

- user-facing capability descriptions without internal function names, API details, model configuration, or orchestration details;
- safe refusals for requests to disclose system/developer instructions, hidden prompts, tool inventories, credentials, or backend implementation details;
- safe handling of requests that attempt to override instructions or cause unsupported actions;
- backend prompt/orchestration and focused automated tests for these response rules.

## Non-Goals

- adding new assistant tools or product capabilities;
- changing authenticated resource ownership or confirmation flows;
- attempting to identify every possible malicious prompt with a separate hard-coded rule;
- exposing a technical debugging interface to end users.

## Impact

The backend assistant prompt and response orchestration will gain explicit disclosure and prompt-injection guardrails. Existing assistant product workflows remain available, but internal implementation details are no longer presented to users. Focused backend tests will validate the required safe behavior.
