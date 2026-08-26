## 1. Frontend

- [ ] 1.1 Replace the stepper-based create/edit alert authoring shell with a fixed Y-shaped React Flow canvas that removes the dedicated preview node.
- [ ] 1.2 Build fixed node types and code-defined edges for coin selection, combined scenario/configuration, timing, and the central review/save node.
- [ ] 1.3 Ensure users cannot create, delete, reconnect, or otherwise customize flow edges.
- [ ] 1.3.1 Remove node dragging and keep node positions fixed in the canvas layout.
- [x] 1.4 Preserve watchlist-scoped coin selection through a compact combobox node that shows only saved watchlist coins.
- [x] 1.5 Move scenario selection into a combobox with icons and keep scenario-specific configuration inside that same node.
- [x] 1.6 Preserve chart-first configuration for `Price above` and `Price below` alerts inside the combined scenario/configuration node.
- [x] 1.7 Preserve the lighter `News` configuration path while keeping it inside the same combined scenario/configuration node.
- [x] 1.8 Keep timing behavior intact, but move recurring date selection into a modal-style calendar interaction opened from the chosen date fields.
- [ ] 1.9 Add clear validation and completion feedback while keeping the main authoring nodes persistently visible without active/inactive content swapping.
- [x] 1.10 Ensure the same React Flow canvas model works on mobile and desktop through responsive layout and viewport behavior.
- [x] 1.11 Keep review and save actions inside the guided flow and preserve current loading and request-error handling.
- [ ] 1.12 Use smooth curved edges that visually connect from the outer authoring nodes into the central node without emphasizing square connection points.

## 2. Tests And Validation

- [ ] 2.1 Run relevant frontend checks for the alert authoring changes.
- [ ] 2.2 Run `openspec validate change-alert-authoring-to-react-flow --strict`.
