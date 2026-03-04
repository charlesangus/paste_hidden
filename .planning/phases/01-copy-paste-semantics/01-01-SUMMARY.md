---
phase: 01-copy-paste-semantics
plan: 01
subsystem: link-detection
tags: [nuke, python, knob, PostageStamp, NoOp, anchor]

# Dependency graph
requires: []
provides:
  - ANCHOR_LINK_CLASS_KNOB_NAME constant in constants.py
  - detect_link_class_for_node() with channel-inspection fallback and NoOp default
  - get_link_class_for_anchor() that reads stored class from anchor node knob
  - get_link_class_for_source() dispatches through anchor path first
  - create_anchor_named() stores detected link class as hidden knob at creation time
affects: [02-copy-paste-semantics, paste_hidden paste path]

# Tech tracking
tech-stack:
  added: []
  patterns: [detect-once-at-creation, hidden-knob-cache, NoOp-fallback-for-inconclusive-detection]

key-files:
  created: []
  modified:
    - constants.py
    - link.py
    - anchor.py

key-decisions:
  - "Detect link class once at anchor creation time and cache on hidden knob rather than re-deriving at paste time (avoids repeated channel inspection overhead)"
  - "NoOp is the safe fallback for all inconclusive detection cases (LINK-04) including None input, API errors, and unknown channel types"
  - "Channel-inspection heuristic uses prefix matching on rgba/depth/forward to distinguish 2D streams from 3D/geo streams"

patterns-established:
  - "Hidden-knob cache: expensive detection results stored as hidden String_Knob on the node at creation time, read cheaply at use time"
  - "Dispatch first: get_link_class_for_source() checks anchor path before Dot/LINK_CLASSES to ensure stored class is always preferred over re-detection"

requirements-completed: [LINK-01, LINK-02, LINK-03, LINK-04]

# Metrics
duration: 2min
completed: 2026-03-04
---

# Phase 1 Plan 1: Stream-Type Detection Infrastructure Summary

**Stream-type detection infrastructure added: link class cached on anchor's hidden knob at creation time using channel inspection with NoOp fallback, fixing Camera-produces-PostageStamp bug (LINK-03)**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-04T12:25:09Z
- **Completed:** 2026-03-04T12:26:25Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- `ANCHOR_LINK_CLASS_KNOB_NAME = 'paste_hidden_anchor_link_class'` added to constants.py
- `detect_link_class_for_node()` inspects Nuke channels() API to classify unknown node types, falling back to NoOp on any error or missing data
- `get_link_class_for_anchor()` reads the cached class from the anchor's hidden knob
- `get_link_class_for_source()` updated to dispatch through anchor path first, so Camera anchors return NoOp rather than PostageStamp
- `create_anchor_named()` calls `_store_link_class_on_anchor()` after setting tile_color, persisting the detected class as a hidden String_Knob

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ANCHOR_LINK_CLASS_KNOB_NAME constant and stream detection helpers** - `d13aebf` (feat)
2. **Task 2: Store detected link class on anchor at creation time** - `2fcdba5` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `constants.py` - Added ANCHOR_LINK_CLASS_KNOB_NAME constant
- `link.py` - Added detect_link_class_for_node(), get_link_class_for_anchor(), updated get_link_class_for_source()
- `anchor.py` - Added _store_link_class_on_anchor() helper, updated create_anchor_named() to call it

## Decisions Made
- Detect-once-at-creation pattern chosen over re-detection on every paste: anchor creation is rare, paste is frequent
- NoOp chosen as universal fallback (not PostageStamp) because a missed 3D/geo classification is worse than a missed 2D classification
- Channel prefix heuristic (`rgba`, `depth`, `forward`) is intentionally simple and wraps all Nuke API access in try/except to remain robust across Nuke versions

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Detection infrastructure is in place; subsequent plans in this phase can use `get_link_class_for_source()` with confidence that anchor nodes return the correct stored class
- No blockers

## Self-Check: PASSED

- FOUND: constants.py
- FOUND: link.py
- FOUND: anchor.py
- FOUND: 01-01-SUMMARY.md
- FOUND: d13aebf (Task 1 commit)
- FOUND: 2fcdba5 (Task 2 commit)

---
*Phase: 01-copy-paste-semantics*
*Completed: 2026-03-04*
