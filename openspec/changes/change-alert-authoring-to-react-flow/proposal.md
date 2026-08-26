## Summary

Replace the current stepper-based alert create/edit experience with a React Flow canvas organized as a fixed Y-shaped authoring graph. The new flow keeps the existing alert scenarios, timing behavior, chart-first price configuration, and watchlist-scoped coin selection, but expresses them through compact code-defined nodes and edges instead of a stepper UI.

## Problem

The approved alert-authoring flow is currently specified around a visible stepper. That works functionally, but it does not match the more visual, node-based builder direction now chosen for MarketPulse alerts.

Without an approved spec change, implementation would risk:

- replacing the stepper with an unapproved frontend interaction model
- drifting into a generic node editor with custom connections that changes product scope
- introducing frontend behavior differences between price and news flows that are not clearly defined
- creating mobile and desktop inconsistencies for the canvas experience

## Proposed Solution

Modify the `alerts` capability so create and edit alert flows use a React Flow canvas built from a fixed Y-shaped graph instead of a stepper.

This change defines:

- three compact authoring nodes for coin, scenario, and timing feeding one central review/save node
- no dedicated preview node
- scenario selection and scenario-specific configuration combined into one node
- no node dragging
- code-defined edges only
- no user-created, removed, or reconnected edges
- a simultaneous editing model where the compact nodes remain visible together instead of swapping between active and inactive content states
- scenario-dependent branching inside the fixed flow for `Price above`, `Price below`, and `News`
- reuse of the existing alert semantics, validation rules, and backend/API contracts
- the same React Flow canvas model on mobile and desktop, adapted responsively without falling back to a separate stepper or stacked-only authoring mode
- a compact coin-selection node that uses watchlist-only search and dropdown selection
- a compact scenario node that uses a combobox with icons and also contains scenario-specific configuration controls
- a timing node that keeps the current timing behavior model but opens recurring date selection in a modal-style calendar interaction
- smooth curved edges that visually connect from the three authoring nodes into the central review/save node rather than emphasizing square connection points
- persistent node glow or outline styling without relying on an active/inactive content mode
- validation feedback and a final save state so users remain oriented without a dedicated stepper

## Scope

Affected domains:

- `alerts`

Primary user workflows:

- authenticated user creates a new alert through a fixed Y-shaped visual canvas
- authenticated user edits an existing alert through the same fixed Y-shaped visual canvas
- authenticated user selects a watchlist coin through a combobox that only shows saved watchlist coins
- authenticated user chooses one of the three supported scenarios from a combobox with icons and configures scenario-specific alert settings in that same node
- authenticated user configures timing and price or news behavior directly within the node-based flow while all major nodes remain visible
- authenticated user reviews a compact visual summary and saves the alert from the central review node

In scope:

- replacing the stepper requirement in alert authoring with a fixed Y-shaped React Flow canvas
- fixed node layout and fixed edge connections
- responsive behavior for the same canvas model on desktop and mobile
- visual branching for `Price above`, `Price below`, and `News`
- removing the dedicated preview node from the authoring graph
- combining scenario selection and scenario-specific configuration into one node
- using a central review/save node as the convergence point for the three authoring branches
- compact node summaries, validation states, and persistent glow styling without active/inactive content swapping
- preserving the existing chart-first configuration for price alerts within the flow
- preserving watchlist-scoped coin selection through a compact watchlist-only picker
- preserving existing timing behavior and review/save behavior while moving recurring date selection into a modal-style calendar interaction
- smoothing edge visuals so connections read as flowing into the central node rather than routing between visible square connection points

Out of scope:

- backend API changes
- alert rule semantic changes
- new alert scenarios
- adding coins to the watchlist from inside the alert-authoring canvas
- reintroducing a dedicated preview node
- reintroducing draggable nodes
- user-created custom connections
- drag-to-rewire behavior
- backend persistence of user-arranged node positions
- turning alerts into a generic automation builder
- replacing the alert list workspace cards

## Non-Goals

- adding multi-condition alert logic
- adding backend persistence for graph structures
- introducing a separate mobile-specific authoring paradigm
- changing how alerts are evaluated, stored, or delivered
- adding arbitrary node libraries, templates, or saved flow presets

## Impact

This change updates the approved frontend interaction model for alert authoring while keeping the existing alert contract intact. It gives implementation a clear product boundary for using React Flow as a guided, central-preview builder, avoids accidental scope expansion into a generic workflow editor, and preserves consistency between desktop and mobile authoring.
