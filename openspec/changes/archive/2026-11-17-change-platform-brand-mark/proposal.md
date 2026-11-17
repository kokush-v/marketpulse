# Change: Introduce A Custom MarketPulse Brand Mark

## Summary

Replace the generic pulse icon used as the platform's logo with a custom MarketPulse mark: a rising price line whose end point sends out expanding ripples (the "price pulse"). Use one reusable mark in the dashboard sidebar, on the authentication pages, and as the browser tab icon.

## Problem

The platform's only visual identity is the stock `Activity` pulse icon from the icon library. It is generic, it is also used as the `Overview` navigation icon (so the brand and a menu item look the same), and the browser tab shows the default icon because the app has no favicon.

## Proposed Solution

- Add a single custom brand mark (outlined tile, rising price line, ripples around the end point, green accent point) that renders crisply from 16px to 96px.
- Show the mark in the sidebar header in place of the pulse icon, including the collapsed sidebar state.
- Show the mark above the `MarketPulse` name on the authentication pages (sign in, sign up, reset password, update password).
- Provide the same mark as the browser tab icon.
- Give the `Overview` navigation item its own icon so it no longer duplicates the brand.
- Give each sidebar navigation item (`Overview`, `Watchlist`, `Alerts`, `Assistant`) its own icon color so the items are easy to tell apart on the dark interface.

## Scope

- Domain: `market-data` (public dashboard shell), plus the authentication page headers.
- Frontend only.

## Assumptions

- No dedicated branding domain exists in `openspec/specs/`, so the requirement is added to `market-data`, which owns the dashboard shell.
- The selected mark is the "price + ripples" variant approved by the user; the colors follow the existing blue accent of the app.
- The `Overview` item uses a different existing library icon; the exact icon is chosen during implementation.

## Non-Goals

- Changing the navigation items, their order, or the active/hover states, beyond the icon colors.
- A wordmark or typography redesign; the `MarketPulse` text stays as is.
- Changes to the color theme, page layouts, or navigation structure.
- Social/share images, app manifests, or additional icon sizes beyond the browser tab icon.
- Backend, database, or API changes.

## Impact

- Affected spec: `openspec/specs/market-data/spec.md` (adds the brand mark requirement).
- Affected code: the shared brand mark component, `features/market-dashboard/components/app-sidebar.tsx`, the four `app/(auth)/*` pages, and the app icon in `frontend/app/`.
- No migrations and no OpenAPI changes.
