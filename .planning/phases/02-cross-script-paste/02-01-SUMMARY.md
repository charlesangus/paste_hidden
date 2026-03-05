---
phase: 02-cross-script-paste
plan: 01
subsystem: paste
tags: [nuke, copy-paste, cross-script, anchor, link, constants, tdd]

# Dependency graph
requires:
  - phase: 01-copy-paste-semantics
    provides: paste_hidden() Path A/C structure, find_anchor_node() cross-script detection, link.py setup_link_node(), anchor.py find_anchor_by_name()
provides:
  - _extract_display_name_from_fqnn() helper in paste_hidden.py for FQNN last-segment extraction
  - Cross-script name-based reconnect for NoOp anchors in paste_hidden() Path A/C (XSCRIPT-01)
  - XSCRIPT-02/PASTE-04 comment in Path B confirming silent Dot disconnection
  - LINK_SOURCE_CLASSES frozenset in constants.py replacing LINK_CLASSES dict
  - 11 unit tests in tests/test_cross_script_paste.py with offline stub pattern including Qt/tabtabtab stubs
affects: [future paste phases, anchor navigation, any phase consuming constants.LINK_SOURCE_CLASSES]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "FQNN last-segment extraction: stored_fqnn.split('.')[-1] to handle group-nested nodes"
    - "Cross-script gate: find_anchor_node() returns None → attempt name-based lookup for NoOp anchors, skip for Dots and file nodes"
    - "Qt/tabtabtab stub pattern for offline tests that import anchor.py transitively"

key-files:
  created:
    - tests/test_cross_script_paste.py
    - .planning/phases/02-cross-script-paste/02-01-SUMMARY.md
  modified:
    - paste_hidden.py
    - constants.py
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Dot anchors excluded from cross-script name lookup via node.Class() != 'Dot' guard — Dot identity is positional, not name-stable across scripts"
  - "LINK_SOURCE_CLASSES frozenset replaces LINK_CLASSES dict since the link class values (PostageStamp/NoOp) are determined at anchor creation time, not at paste time"
  - "find_anchor_by_name() imported at top-level in paste_hidden.py; offline tests stub Qt and tabtabtab modules to avoid PySide2/PySide6 dependency at import time"
  - "Empty display name after ANCHOR_PREFIX strip is treated as no-match — avoids lookup for malformed FQNNs like 'shotA.Anchor_'"

patterns-established:
  - "Offline stub pattern: stub PySide6, PySide2, tabtabtab before any local imports when test chain reaches anchor.py"
  - "Cross-script reconnect: extract display name from FQNN → find_anchor_by_name() → replace placeholder with new link node"

requirements-completed: [XSCRIPT-01, XSCRIPT-02]

# Metrics
duration: 3min
completed: 2026-03-05
---

# Phase 2 Plan 1: Cross-Script Paste Summary

**Cross-script NoOp anchor reconnect via name lookup (_extract_display_name_from_fqnn + find_anchor_by_name) with LINK_CLASSES dead code replaced by LINK_SOURCE_CLASSES frozenset**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-05T03:49:30Z
- **Completed:** 2026-03-05T03:52:53Z
- **Tasks:** 2 (RED + GREEN)
- **Files modified:** 4

## Accomplishments
- Implemented `_extract_display_name_from_fqnn()` helper that extracts anchor display name from FQNN last segment, handling group-nested nodes and guarding empty/non-anchor FQNNs
- Extended `paste_hidden()` Path A/C to attempt name-based anchor reconnect for NoOp anchors pasted cross-script, with Dot anchor exclusion guard (XSCRIPT-01)
- Replaced `LINK_CLASSES` dict with `LINK_SOURCE_CLASSES` frozenset in constants.py; removed `ANCHOR_LINK_CLASS_KNOB_NAME`; all usages updated in paste_hidden.py
- Confirmed XSCRIPT-02/PASTE-04 via inline comment in Path B — Dot cross-script disconnection already handled by existing `if not input_node: continue`
- 11 offline unit tests passing with Qt/tabtabtab stub pattern

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Write failing tests** - `c531e82` (test)
2. **Task 2 GREEN + CLEANUP: Implement cross-script reconnect and remove LINK_CLASSES dead code** - `5656fd7` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD tasks — test commit (RED) then feat commit (GREEN)_

## Files Created/Modified
- `tests/test_cross_script_paste.py` - 11 unit tests covering FQNN extraction, cross-script reconnect (found/not-found), Dot exclusion gate, LINK_SOURCE_CLASSES membership, ANCHOR_LINK_CLASS_KNOB_NAME removal
- `paste_hidden.py` - Added `_extract_display_name_from_fqnn()`, cross-script reconnect block in Path A/C, XSCRIPT-02 comment in Path B, updated import and LINK_CLASSES references
- `constants.py` - LINK_CLASSES dict replaced with LINK_SOURCE_CLASSES frozenset; ANCHOR_LINK_CLASS_KNOB_NAME removed
- `.planning/REQUIREMENTS.md` - PASTE-04, XSCRIPT-01, XSCRIPT-02 marked complete

## Decisions Made
- Dot anchors excluded from cross-script name lookup via `node.Class() != 'Dot'` guard — Dot identity is positional, not name-stable across scripts
- `LINK_SOURCE_CLASSES` frozenset replaces `LINK_CLASSES` dict since link class values (PostageStamp/NoOp) are determined at anchor creation time, not paste time
- `find_anchor_by_name()` imported at module top-level; offline tests stub Qt and tabtabtab modules to avoid PySide2/PySide6 import failure in CI
- Empty display name after ANCHOR_PREFIX strip (e.g. `'Anchor_'` → `''`) is treated as no-match — avoids lookup for malformed FQNNs

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added Qt/tabtabtab stubs to test file**
- **Found during:** Task 2 (GREEN phase test run)
- **Issue:** Top-level `from anchor import find_anchor_by_name` in paste_hidden.py triggered anchor.py's `import tabtabtab`, which requires PySide6 or PySide2 — neither available in offline test environment
- **Fix:** Added `PySide6`, `PySide6.QtCore`, `PySide6.QtGui`, `PySide6.QtWidgets`, and `tabtabtab` module stubs to the test file's stub setup block (before any local imports)
- **Files modified:** tests/test_cross_script_paste.py
- **Verification:** All 11 tests pass with `python3 -m pytest tests/test_cross_script_paste.py -v`
- **Committed in:** `5656fd7` (Task 2 commit)

**2. [Rule 1 - Bug] Updated stale LINK_CLASSES comments in copy_hidden() docstring and Path A comment**
- **Found during:** Task 2 post-verification grep
- **Issue:** Two comment strings still referenced `LINK_CLASSES` after the rename to `LINK_SOURCE_CLASSES`
- **Fix:** Updated both references to `LINK_SOURCE_CLASSES` in the docstring and the Path A inline comment
- **Files modified:** paste_hidden.py
- **Verification:** `grep -n "LINK_CLASSES" paste_hidden.py constants.py` returns no matches
- **Committed in:** `5656fd7` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 stale comment bug)
**Impact on plan:** Auto-fixes required for test viability and code consistency. No scope creep.

## Issues Encountered
None beyond the deviation items above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- XSCRIPT-01 and XSCRIPT-02 complete; cross-script paste reconnect is fully implemented
- Phase 2 Plan 1 is the only plan in phase 02; phase is complete
- Phase 3 (anchor color system) or Phase 4 (navigation) can proceed

---
*Phase: 02-cross-script-paste*
*Completed: 2026-03-05*
