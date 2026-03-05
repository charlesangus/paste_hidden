---
phase: 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction
plan: 01
subsystem: paste-logic
tags: [nuke, python, tdd, copy-paste, hidden-input, dot-type, link-dot, local-dot]

requires:
  - phase: 02-cross-script-paste
    provides: "cross-script anchor reconnect via find_anchor_by_name(); FQNN storage on paste nodes"

provides:
  - "DOT_TYPE_KNOB_NAME='paste_hidden_dot_type' and LOCAL_DOT_COLOR=0xB35A00FF constants in constants.py"
  - "add_input_knob(node, dot_type=None) — conditionally stamps a hidden DOT_TYPE String_Knob on copy"
  - "copy_hidden() Path B: anchor-backed Dots stamped as 'link' with ANCHOR_DEFAULT_COLOR; plain-node Dots stamped as 'local' with LOCAL_DOT_COLOR and 'Local: ' label"
  - "paste_hidden() Path B: FQNN-stem cross-script gate; Link Dots reconnect to same-named anchor; Local Dots are unconditional no-op cross-script; same-script Local Dots restore Local appearance after reconnect"
  - "Backward compat: nodes lacking DOT_TYPE_KNOB_NAME infer type from FQNN anchor-prefix"
  - "16-test offline suite (test_dot_type_distinction.py) covering all new DOT_TYPE behaviors"

affects:
  - "future phases modifying copy_hidden() or paste_hidden() Path B"
  - "UAT for XSCRIPT-01 (Link Dot cross-script reconnect) and XSCRIPT-02 (Local Dot cross-script no-op)"

tech-stack:
  added: []
  patterns:
    - "DOT_TYPE knob stamped at copy time — single-source-of-truth for paste routing"
    - "FQNN stem comparison (not find_anchor_node() return value) as cross-script gate to prevent same-stem false positives"
    - "Backward compat inference: anchor FQNN last segment → 'link'; plain FQNN → 'local'"

key-files:
  created:
    - tests/test_dot_type_distinction.py
  modified:
    - constants.py
    - link.py
    - paste_hidden.py

key-decisions:
  - "FQNN stem comparison used as cross-script gate instead of find_anchor_node() return value — prevents same-stem false positives where a same-named node in the destination script would incorrectly reconnect a Local Dot (Bug 2 root cause)"
  - "DOT_TYPE knob managed inside add_input_knob() via remove-then-re-add cycle, keeping it last in knob order alongside TAB_NAME and KNOB_NAME"
  - "Link Dot tile_color always overridden to ANCHOR_DEFAULT_COLOR at copy time — setup_link_node() uses find_node_color() which may return a custom anchor color that would be misleading"
  - "Local Dot appearance restoration happens after setup_link_node() in both copy and paste paths — setup_link_node() always overwrites label and color"
  - "Backward compat fallback: nodes lacking DOT_TYPE_KNOB_NAME infer type from FQNN anchor-prefix (_extract_display_name_from_fqnn returning non-None → 'link', else → 'local')"

patterns-established:
  - "DOT_TYPE gate at top of paste_hidden() Path B: compute dot_type before checking input_node, because same-stem false positives make input_node non-None even for cross-script Local Dots"
  - "Test pattern: patch 'paste_hidden.is_link' to False in copy_hidden() tests when node has KNOB_NAME pre-populated for setText() to succeed"

requirements-completed: [XSCRIPT-01, XSCRIPT-02]

duration: 7min
completed: 2026-03-05
---

# Phase 05 Plan 01: DOT_TYPE Link/Local Dot Distinction Summary

**DOT_TYPE knob stamped at copy time gates cross-script paste: Link Dots reconnect to same-named anchors; Local Dots are unconditional no-ops cross-script; same-stem false positives (Bug 2) eliminated via FQNN stem comparison**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-05T13:30:20Z
- **Completed:** 2026-03-05T13:37:00Z
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 4

## Accomplishments

- Introduced `DOT_TYPE_KNOB_NAME` and `LOCAL_DOT_COLOR` constants; Link Dots now visually distinct (canonical purple) from Local Dots (burnt orange) at copy time
- Fixed Bug 1: Link Dots now reconnect cross-script to same-named anchors via `find_anchor_by_name()`
- Fixed Bug 2: Local Dots can no longer falsely reconnect cross-script when source and destination scripts share the same filename stem — FQNN stem comparison replaces `find_anchor_node()` as the cross-script gate in Path B
- Preserved PASTE-03: same-script Local Dots still reconnect by identity and restore Local appearance after `setup_link_node()` overwrites it
- 16 new offline tests (pytest, no Nuke required) covering all DOT_TYPE behaviors; all 27 tests (new + pre-existing) pass

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — Failing tests for DOT_TYPE Link/Local Dot distinction** - `ac288b0` (test)
2. **Task 2: GREEN — Implement DOT_TYPE knob distinction — constants, link.py, paste_hidden.py** - `ae93729` (feat)

_Note: TDD tasks have two commits (test RED → feat GREEN). Test file was also updated in the GREEN commit to fix stub incompatibilities discovered during implementation (StubKnob missing setText/setFlag, is_link patch required for copy_hidden tests)._

## Files Created/Modified

- `tests/test_dot_type_distinction.py` — 16-test offline suite covering copy_hidden() Path B DOT_TYPE assignment, paste_hidden() Path B cross-script/same-script DOT_TYPE routing, add_input_knob() extension, and backward compat inference
- `constants.py` — Added `DOT_TYPE_KNOB_NAME = 'paste_hidden_dot_type'` and `LOCAL_DOT_COLOR = 0xB35A00FF`
- `link.py` — Extended `add_input_knob(node, dot_type=None)` with DOT_TYPE_KNOB_NAME knob removal in re-add cycle and conditional DOT_TYPE String_Knob creation
- `paste_hidden.py` — Updated imports; copy_hidden() Path B now sets dot_type and Local appearance; paste_hidden() Path B replaced with FQNN-stem cross-script gate and DOT_TYPE-gated reconnect logic

## Decisions Made

- FQNN stem comparison used as cross-script gate (not `find_anchor_node()` return value) — prevents same-stem false positives
- `add_input_knob()` manages DOT_TYPE knob removal/re-addition to maintain correct knob order
- Link Dot color always forced to ANCHOR_DEFAULT_COLOR at copy time (canonical purple, not anchor's custom tile_color)
- Backward compat fallback: anchor-prefix FQNN → 'link'; plain FQNN → 'local' (handles pre-Phase-5 nodes)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test stub StubKnob missing setText() and setFlag() methods**
- **Found during:** Task 2 (GREEN) — first test run after implementation
- **Issue:** copy_hidden() calls `node[KNOB_NAME].setText(stored_fqnn)` and link.py calls `tab.setFlag(nuke.INVISIBLE)`; the StubKnob created in the new test file lacked these methods (unlike the existing test which works because those tests don't exercise those code paths directly)
- **Fix:** Added `setText()` and `setFlag()` to StubKnob in test_dot_type_distinction.py
- **Files modified:** tests/test_dot_type_distinction.py
- **Committed in:** ae93729 (Task 2 commit)

**2. [Rule 1 - Bug] copy_hidden() tests skipped node due to is_link() check on pre-populated KNOB_NAME**
- **Found during:** Task 2 (GREEN) — copy_hidden tests failed because node had KNOB_NAME in knobs, so is_link() returned True and copy_hidden() skipped with `continue`
- **Issue:** _make_dot_node_with_hide_input() included KNOB_NAME for the setText() call, but that made is_link() return True
- **Fix:** Added `patch('paste_hidden.is_link', return_value=False)` to all 5 copy_hidden() test cases
- **Files modified:** tests/test_dot_type_distinction.py
- **Committed in:** ae93729 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — test stub bugs)
**Impact on plan:** Both fixes were required to make the tests work correctly in the offline environment. No scope creep; implementation code required no changes beyond the plan.

## Issues Encountered

None in the implementation code. Two stub incompatibilities were discovered in the test file during the GREEN phase and auto-fixed inline.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- DOT_TYPE distinction is now in place; UAT for XSCRIPT-01 (Link Dot cross-script reconnect) and Bug 2 (Local Dot same-stem false positive) can proceed
- The `is_anchor()` legacy label-based heuristic in link.py may still classify unexpected Dots as anchors — noted as pre-existing concern, not introduced by this phase
- All 27 offline tests pass; no known regressions

---
*Phase: 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction*
*Completed: 2026-03-05*

## Self-Check: PASSED

- constants.py: FOUND
- link.py: FOUND
- paste_hidden.py: FOUND
- tests/test_dot_type_distinction.py: FOUND
- 05-01-SUMMARY.md: FOUND
- Commit ac288b0 (RED): FOUND
- Commit ae93729 (GREEN): FOUND
- Test suite: 27 passed, 0 failed
