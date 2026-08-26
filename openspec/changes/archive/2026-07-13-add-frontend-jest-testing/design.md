## Overview

This change introduces a frontend automated testing foundation for the Next.js application using Jest. The goal is to establish one approved baseline for local execution and CI enforcement while keeping the initial coverage scope intentionally focused.

## Decision

The project will use Jest as the required frontend automated test runner for unit and component tests.

The approved initial coverage scope is:

- `shared/lib` and `features/*/lib`
- `shared/hooks` and `features/*/hooks`
- critical interactive components that influence protected user workflows

This change also requires a standard `npm run test` command in the frontend package and CI execution of that command.

## Rationale

Jest fits the current frontend structure because the codebase already centers on reusable TypeScript modules, custom hooks, and interactive React components. The approved scope emphasizes logic-heavy surfaces first, where automated tests produce the highest regression-prevention value without forcing broad low-signal coverage.

Defining `npm run test` as the standard entry point avoids fragmented local workflows and gives CI one stable integration point.

## Test Boundaries

Required test categories for this change:

- unit tests for reusable frontend logic modules
- tests for custom hooks with browser-state or asynchronous behavior
- component tests for critical interactive components

Excluded from required scope for this change:

- end-to-end browser flows
- visual regression tooling
- blanket coverage requirements for simple UI primitives without meaningful project-specific behavior

## CI Notes

CI must execute frontend automated tests in addition to the existing frontend quality checks. This change does not require altering backend CI behavior beyond keeping current backend checks intact.

## Risks

- Browser-like test setup may require shared mocks for environment APIs such as storage, media queries, routing, or query providers.
- CI runtime may increase once frontend automated tests become required.
- Overly broad component testing could slow implementation if the approved scope is not kept focused on critical interactive behavior.

## Rollback

If the testing foundation causes unacceptable friction, rollback can remove the frontend test command and CI requirement together. Existing implementation changes should be reassessed against the approved quality bar before such a rollback is accepted.
