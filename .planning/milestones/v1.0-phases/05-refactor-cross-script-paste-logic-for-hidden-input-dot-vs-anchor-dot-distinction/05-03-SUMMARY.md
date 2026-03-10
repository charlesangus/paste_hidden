---
phase: 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction
plan: 03
subsystem: paste
tags: [nuke, paste_hidden, dot_type, local_dot, constants, tdd]

# Dependency graph
requires:
  - phase: 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction
    provides: DOT_TYPE knob stamped at copy time; Link/Local Dot cross-script paste routing

provides:
  - LOCAL_DOT_COLOR darkened to 0x7A3A00FF in constants.py
  - paste_hidden() Path B same-script re-stamps DOT_TYPE knob via saved_dot_type pattern
  - paste_hidden() Path A/C uses get_link_class_for_source() so Dot anchors produce Dot link nodes
  - 4 new TDD tests covering all three fixes

affects:
  - 05-02 (Dot anchor node name sync — pre-existing unrelated failures remain)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Save knob value before stripping call, re-stamp after — used for DOT_TYPE knob around setup_link_node()"
    - "get_link_class_for_source() at paste time determines Dot vs NoOp link node class"

key-files:
  created:
    - tests/test_dot_type_distinction.py (4 new test classes/tests appended)
  modified:
    - constants.py
    - paste_hidden.py

key-decisions:
  - "DOT_TYPE preservation via saved_dot_type before setup_link_node() — safer than changing setup_link_node() which is shared with anchor.py"
  - "get_link_class_for_source() already existed in link.py but was not imported in paste_hidden.py — added to imports as a Rule 3 (blocking) fix"

patterns-established:
  - "saved_dot_type pattern: read knob value before a call that strips it, re-stamp after via add_input_knob(node, dot_type=saved)"

requirements-completed: [XSCRIPT-01, XSCRIPT-02]

# Metrics
duration: 8min
completed: 2026-03-05
---

# Phase 05 Plan 03: LOCAL_DOT_COLOR Darkening + DOT_TYPE Re-stamp + Path A/C Link Class Fix Summary

**Three UAT gap fixes: darkened LOCAL_DOT_COLOR constant (0x7A3A00FF), saved_dot_type re-stamp pattern to survive setup_link_node() knob-stripping, and get_link_class_for_source() in Path A/C to produce Dot link nodes for Dot anchors**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-05T14:00:00Z
- **Completed:** 2026-03-05T14:08:00Z
- **Tasks:** 2 (RED + GREEN; no REFACTOR needed)
- **Files modified:** 3

## Accomplishments

- `LOCAL_DOT_COLOR` darkened from `0xB35A00FF` to `0x7A3A00FF` (approximately 30% darker burnt orange, closes UAT visual gap)
- Same-script Local Dot paste now correctly re-stamps the `DOT_TYPE_KNOB_NAME` knob after `setup_link_node()` strips it, making `add_input_knob(node, dot_type='local')` the re-stamp mechanism rather than the broken post-hoc knob check
- Both `nuke.createNode('NoOp')` hardcoded calls in Path A/C replaced with `nuke.createNode(get_link_class_for_source(...))`, so pasting a Dot-backed anchor produces a Dot link node instead of a NoOp
- 4 new failing tests written (RED), all 4 pass after implementation (GREEN); all 16 pre-existing tests continue to pass (20 total in `test_dot_type_distinction.py`)

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — failing tests** - `334929a` (test)
2. **Task 2: GREEN — implementation** - `df65a84` (feat)

## Files Created/Modified

- `/home/latuser/git/nuke_layout_project/paste_hidden/constants.py` — LOCAL_DOT_COLOR changed to 0x7A3A00FF
- `/home/latuser/git/nuke_layout_project/paste_hidden/paste_hidden.py` — get_link_class_for_source added to imports; Path B same-script uses saved_dot_type + re-stamp; Path A/C uses get_link_class_for_source()
- `/home/latuser/git/nuke_layout_project/paste_hidden/tests/test_dot_type_distinction.py` — 4 new test classes appended: TestLocalDotColorValue, TestPasteHiddenSameScriptDotTypeKnobPreservation, TestPasteHiddenPathACLinkClass (2 tests)

## Decisions Made

- **DOT_TYPE preservation via saved_dot_type** — reading the knob value before `setup_link_node()` and re-stamping via `add_input_knob(node, dot_type='local')` after is safer than modifying `setup_link_node()` itself, which is also called from `anchor.py` paths where stripping `DOT_TYPE_KNOB_NAME` is the correct behavior.
- **get_link_class_for_source() was missing from paste_hidden.py imports** — it existed in `link.py` already but was not in the `from link import (...)` block. Added as a Rule 3 (blocking) fix before applying the Path A/C change.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added get_link_class_for_source to paste_hidden.py imports**
- **Found during:** Task 2 (GREEN — implementation of Path A/C fix)
- **Issue:** `get_link_class_for_source` was not imported in `paste_hidden.py` despite the plan assuming it was already available
- **Fix:** Added `get_link_class_for_source` to the `from link import (...)` block
- **Files modified:** `paste_hidden.py`
- **Verification:** Tests pass; `nuke.createNode(get_link_class_for_source(...))` resolves correctly
- **Committed in:** `df65a84` (Task 2 commit)

**2. [Rule 3 - Blocking] Added 'selected' knob to Path A/C test stub nodes**
- **Found during:** Task 1 (RED — test writing) — revealed during test execution
- **Issue:** The `created_link_node` stubs in `TestPasteHiddenPathACLinkClass` lacked a `'selected'` knob, causing `KeyError: 'selected'` in paste_hidden()'s final selection-restore loop
- **Fix:** Added `'selected': _make_knob(False)` to both `created_link_node` stub `knobs_dict` dicts
- **Files modified:** `tests/test_dot_type_distinction.py`
- **Verification:** Tests fail for the correct reason after fix (wrong createNode argument, not KeyError)
- **Committed in:** `334929a` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes essential for tests to run and implementation to import correctly. No scope creep.

## Issues Encountered

- `test_dot_anchor_name_sync.py` has 6 pre-existing failures (from plan 05-02's unimplemented `rename_anchor_to()` Dot-anchor path and `setName()` absence in StubNode). These are not caused by plan 05-03 and are documented in `deferred-items.md`.

## Next Phase Readiness

- All three UAT gaps closed: LOCAL_DOT_COLOR darkened, Local Dot DOT_TYPE knob survives paste, Dot anchor paste produces Dot link node
- `test_dot_anchor_name_sync.py` failures remain as a known deferred item for a follow-up plan implementing Dot anchor `setName()` and `rename_anchor_to()` completion
- UAT re-run in Nuke recommended to confirm visual and functional behavior matches test expectations

---
*Phase: 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction*
*Completed: 2026-03-05*
