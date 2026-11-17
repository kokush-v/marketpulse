# Design: Backend Alert Filtering

## API Contract

`GET /alerts` gains optional query parameters:

- `status`: `active` or `paused`. Omitted means all statuses.
- `scenario`: `price_above`, `price_below`, or `coin_news`. Omitted means all scenarios.
- `q`: free text matched case-insensitively against the coin name or symbol. Blank or omitted means no coin filter.

Response `AlertListResponse` keeps `items` and adds `counts`:

```text
counts: { all: int, active: int, paused: int }
```

`counts` is computed over the authenticated user's alerts that match `q` and `scenario` but NOT `status`, so each status option shows how many alerts selecting it would display. `items` is filtered by all provided parameters.

Invalid `status` or `scenario` values are rejected by request validation (422). The parameters are optional, so existing callers are unaffected.

## Ownership And Security

Every query keeps the `user_id == current_user.id` condition; filters are applied in addition to it and never replace it. Parameters are never used to select another user's data.

## Implementation Notes

- Filtering is applied in the repository query (`status` column, `symbol`/`name`, and `scenario_payload["scenario"]` as already used by evaluation queries).
- `q` is treated as literal text: SQL wildcard characters (`%`, `_`) are escaped so they match literally.
- `counts` is computed with one grouped query over the user's alerts filtered by `q` and `scenario`.
- Routes stay thin; filter parsing uses typed query parameters and enums, and business logic stays in the service.

## Frontend

The frontend sends filter state as query parameters through the Orval-generated hook, debounces coin search input, and keeps the previous list visible while a filtered request is loading. The alert edit flow keeps calling the endpoint without filters.

## Risks And Rollback

- Additive contract change; reverting removes the parameters and `counts` while the old frontend continues to work.
- Search runs per keystroke after debounce; the result set is small per user, so no index is added.
