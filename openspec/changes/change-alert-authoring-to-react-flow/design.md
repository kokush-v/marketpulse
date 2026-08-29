## Overview

This change is frontend-only. React Flow SHALL be used as a fixed Y-shaped visual canvas organized around three authoring nodes feeding one central review/save node, not as an open-ended workflow editor or a staged wizard.

The existing alert semantics remain unchanged. The canvas is only a presentation and interaction layer over the current authoring state.

## Interaction Model

The flow SHALL:

- render a fixed set of alert-authoring nodes
- omit a dedicated preview node
- place coin, scenario, and timing nodes around a central review/save node in a Y-shaped arrangement
- use code-defined edges only
- prevent user-created connections and reconnections
- not allow nodes to be dragged
- keep all authoring nodes visible and editable together from the initial render
- not use active, selected-stage, progressively unlocked, or completion-driven node presentation
- give every node the same defined outer width and height
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

The coin node should rely on a watchlist-only combobox. The scenario node should combine scenario selection and scenario-specific configuration so users do not need to move into a separate configuration node after choosing a scenario. The timing node should preserve the current time-behavior model, but recurring date selection should open through a modal-style calendar interaction instead of rendering a full calendar inline inside the node. The central node should provide review and save rather than act as an always-expanded preview. All nodes use identical outer dimensions; controls and content must fit within that shared visual frame.

## Responsive Behavior

Desktop and mobile SHALL use the same React Flow canvas concept. Responsive adaptation may change zoom defaults, viewport fit behavior, and spacing, but it SHALL NOT make one node a different size from another or replace the canvas with a separate stepper or stacked-only authoring mode.
The layout should remain fixed on both desktop and mobile-capable canvases so the Y-shaped structure stays recognizable.

## Validation And Orientation

Because the stepper is removed, orientation must come from the complete form visible on the canvas. The implementation should use validation state to communicate:

- validity and completeness
- validation errors and incomplete required fields blocking save

The canvas should keep the main editing controls embedded directly in the persistently visible nodes. Nodes use neutral styling and must not imply an active stage through glow, highlighting, or state-driven expansion. The save action is disabled until every required field has a valid value; it becomes available immediately once the complete alert definition is valid. Edge styling should visually approach the center of each node so connections feel soft and intentional rather than anchored to obvious square connection points.
