## Summary

Upgrade the standalone Ruby `market-data-api` service directly to the latest supported Rails and Ruby runtime used for this project, while preserving the existing public market-overview, asset-search, coin-news, and snapshot-refresh behavior exposed through the FastAPI backend.

## Problem

The `market-data-api` service currently runs on an older Rails generation and a runtime setup that is already producing local dependency and native-extension failures during development and test setup.

This creates several risks:

- current dependency installation is fragile and blocks normal development workflows
- the Ruby service runtime drifts further away from the current Rails guides, ecosystem defaults, and supported upgrade path
- future dependency work, including Snowflake analytics export, becomes harder to implement and verify on top of an outdated runtime base
- runtime and dependency issues in the Ruby service may eventually threaten the stability of existing market-data and news provider integrations

Without a runtime upgrade, the Ruby integration boundary remains increasingly expensive to maintain and harder to evolve safely.

## Proposed Solution

Upgrade the `market-data-api` service directly to the latest Rails and Ruby runtime versions adopted by this change, while explicitly preserving the current observable product behavior:

- update the Ruby service runtime, framework, and dependency set to the latest approved target versions for this change
- align service configuration, boot files, dependency declarations, and tests with the upgraded Rails application conventions
- keep the existing `market-overview`, `assets/search`, and `news` contracts stable from the perspective of the FastAPI backend and frontend consumers
- preserve background snapshot refresh behavior and observability during the runtime transition
- validate the upgraded runtime through focused Ruby tests and service-level verification

## Scope

- `market-data-api` runtime and framework upgrade
- Ruby and Rails dependency updates required for the upgrade
- configuration and bootstrapping changes required by the new Rails runtime
- test and task updates needed to keep the Ruby service verifiable after the upgrade
- preservation of existing market-data, news, and snapshot-refresh behavior

## Non-Goals

- changing the FastAPI backend runtime or Python dependency stack
- redesigning user-facing product behavior for market overview or coin news
- introducing new product endpoints solely because of the runtime upgrade
- implementing Snowflake analytics export as part of this change
- redesigning deployment architecture beyond what the runtime upgrade requires
- refactoring unrelated product logic just to modernize style

## Impact

- Affected domains: `market-data`, `news`, `background-jobs`
- The Ruby `market-data-api` service will undergo a high-risk framework and runtime transition
- Existing provider clients, snapshot refresh flows, Rake tasks, and tests may require targeted compatibility updates
- Verification effort is higher than a normal feature change because both dependency resolution and runtime behavior must remain stable
