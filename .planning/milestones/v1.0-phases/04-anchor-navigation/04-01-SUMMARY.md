---
phase: 04-anchor-navigation
plan: "01"
subsystem: navigation
tags: [nuke, dag-navigation, viewport, anchor, menu]

# Dependency graph
requires:
  - phase: 04-anchor-navigation
    provides: W0 RED test scaffold for NAV-01/02 (TestSaveDagPosition, TestNavigateBack, TestInvokeSavesPosition)
provides:
  - _back_position module-level slot (single-slot navigation history)
  - _save_dag_position() captures nuke.zoom()/nuke.center() into slot
  - navigate_back() restores viewport and consumes slot; no-op when empty
  - navigate_to_backdrop() stub (full implementation in Plan 02)
  - AnchorNavigatePlugin.invoke() saves position before every navigation jump
  - Alt+Z Anchor Back shortcut registered in menu.py
affects:
  - 04-02 (adds BackdropNode dispatch in invoke() and full navigate_to_backdrop body)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single-slot viewport save/restore: (zoom_level, center_xy) tuple stored in _back_position global"
    - "invoke() renamed anchor_node to node to accommodate both NoOp anchors and BackdropNodes"
    - "navigate_to_backdrop() stub added alongside navigate_to_anchor() for Plan 02 wiring"

key-files:
  created: []
  modified:
    - anchor.py
    - menu.py

key-decisions:
  - "invoke() variable renamed from anchor_node to node — consistent with upcoming BackdropNode dispatch in Plan 02"
  - "navigate_to_backdrop() stub added in Plan 01 alongside the dispatch in invoke() — tests required the attribute to be patchable before Plan 02 provides the full body"
  - "navigate_back() consumes slot before calling nuke.zoom() to prevent double-restore if nuke.zoom raises"

patterns-established:
  - "Back-navigation slot pattern: _save_dag_position() called before every nav jump; navigate_back() restores and clears"

requirements-completed: [NAV-01, NAV-02]

# Metrics
duration: 2min
completed: 2026-03-10
---

# Phase 4 Plan 01: Anchor Navigation Back-Position Summary

**Single-slot DAG viewport save/restore: _save_dag_position() + navigate_back() wired to Alt+Z, with invoke() saving position before every Alt+A jump**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-10T03:19:22Z
- **Completed:** 2026-03-10T03:21:42Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `_back_position` module-level slot added (None until first nav jump)
- `_save_dag_position()` stores `(nuke.zoom(), nuke.center())` tuple into slot, overwriting any previous value
- `navigate_back()` restores viewport via `nuke.zoom(zoom_level, center_xy)`, calls `nukescripts.clear_selection_recursive()`, consumes slot, and is a silent no-op when slot is empty
- `AnchorNavigatePlugin.invoke()` calls `_save_dag_position()` before every navigation (anchor or backdrop), ensuring Alt+A always saves prior position
- `navigate_to_backdrop()` stub added alongside invoke() dispatch so tests can patch it before Plan 02 implements the body
- Alt+Z `Anchor Back` shortcut registered in `menu.py` immediately after `Anchor Find`

## Task Commits

Each task was committed atomically:

1. **Task 1: Add _back_position slot, _save_dag_position(), and navigate_back()** - `d64f9a4` (feat)
2. **Task 2: Update invoke() to save position; register Alt+Z in menu.py** - `0dca61e` (feat)

## Files Created/Modified
- `/workspace/anchor.py` - Added _back_position, _save_dag_position(), navigate_back(), navigate_to_backdrop() stub; updated invoke()
- `/workspace/menu.py` - Added Anchor Back / alt+Z command registration

## Decisions Made
- `invoke()` variable renamed from `anchor_node` to `node` to accommodate both anchor NoOp nodes and BackdropNodes after Plan 02's dispatch
- `navigate_to_backdrop()` stub added in Plan 01 because `TestInvokeSavesPosition.test_invoke_saves_position_before_navigating_backdrop` patches `anchor.navigate_to_backdrop` — the attribute must exist for `patch.object` to work; Plan 02 replaces the stub body with the full implementation
- `navigate_back()` sets `_back_position = None` before calling `nuke.zoom()` to avoid double-restore if the restore call raises

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added navigate_to_backdrop() stub alongside invoke() dispatch**
- **Found during:** Task 2 (update AnchorNavigatePlugin.invoke())
- **Issue:** Plan specified a TODO comment for BackdropNode dispatch in invoke(), but TestInvokeSavesPosition patches `anchor.navigate_to_backdrop` — `patch.object` raises AttributeError if the attribute does not exist at all. Without the stub, the test cannot even set up the patch.
- **Fix:** Added a functional `navigate_to_backdrop()` stub (select node + zoomToFitSelected + clear selection) so invoke() can dispatch and the test can patch successfully. Plan 02 will replace the stub body.
- **Files modified:** anchor.py
- **Verification:** TestInvokeSavesPosition.test_invoke_saves_position_before_navigating_backdrop passes; TestNavigateToBackdrop also turns green
- **Committed in:** 0dca61e (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Stub required for test infrastructure correctness. Scope stays within Plan 01 — Plan 02 provides the real body.

## Issues Encountered
- None — TDD RED/GREEN cycle executed cleanly.

## Next Phase Readiness
- NAV-01 and NAV-02 fully implemented and tested
- Plan 02 can wire `navigate_to_backdrop()` body and update `get_items()` for FIND-01 (backdrop picker)
- `TestNavigateToBackdrop` and the two FIND-01 picker tests remain RED pending Plan 02

---
*Phase: 04-anchor-navigation*
*Completed: 2026-03-10*
