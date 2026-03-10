---
phase: 04-anchor-navigation
plan: W0
subsystem: testing
tags: [unittest, tdd, nuke-stub, navigation, backdrop]

# Dependency graph
requires:
  - phase: 03-anchor-color-system
    provides: nuke stub pattern with StubNode/StubKnob and Qt/tabtabtab stubs
provides:
  - Full RED test suite for Phase 4 navigation features in tests/test_anchor_navigation.py
  - nuke stub extended with zoom/center/zoomToFitSelected viewport methods
  - 16 test methods covering NAV-01, NAV-02, FIND-01 requirements
affects: [04-01, 04-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "nuke stub extended per-plan: add domain-specific methods (zoom, center) to make_stub_nuke_module()"
    - "allNodes side_effect pattern for discriminating BackdropNode vs anchor queries in tests"
    - "_ensure_qt_stubs_support_mock_attributes() guard preserved across test suite discovery order"

key-files:
  created:
    - tests/test_anchor_navigation.py
  modified: []

key-decisions:
  - "nuke.zoom stub returns 1.0 float and nuke.center returns [0.0, 0.0] list — matches Nuke API signatures exactly"
  - "allNodes side_effect dispatches by class_name argument to simulate separate BackdropNode and anchor node lists"
  - "Tests are RED-first: AttributeError on _save_dag_position, navigate_back, navigate_to_backdrop is expected correct state"

patterns-established:
  - "Side-effect dispatch pattern: def _allNodes_side_effect(class_name=None): return backdrop_nodes if class_name == 'BackdropNode' else anchor_nodes"

requirements-completed: [NAV-01, NAV-02, NAV-03, FIND-01]

# Metrics
duration: 4min
completed: 2026-03-10
---

# Phase 4 Plan W0: Anchor Navigation Test Scaffold Summary

**16-test RED scaffold for DAG back-navigation (NAV-01/02) and backdrop picker (FIND-01) using nuke stub with zoom/center viewport methods**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-10T03:15:22Z
- **Completed:** 2026-03-10T03:19:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created `tests/test_anchor_navigation.py` with 16 test methods across 6 test classes
- Extended nuke stub with `zoom`, `center`, and `zoomToFitSelected` methods for DAG viewport testing
- Established `allNodes` side-effect dispatch pattern for distinguishing BackdropNode vs anchor queries
- All tests are appropriately RED (AttributeError/FAIL on missing functions) with no SyntaxError or ImportError

## Task Commits

1. **Task 1: Create tests/test_anchor_navigation.py** - `2c6ec4c` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `tests/test_anchor_navigation.py` - Full Phase 4 test suite: TestSaveDagPosition, TestNavigateBack, TestInvokeSavesPosition, TestGetItemsIncludesBackdrops, TestNavigateToBackdrop, TestPickerLaunchGuard

## Decisions Made
- nuke.zoom stub returns `1.0` float and nuke.center returns `[0.0, 0.0]` list to match Nuke API call signatures exactly
- `allNodes` side_effect pattern dispatches by `class_name` keyword arg to support both BackdropNode and anchor node queries from the same mock
- Tests are intentionally RED: functions `_save_dag_position`, `navigate_back`, `navigate_to_backdrop` are not yet in anchor.py; Plans 01 and 02 will make them GREEN

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Test scaffold complete — Plans 04-01 and 04-02 have a concrete test target to turn GREEN
- All 16 tests are RED with AttributeError/FAIL on missing implementations (not broken with SyntaxError/ImportError)
- Pre-existing test suite (58 tests excluding new file) unaffected

## Self-Check: PASSED
- `tests/test_anchor_navigation.py` — FOUND
- `04-W0-SUMMARY.md` — FOUND
- Commit `2c6ec4c` — FOUND

---
*Phase: 04-anchor-navigation*
*Completed: 2026-03-10*
