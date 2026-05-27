## Summary
Improve the production-readiness of the Ruby `market-data-api` service so public market overview requests use a modern Rails production concurrency model instead of rebuilding provider-heavy payloads inside the request path.

## Problem
The current Ruby market-data service builds the public market overview payload during request handling, performs sequential upstream HTTP fan-out, and uses process-local memory caching. That design is acceptable for an early prototype, but it does not match a typical modern production Rails deployment where request concurrency is handled through Puma workers and threads, shared caches are used across instances, and expensive upstream refresh work is moved out of the hot request path.

Without a clearer architecture, the service risks:
- slow response times under concurrent public traffic
- duplicated upstream provider work across Puma workers or service instances
- avoidable rate-limit pressure on external providers
- fragile behavior when upstream refresh fails while requests are in flight

## Proposed Solution
Update the `market-data` and `background-jobs` capabilities so the Ruby market-data service standardizes a production-oriented concurrency model:
- production request concurrency is handled through explicit Puma worker and thread configuration
- public market overview requests prefer returning a reusable cached snapshot rather than rebuilding the full provider payload on every request
- snapshot refresh runs outside the normal request-response path in production deployments
- the service keeps the last successful snapshot available during refresh failures or transient provider issues
- any remaining request-path upstream work uses bounded concurrency, explicit timeouts, and safe degradation behavior
- frontend-facing API behavior remains routed through the FastAPI backend without requiring direct frontend changes

## Scope
In scope:
- Production concurrency expectations for the Ruby `market-data-api` service
- Shared cache expectations for public market overview snapshots in production
- Background refresh behavior for public market overview data
- Failure-handling rules for stale snapshot fallback during provider outages
- Bounded and observable upstream integration behavior for CoinGecko-backed refresh work
- Preservation of the existing FastAPI-owned frontend contract unless a follow-up explicitly changes it

## Non-Goals
- Rewriting the Ruby service around a fully fiber-driven async execution model
- Replacing Puma with a different Ruby web server
- Changing the public dashboard UX or adding new frontend features
- Adding PostgreSQL persistence for market overview payloads
- Expanding this change into watchlists, alerts, or broader infrastructure redesign
- Replacing FastAPI as the frontend-facing API boundary

## Impact
Affected domains:
- `market-data`
- `background-jobs`

Primary user workflows:
- Visitor opens the public market dashboard and receives market overview data with stable latency
- Visitor continues receiving market overview data during transient upstream provider failures through safe stale fallback behavior

System impact:
- Formalizes a production deployment model for the Ruby market-data microservice
- Adds background refresh expectations for public market overview snapshots
- Requires a shared production cache strategy instead of process-local request optimization only
- Introduces operational expectations for timeouts, bounded fan-out, and observability around provider-backed refresh work

Assumptions:
- Production deployments can run a background execution path for recurring snapshot refreshes
- Production deployments can provide a cache backend shared across Puma workers and service instances
