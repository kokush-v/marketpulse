# Proposal: Document MCP Workflow Guidance

## Problem

MarketPulse now has GitHub and Linear MCP access, but repository and skill instructions do not yet define when those MCP tools are appropriate. Without explicit guidance, agents may create issues or PRs before OpenSpec validation, implementation, QA, or review are complete.

## Scope

- Add repository-level MCP usage rules for GitHub and Linear.
- Add repository-level role-agent orchestration rules for spec, implementation, QA, and review phases.
- Add Linear MCP gating rules to the MarketPulse OpenSpec change creation skill.
- Add GitHub MCP gating rules to the MarketPulse review skill.
- Capture the expected MCP workflow order in OpenSpec.

## Out of Scope

- Implementing application code.
- Creating Linear issues.
- Creating GitHub pull requests.
- Changing GitHub, Linear, or MCP server configuration.
- Adding automated MCP calls.

## Acceptance Criteria

- `AGENTS.md` documents allowed GitHub MCP and Linear MCP usage.
- `AGENTS.md` documents when to use separate role-specific agents for spec, implementation, QA, and review phases.
- `AGENTS.md` instructs agents to reuse already-open role agents for the same active change when practical.
- `marketpulse-create-openspec-change` requires proposal, tasks, nested specs, and strict validation before Linear issue creation is suggested.
- `marketpulse-review-agent` limits GitHub MCP use to post-review branch/PR actions and forbids automatic merge or branch deletion.
- The OpenSpec change validates with `openspec validate document-mcp-workflow-guidance --strict`.

## Related Specs

- `openspec/specs/development-workflow/spec.md` (new capability)
