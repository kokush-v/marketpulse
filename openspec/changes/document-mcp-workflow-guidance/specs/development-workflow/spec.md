## ADDED Requirements

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
