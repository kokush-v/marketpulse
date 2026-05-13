# development-workflow Specification

## Purpose
TBD - created by archiving change document-mcp-workflow-guidance. Update Purpose after archive.
## Requirements
### Requirement: MCP usage follows OpenSpec workflow

The repository SHALL define when GitHub MCP and Linear MCP may be used during MarketPulse development.

GitHub MCP usage SHALL be limited to repository, branch, PR status, PR creation, PR metadata checks, and requested PR comments.

Linear MCP usage SHALL be limited to issues created from approved OpenSpec proposals, reading issue context, updating issue status, and adding implementation or review summaries.

MCP usage SHALL NOT bypass OpenSpec proposal, validation, implementation, QA, review, commit, archive, or PR sequencing.

#### Scenario: Create Linear issue after OpenSpec validation

- Given an OpenSpec change has `proposal.md`, `tasks.md`, and nested `specs/<capability>/spec.md`
- And `openspec validate <change-id> --strict` passes
- When a Linear issue is needed for tracking approved work
- Then Linear MCP may create an issue from the approved OpenSpec proposal

#### Scenario: Block Linear issue before OpenSpec validation

- Given an OpenSpec proposal is missing required artifacts or strict validation fails
- When a Linear issue is requested for the change
- Then Linear MCP must not create the issue
- And the missing OpenSpec or validation requirement must be reported

#### Scenario: Create GitHub PR after local review

- Given implementation, QA, and local review have passed for an OpenSpec change
- And the change has been committed and pushed to a branch
- When a pull request is needed
- Then GitHub MCP may read branch status and create a draft PR
- And GitHub MCP may add a review summary to the PR when requested

#### Scenario: Prevent automatic merge or branch deletion

- Given GitHub MCP is available
- When review or PR work is performed
- Then GitHub MCP must not merge PRs automatically
- And GitHub MCP must not delete branches automatically

### Requirement: OpenSpec phases use role-specific agents when appropriate

The repository SHALL define when separate role-specific agents should be used for MarketPulse OpenSpec workflow phases.

When subagent tooling is available and allowed by the current session instructions, the workflow SHALL use separate role-specific agents for spec, implementation, QA, and review phases.

Agents SHALL reuse an already-open role agent for the same active change when practical instead of spawning a duplicate agent.

Agents SHALL NOT spawn subagents for simple Q&A, status requests, or instruction-only edits unless the user explicitly asks for agent delegation.

#### Scenario: Use separate agents for implementation workflow phases

- Given an approved OpenSpec change is ready for implementation
- And subagent tooling is available and allowed
- When implementation, QA, and review are needed
- Then the coordinator uses an implementation agent for code changes
- And the coordinator uses a QA agent for verification
- And the coordinator uses a review agent for final review

#### Scenario: Reuse existing role agent for the same change

- Given a role-specific agent is already open for the active OpenSpec change
- When more work is needed for that same role and change
- Then the coordinator sends the follow-up work to the existing agent when practical
- And the coordinator avoids spawning a duplicate agent that would repeat the same context discovery

#### Scenario: Avoid agents for simple instruction edits

- Given the user requests a simple instruction-only edit
- And the user does not ask for subagent delegation
- When the edit can be completed directly
- Then the coordinator updates the instruction files without spawning role-specific agents

