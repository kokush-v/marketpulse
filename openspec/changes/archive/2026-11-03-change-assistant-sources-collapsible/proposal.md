## Summary

Make the sources block under assistant messages compact: it is collapsed by default and shows only the source names and their count, and the user expands it to see the full list.

## Problem

The sources block always shows the full list with publisher, article title, time, and link for every source. With several news sources it takes a lot of space under every answer and draws attention away from the answer itself.

## Proposed Solution

- Show the sources block collapsed by default, for any number of sources.
- In the collapsed state, show the `Sources` heading, the unique source labels (publishers or `MarketPulse knowledge`), and the total number of sources, with a control to expand the list.
- When expanded, show the current full list unchanged: publisher, title, time, link for news, and the stale marker; the user can collapse it again.
- Show the stale marker only in the expanded list.

## Scope

Affected domain: `ai-assistant` (frontend only). Primary workflow: reading an assistant answer with sources in the widget or on the assistant page.

- collapsed and expanded states of the sources block;
- the expand and collapse control.

## Non-Goals

- changing which sources are attached to a message or how they are persisted;
- backend, API, or Orval client changes;
- remembering the expanded state after a reload;
- changing the stale data warning in the assistant answer text.

## Impact

- Frontend: `features/ai-assistant/components/message-sources.tsx` and its tests.
- Backend, database, API, and Orval client: no changes.
