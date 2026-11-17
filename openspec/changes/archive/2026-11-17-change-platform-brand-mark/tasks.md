# Tasks

## 1. Frontend: Brand Mark
- [x] 1.1 Add a reusable brand mark component (outlined tile, rising price line, ripples around the end point, green accent point) that scales from 16px to 96px.
- [x] 1.2 Add the same mark as the browser tab icon for the app.

## 2. Frontend: Placement
- [x] 2.1 Use the brand mark in the sidebar header in place of the pulse icon, including the collapsed sidebar state.
- [x] 2.2 Show the brand mark above the `MarketPulse` name on the sign in, sign up, reset password, and update password pages.
- [x] 2.3 Give the `Overview` navigation item a different icon than the brand mark.
- [x] 2.4 Give each sidebar navigation item its own icon color.

## 3. Validation
- [x] 3.1 Run `docker compose exec -T frontend npm run lint`.
- [x] 3.2 Run `docker compose exec -T frontend npm run typecheck`.
- [x] 3.3 Run `docker compose exec -T frontend npm run build` (stop the dev frontend first, then restart it).
- [x] 3.4 Manually verify the mark in the expanded and collapsed sidebar, the four authentication pages, the browser tab, and the colored navigation icons.
- [x] 3.5 Run `openspec validate change-platform-brand-mark --strict`.
