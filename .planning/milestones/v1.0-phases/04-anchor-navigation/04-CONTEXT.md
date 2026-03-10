# Phase 4: Anchor Navigation - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Two capabilities delivered in this phase:
1. **Navigation history** — when the artist jumps to an anchor (or Backdrop) via Alt+A, their previous DAG position is saved and can be restored with a back shortcut (Alt+Z).
2. **Backdrops in picker** — labelled BackdropNodes appear in the Alt+A navigation picker alongside anchor nodes and are navigable (DAG zooms to fit the Backdrop).

Scope is strictly these two features. Full browser-style forward/back history (NAV-03) is deferred.

</domain>

<decisions>
## Implementation Decisions

### Navigation history depth
- Single-step back only — one saved position slot, no history stack
- Each Alt+A jump (to anchor or Backdrop) overwrites the saved slot before navigating
- The slot is cleared/consumed when Alt+Z is used (no "forward" re-visit)
- Every Alt+A saves regardless of whether the user just came back (no ping-pong detection needed)
- NAV-03 (full browser-style history) deferred to a future phase

### Back shortcut
- Keyboard shortcut: **Alt+Z**
- Registered in the Anchors menu (same place as Alt+A Anchor Find)
- Silent no-op if no position has been saved yet (no error, no message)

### What "DAG position" means
- Save: `nuke.zoom()` (zoom level) + `nuke.center()` (x, y center point)
- Session-only — in-memory module-level variable in `anchor.py`; not persisted to disk
- On **Alt+Z restore**: set zoom + center back to saved values, then call `nukescripts.clear_selection_recursive()` (matches existing behaviour in `navigate_to_anchor()`)
- Selection state at the time of the original jump is NOT saved (viewport only)

### Backdrop inclusion in picker
- Only BackdropNodes with a non-empty `label` knob appear in the picker
- **Anchors appear bare** (no prefix): `MyAnchor`, `PlateA`
- **Backdrops appear prefixed**: `Backdrops/GradeStack`, `Backdrops/Comp`
- Navigating to a Backdrop = `nuke.zoomToFitSelected()` on the BackdropNode (zoom to fit entire backdrop)
- Backdrop navigation **also saves** the previous DAG position (identical to anchor navigation — any Alt+A jump saves position)

### Claude's Discretion
- How `nuke.center()` / `nuke.zoom()` are called to restore position (API details)
- Whether to introduce a `navigate_to_backdrop()` helper or extend `navigate_to_anchor()`
- Test strategy for the in-memory back-position slot

</decisions>

<specifics>
## Specific Ideas

- The picker layout should show anchors bare and backdrops prefixed — user explicitly confirmed this after seeing mockups. The visual distinction is intentional: "Only identify backdrops, anchors appear bare."
- Alt+Z is the back shortcut — positioned as a pair with Alt+A (navigate = A, back = Z)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `navigate_to_anchor(anchor_node)` in `anchor.py` — zooms DAG using `nuke.zoomToFitSelected()` after selecting upstream nodes; pattern for "navigate to something"
- `find_smallest_containing_backdrop(node)` in `link.py` — iterates `nuke.allNodes('BackdropNode')`, reusable pattern for finding/listing Backdrops
- `AnchorNavigatePlugin` in `anchor.py` — existing tabtabtab plugin class; Backdrop support goes here (add Backdrop items to `get_items()`)
- `_anchor_navigate_widget` global + `select_anchor_and_navigate()` — existing entry point for Alt+A; back shortcut needs a parallel entry point

### Established Patterns
- Module-level widget globals (`_anchor_picker_widget`, `_anchor_navigate_widget`) — in-memory back-position slot follows this same pattern
- `menupath: 'Anchors/' + name` in `AnchorNavigatePlugin.get_items()` — Backdrops will use `'Backdrops/' + label` to produce the prefix
- `nukescripts.clear_selection_recursive()` called after navigation in `navigate_to_anchor()` — same should happen on Alt+Z restore

### Integration Points
- `menu.py` line 33: `anchors_menu.addCommand("Anchor Find", ..., "alt+A")` — back shortcut registered the same way with `"alt+Z"`
- `anchor.py` imports `nuke`, `nukescripts` — `nuke.center()`, `nuke.zoom()`, `nuke.center(x, y)`, `nuke.zoom(level)` available here

</code_context>

<deferred>
## Deferred Ideas

- NAV-03: Full browser-style forward/back history stack — future phase (NAV-V2-01 in REQUIREMENTS.md)

</deferred>

---

*Phase: 04-anchor-navigation*
*Context gathered: 2026-03-08*
