---
phase: 01-copy-paste-semantics
plan: 02
subsystem: copy-paste
tags: [nuke, python, anchor, PostageStamp, NoOp, LINK_CLASSES, hidden-input]

# Dependency graph
requires:
  - phase: 01-copy-paste-semantics/01-01
    provides: is_anchor(), get_link_class_for_source() dispatch to anchor knob, add_input_knob(), setup_link_node(), find_anchor_node()
provides:
  - copy_hidden() with three-path classification (LINK_CLASSES file node, hidden-input Dot, anchor node)
  - paste_hidden() reading link class through get_link_class_for_source() with anchor-knob dispatch
  - Silent cross-script disconnection for legacy Dots (PASTE-03/PASTE-04)
affects: [03-copy-paste-semantics, paste tests, cut_hidden]

# Tech tracking
tech-stack:
  added: []
  patterns: [LINK_CLASSES-first-ordering, anchor-scan-by-identity, silent-skip-on-none-input]

key-files:
  created: []
  modified:
    - paste_hidden.py

key-decisions:
  - "LINK_CLASSES branch ordered before HIDDEN_INPUT_CLASSES in copy_hidden() to prevent a file node with hide_input set from being mis-routed into the Dot branch"
  - "Anchor scan in Path A uses identity check (candidate.input(0) is node) rather than name comparison to handle renamed nodes correctly"
  - "paste_hidden() issues a silent continue for unresolvable FQNNs in both the link-creation and Dot-reconnect branches — no error raised, placeholder node left in place"

patterns-established:
  - "LINK_CLASSES-first ordering: checking LINK_CLASSES before HIDDEN_INPUT_CLASSES prevents ambiguous node classes from being mis-classified when hide_input is set"
  - "Anchor scan by identity: scanning allNodes() with candidate.input(0) is node is safe because identity checks work within a single script and return no false positives"

requirements-completed: [PASTE-01, PASTE-03]

# Metrics
duration: 1min
completed: 2026-03-04
---

# Phase 1 Plan 2: Copy-Paste Routing Summary

**Three-path copy/paste routing in paste_hidden.py: LINK_CLASSES nodes route through anchor scan first; hidden-input Dots split on anchor vs non-anchor input; paste reads link class from anchor's stored knob so Camera anchor correctly produces NoOp and Read anchor produces PostageStamp**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-04T12:28:54Z
- **Completed:** 2026-03-04T12:30:07Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- `copy_hidden()` rewritten with three explicit paths: Path A (LINK_CLASSES file node with anchor scan), Path B (hidden-input Dot with anchor-vs-non-anchor split), Path C (anchor node)
- Path A scans `nuke.allNodes()` for an anchor whose `input(0)` is the file node by identity; stores anchor FQNN when found, file node FQNN as legacy fallback
- `paste_hidden()` dispatch reordered to check `LINK_CLASSES.keys() or is_anchor(node)` first, then `HIDDEN_INPUT_CLASSES`
- `get_link_class_for_source(input_node)` now used in paste, correctly dispatching to the anchor's stored knob to return NoOp for Camera anchors and PostageStamp for Read anchors (LINK-03 fix)
- Unresolvable FQNNs (cross-script, deleted nodes) silently skipped in both branches (PASTE-03/PASTE-04)

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite copy_hidden() with three-path classification** - `f156b30` (feat)
2. **Task 2: Update paste_hidden() for anchor-aware link class lookup** - `f046c79` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `paste_hidden.py` - copy_hidden() three-path classification; paste_hidden() anchor-aware dispatch

## Decisions Made
- LINK_CLASSES branch ordered first in `copy_hidden()` because a Read or Camera node with `hide_input` set could otherwise fall into the HIDDEN_INPUT_CLASSES branch — class membership is a stronger signal than hide_input state
- Identity check (`candidate.input(0) is node`) used for anchor scan rather than name comparison, so renamed nodes are found correctly and there are no false positives from nodes with similar names
- Silent `continue` on unresolvable FQNN chosen over raising an error, matching the existing cross-script behavior established in find_anchor_node()

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- paste_hidden.py now routes all three copy paths correctly; subsequent plans can build on this routing behavior
- Camera anchor → NoOp and Read anchor → PostageStamp are both handled correctly via get_link_class_for_source()
- No blockers

## Self-Check: PASSED

- FOUND: paste_hidden.py
- FOUND: f156b30 (Task 1 commit)
- FOUND: f046c79 (Task 2 commit)

---
*Phase: 01-copy-paste-semantics*
*Completed: 2026-03-04*
