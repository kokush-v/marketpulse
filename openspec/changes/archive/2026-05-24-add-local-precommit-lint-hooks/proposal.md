## Summary

Add local pre-commit lint enforcement for both backend and frontend code before a developer can create a Git commit.

## Problem

The repository already defines lint commands for backend and frontend code, but developers can still create commits without running them locally first. This increases the chance of avoidable lint failures reaching shared branches and CI.

## Proposed Solution

Introduce a local commit workflow that runs whole-codebase lint checks before commit creation:

- use Python `pre-commit` for backend-side hook orchestration
- use `husky` for frontend-side hook orchestration
- run the full backend lint command rather than checking only staged files
- run the full frontend lint command rather than checking only staged files
- block commit creation when either lint check fails

This change is intentionally limited to local developer hooks and does not change CI behavior.

## Scope

- Define required local pre-commit hook behavior for backend and frontend lint checks
- Cover full-codebase lint execution before local commits
- Specify blocking behavior when lint checks fail
- Cover developer-facing setup and validation expectations for the new local workflow

## Non-Goals

- Adding new CI jobs or changing existing CI quality gates
- Adding frontend typecheck requirements to the pre-commit flow
- Adding backend format-check requirements to the pre-commit flow
- Limiting checks to staged files only
- Introducing pre-push hooks or server-side Git hooks

## Impact

- Affected domain: `api-client-generation`
- Affected workflow: local developer commit workflow
- Developers will need local hook setup for both backend and frontend before relying on the automated lint gate
- Commit attempts will fail earlier when repository lint rules are violated
