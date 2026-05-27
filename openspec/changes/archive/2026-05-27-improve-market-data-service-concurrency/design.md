## Overview
This change defines a production-oriented concurrency model for the Ruby `market-data-api` service. The intent is not to make the service uniformly "async" in the JavaScript or Python sense. Instead, it formalizes the more typical modern Rails production approach for a provider-backed read API:
- Puma handles request concurrency through workers and threads
- expensive upstream aggregation work is moved out of the hot request path when possible
- shared cache snapshots are reused across workers and instances
- stale-but-safe data is preferred over request-path upstream fan-out during transient failures

## Architectural Decisions

### 1. Request concurrency model
- Production request concurrency SHALL be based on Puma worker and thread settings rather than on a full fiber-driven rewrite.
- The service SHOULD keep request handlers short and predictable by serving prebuilt or reusable market overview snapshots.
- Any request-path work that still reaches upstream providers SHALL use explicit timeouts and bounded concurrency.

### 2. Snapshot-first market overview delivery
- The public market overview payload SHALL be treated as a reusable snapshot artifact.
- In production, normal public requests SHOULD read the latest reusable snapshot from shared cache rather than assembling the entire payload from upstream providers during request handling.
- If no successful snapshot exists yet, the implementation MAY perform a bounded cold-start build, but this behavior must be documented and kept exceptional.

### 3. Background refresh responsibility
- Refreshing the market overview snapshot SHALL run outside the normal request-response cycle in production deployments.
- The refresh path MAY be implemented through Rails-native jobs, an external scheduler that triggers Rails job execution, or another operationally equivalent background execution path.
- Refresh cadence should balance freshness, provider quotas, and operational cost without requiring every incoming request to trigger a full rebuild.

### 4. Shared cache expectations
- Production deployments SHALL use a cache backend shared across Puma workers and service instances for market overview snapshots.
- Process-local in-memory caching MAY remain acceptable for development or test environments, but it is not sufficient as the production cache strategy for this capability.
- Cache entries should carry enough metadata to distinguish freshness, last successful generation time, and refresh failures when needed for observability.

### 5. Failure handling and stale fallback
- If a scheduled or background refresh fails because of provider errors, malformed payloads, timeouts, or rate limits, the last successful snapshot SHOULD remain available until it is explicitly replaced or expires under a documented policy.
- The service SHOULD prefer returning a recent successful snapshot over surfacing an avoidable outage caused by refresh-path failure.
- If no successful snapshot exists and the service cannot build one within bounded limits, the service SHALL continue returning safe upstream failure responses.

### 6. Upstream provider concurrency and limits
- This change does not require a blanket migration to fiber-scheduled HTTP clients.
- The implementation MAY use controlled parallelism for independent upstream calls if it improves refresh latency without creating unbounded provider pressure.
- Any parallel upstream refresh behavior must define:
  - maximum in-flight provider requests
  - explicit connection and read timeouts
  - retry rules, if any
  - safe handling for partial upstream failures
- The implementation SHOULD avoid multiplying provider requests linearly with public traffic volume.

### 7. FastAPI integration boundary
- FastAPI remains the frontend-facing API boundary for the dashboard.
- This change SHOULD preserve the existing Ruby-to-FastAPI payload contract unless implementation work discovers an unavoidable contract issue.
- Any contract change that affects backend OpenAPI or Orval-generated frontend clients requires a separate approved follow-up or an explicit expansion of this change.

## Security and Operational Considerations
- Provider credentials remain server-side in the Ruby service.
- Shared cache infrastructure must not expose provider credentials or internal refresh details to the frontend.
- Background refresh execution must avoid overlapping refresh storms where multiple workers or instances rebuild the same snapshot unnecessarily.
- Logging and metrics should help operators distinguish between:
  - request latency issues
  - cache effectiveness issues
  - upstream provider failures
  - scheduler or background execution failures

## Testing Notes
- Tests should verify that successful snapshots are reused across normal requests.
- Tests should verify that failed refresh attempts do not discard the last successful snapshot.
- Tests should verify documented cold-start behavior when no snapshot exists.
- Tests should verify bounded timeout or concurrency behavior where practical without introducing brittle timing-dependent suites.

## Risks and Rollback Considerations
- Risk: adding background refresh and shared cache increases operational complexity compared with a single-process prototype.
- Mitigation: keep the change focused on one read-only capability and document the deployment expectations clearly.
- Risk: bounded parallel upstream refresh could still create provider pressure if limits are too high.
- Mitigation: require explicit concurrency ceilings and observe real provider error rates before increasing them.
- Rollback: the service can temporarily fall back to synchronous snapshot assembly for cold-start or emergency operation, but production should treat that as degraded mode rather than the steady-state model.
