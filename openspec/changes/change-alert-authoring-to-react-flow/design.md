## Overview

This change is frontend-only, but it introduces an important interaction-model decision: React Flow SHALL be used as a fixed Y-shaped canvas organized around three authoring nodes feeding one central review/save node, not as an open-ended workflow editor.

The existing alert semantics remain unchanged. The canvas is only a presentation and interaction layer over the current authoring state.

## Interaction Model

The flow SHALL:

- render a fixed set of alert-authoring nodes
- omit a dedicated preview node
- place coin, scenario, and timing nodes around a central review/save node in a Y-shaped arrangement
- use code-defined edges only
- prevent user-created connections and reconnections
- not allow nodes to be dragged
- keep the main authoring nodes visible together rather than swapping between active and inactive content states
- use smooth curved edge styling that reads as node-to-node flow rather than square handle-to-handle routing

The flow SHALL NOT:

- persist arbitrary graph geometry as alert data
- allow user-authored graph topology
- introduce new alert-rule semantics

## Node Model

The authoring canvas should be modeled around stable stages that already exist in the approved alert flow:

- coin selection
- scenario selection and scenario-specific configuration
- timing
- review and save

The coin node should stay compact and rely on a watchlist-only combobox. The scenario node should combine scenario selection and scenario-specific configuration so users do not need to move into a separate configuration node after choosing a scenario. The timing node should preserve the current time-behavior model, but recurring date selection should open through a modal-style calendar interaction instead of rendering a full calendar inline inside the node. The central node should act as the convergence point for review and save rather than as an always-expanded preview.

## Responsive Behavior

Desktop and mobile SHALL use the same React Flow canvas concept. Responsive adaptation may change zoom defaults, viewport fit behavior, node sizing, and spacing, but it SHALL NOT replace the canvas with a separate stepper or stacked-only authoring mode.
The layout should remain fixed on both desktop and mobile-capable canvases so the Y-shaped structure stays recognizable.

## Validation And Orientation

Because the stepper is removed, orientation must come from the canvas itself. The implementation should use node state to communicate:

- validity and completeness
- validation errors blocking save

The canvas should stay compact, with brief summaries inside nodes and the main editing controls embedded directly in the persistent visible nodes. Node styling may keep glow or outline accents, but orientation should not depend on one node switching into an "active" content mode while others collapse. Edge styling should visually approach the center of each node so connections feel soft and intentional rather than anchored to obvious square connection points.
