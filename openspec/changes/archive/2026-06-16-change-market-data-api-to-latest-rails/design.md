## Overview

This change upgrades the standalone Ruby `market-data-api` service directly to the latest runtime targets adopted for this repository change, rather than stepping through multiple intermediate Rails upgrades first. The business goal is not to change product behavior. The goal is to restore a maintainable, installable, testable Ruby integration boundary that can keep serving market overview and coin-news functionality reliably.

## Goals

- Move the Ruby `market-data-api` service onto the latest approved Ruby and Rails runtime targets for this change.
- Keep the existing public market overview, asset search, and protected coin-news contracts stable.
- Keep reusable snapshot refresh and related background execution behavior stable and observable.
- Restore a dependency set that can be installed and tested consistently.

## Non-Goals

- Changing the Python backend runtime.
- Redesigning product behavior for market overview, coin news, or watchlist flows.
- Combining this runtime upgrade with Snowflake analytics implementation.
- Introducing new product features solely because a newer Rails version enables them.

## Architecture Impact

The service remains a dedicated Ruby boundary that:

- serves `market-overview`
- serves `assets/search`
- serves `news`
- refreshes reusable market-overview snapshots outside request paths

The upgrade changes runtime and framework internals, but not the architectural placement of the service in the wider MarketPulse system.

## Direct Upgrade Strategy

The user explicitly requested a direct jump to the latest runtime rather than a slower incremental path. This is higher risk than the official Rails guidance, which recommends moving slowly across minor versions and fixing deprecations along the way.

Because this change intentionally chooses the faster, higher-risk path, implementation must compensate with:

- tighter regression testing around existing observable service behavior
- careful review of boot/configuration differences introduced by the new Rails version
- explicit dependency and native-extension troubleshooting
- readiness to make small compatibility fixes across controllers, services, tasks, and tests

## Dependency And Runtime Concerns

The current development flow is already showing dependency-installation trouble. That means the upgrade must explicitly account for:

- Bundler version alignment
- Ruby version compatibility with the selected Rails version
- native extension builds such as Nokogiri and PostgreSQL adapters
- platform-specific differences for local macOS development and CI

The implementation may need to refresh lockfiles, dependency declarations, and setup instructions together so the service becomes reproducibly installable again.

## Behavioral Invariants

The following observable behaviors must remain stable:

- FastAPI can continue to retrieve market-overview responses through the Ruby service
- FastAPI can continue to retrieve coin-news responses through the Ruby service
- asset-search behavior stays available through the Ruby service
- reusable snapshot refresh still happens outside user-facing request-response flows
- provider failures remain mapped into safe backend-defined error behavior

## Testing And Verification

Verification should focus on existing observable behavior rather than raw framework internals:

- controller tests for `market-overview`, `assets/search`, and `news`
- service tests for snapshot building, caching, refresh, and failure fallback behavior
- dependency installation and boot verification under the upgraded runtime

## Risks

- a direct jump to the latest Rails version may surface multiple breaking changes at once
- dependency upgrades may require transitive gem changes not obvious at the start
- native extensions may fail on local or CI platforms until the dependency set is stabilized
- service configuration defaults may change in ways that subtly affect caching, logging, or API behavior

## Rollback

If the direct upgrade proves unstable, rollback should restore the previous `market-data-api` runtime and dependency set while preserving current product behavior. The rollback path should avoid mixing partial framework-upgrade artifacts into the previously working service baseline.
