## 1. Frontend

- [x] 1.1 Render the sources block collapsed by default with the `Sources` heading, the unique source labels, the total source count, and an accessible expand control.
- [x] 1.2 On expand, show the existing full sources list including links, times, and stale markers; allow collapsing it again.
- [x] 1.3 Update `message-sources` tests for the collapsed and expanded states.

## 2. Validation

- [x] 2.1 Run `docker compose exec -T frontend npm run lint`, `npm run typecheck`, and `npm run test -- --runInBand`.
- [x] 2.2 Run `openspec validate change-assistant-sources-collapsible --strict`.
