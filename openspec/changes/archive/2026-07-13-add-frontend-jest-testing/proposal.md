## Summary

Add a frontend Jest testing foundation for the Next.js application, including a standard local test command, CI execution, and an initial testing scope focused on `lib`, `hooks`, and critical interactive components.

## Problem

The frontend currently has linting and type checking, but it does not have an approved automated unit and component testing foundation. This creates several risks:

- important frontend business logic can regress without fast feedback
- custom hooks and browser-dependent helpers can break without isolated verification
- critical interactive components can change behavior without automated protection
- CI cannot enforce frontend test execution as part of the quality bar

Without an approved change, adding Jest configuration, commands, and CI behavior would modify project quality expectations without a defined scope.

## Proposed Solution

Introduce Jest as the required frontend automated test runner for the Next.js application and define the first approved test coverage boundary.

This change will:

- add a standard frontend test command for local execution
- establish Jest-based automated testing for frontend unit and component tests
- define the initial approved coverage scope as `lib`, `hooks`, and critical interactive components
- require CI to execute frontend automated tests alongside existing frontend quality checks
- keep the change focused on test infrastructure and initial coverage enablement rather than broad product behavior changes

## Scope

Affected domains:

- `api-client-generation`

Primary workflows:

- a developer runs frontend automated tests locally through a standard package command
- CI runs frontend automated tests as part of the repository quality gates
- frontend contributors add and maintain Jest tests for `lib`, `hooks`, and critical interactive components

In scope:

- approving Jest as the frontend test runner
- defining the local frontend test command
- defining CI execution of frontend tests
- defining the approved initial frontend test coverage scope
- defining expected test categories for unit and component testing in the frontend codebase

## Non-Goals

- introducing end-to-end browser testing
- requiring snapshot-heavy testing practices
- requiring automated tests for every presentational UI primitive
- changing backend testing strategy
- changing API contracts or Orval generation behavior

## Impact

This change raises the frontend quality baseline by adding an approved automated test foundation that matches the current Next.js application structure. It gives implementation a clear boundary for where tests should start, how they should run locally, and how they should be enforced in CI without expanding into unrelated frontend architecture or product scope.
