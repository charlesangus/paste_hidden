---
phase: 01-copy-paste-semantics
plan: 03
subsystem: testing
tags: [nuke, canSetInput, anchor, stream-detection, tdd, probe]

# Dependency graph
requires:
  - phase: 01-copy-paste-semantics
    plan: 01
    provides: "detect_link_class_for_node() in link.py; _store_link_class_on_anchor() in anchor.py; LINK_CLASSES fast-path"
provides:
  - "probe_stream_type_via_can_set_input() in link.py: canSetInput-based stream type probe replacing channel-prefix heuristic"
  - "Updated detect_link_class_for_node(): delegates unknown node classes to probe instead of channels() API"
  - "Updated _store_link_class_on_anchor(): resolves node_to_classify via anchor.input(0) when input_node is None"
  - "tests/test_link_probe.py: 16 unit tests for probe function and detect_link_class_for_node()"
  - "tests/test_anchor_store_link_class.py: 8 unit tests for _store_link_class_on_anchor()"
affects: [anchor creation, link creation, paste semantics, stream type detection]

# Tech tracking
tech-stack:
  added: ["tests/ directory with pytest-compatible unit tests", "nuke stub module for offline testing"]
  patterns: ["canSetInput probe pattern for definitive stream type detection", "TDD with stub nuke module for Nuke-API-dependent code"]

key-files:
  created:
    - "tests/__init__.py"
    - "tests/test_link_probe.py"
    - "tests/test_anchor_store_link_class.py"
  modified:
    - "link.py"
    - "anchor.py"

key-decisions:
  - "Replace channel-name prefix heuristic with canSetInput probe: Nuke's own API definitively answers stream type for arbitrary node classes without relying on channel names"
  - "Probe parameter named node_to_probe (not anchor_node): canSetInput is called on the source node being classified, not on an anchor"
  - "anchor.input(0) fallback in _store_link_class_on_anchor: probe runs against connected node rather than receiving None when anchor is already wired at creation time"
  - "All three scratch node classes (NoOp, Scene, DeepMerge) always deleted in finally block regardless of probe result or exception (LINK-04 preserved)"

patterns-established:
  - "Nuke stub pattern: _StubNode with configurable _can_set_input_results dict enables testing canSetInput behavior without Nuke runtime"
  - "Probe-first fallback: unknown node classes go to canSetInput probe; exceptions always return NoOp"

requirements-completed: [LINK-01, LINK-02, LINK-03, LINK-04]

# Metrics
duration: 4min
completed: 2026-03-04
---

# Phase 01 Plan 03: canSetInput Stream Probe Summary

**canSetInput probe replaces channel-prefix heuristic in detect_link_class_for_node(), correctly classifying arbitrary 2D/3D/Deep node types; _store_link_class_on_anchor() now probes via anchor.input(0) when input_node is None**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-04T12:41:26Z
- **Completed:** 2026-03-04T12:57:53Z
- **Tasks:** 2 (each with RED/GREEN TDD cycle)
- **Files modified:** 4 (link.py, anchor.py, tests/test_link_probe.py, tests/test_anchor_store_link_class.py)

## Accomplishments
- Added `probe_stream_type_via_can_set_input(node_to_probe)` to link.py: creates NoOp/Scene/DeepMerge scratch nodes, calls canSetInput(0, scratch) on each, returns PostageStamp (2D) or NoOp (3D/Deep/unknown), deletes all scratch nodes in finally block
- Replaced channel-prefix heuristic (`_2D_CHANNEL_PREFIXES` + `source_node.channels()`) in `detect_link_class_for_node()` with call to probe; LINK_CLASSES fast-path and Dot early-return preserved
- Updated `_store_link_class_on_anchor()`: resolves `node_to_classify = input_node if input_node is not None else anchor_node.input(0)` so Camera/3D nodes anchored while selected are classified correctly
- Created test infrastructure (`tests/` directory with nuke stub) and 24 unit tests covering all probe behaviors and edge cases

## Task Commits

Each task was committed atomically with RED/GREEN TDD:

1. **Task 1 RED: Failing tests for probe + detect_link_class** - `e086635` (test)
2. **Task 1 GREEN: probe_stream_type_via_can_set_input + replace heuristic** - `da31f33` (feat)
3. **Task 2 RED: Failing tests for _store_link_class_on_anchor input(0) probe** - `a4e384a` (test)
4. **Task 2 GREEN: _store_link_class_on_anchor probes anchor.input(0)** - `cf36101` (feat)

## Files Created/Modified
- `link.py` - Added `probe_stream_type_via_can_set_input()`, replaced channel-inspection fallback, removed `_2D_CHANNEL_PREFIXES`
- `anchor.py` - Updated `_store_link_class_on_anchor()` to resolve `node_to_classify` via `anchor_node.input(0)` when `input_node` is None
- `tests/__init__.py` - Package marker for pytest discovery
- `tests/test_link_probe.py` - 16 tests for probe function and detect_link_class_for_node()
- `tests/test_anchor_store_link_class.py` - 8 tests for _store_link_class_on_anchor()

## Decisions Made
- **canSetInput over channels()**: Nuke's API answers stream type definitively for any node class, while channel-prefix inspection was fragile (only 3 prefixes, had to be updated for new node types)
- **Parameter named node_to_probe**: Plan's `anchor_node` parameter name in the function description was confusing — the probe is actually called on the source node being classified. Clear naming avoids future confusion.
- **anchor.input(0) fallback**: The UAT failure root cause was that `create_anchor_named()` calls `_store_link_class_on_anchor(anchor, input_node)` with the original `input_node`, but the anchor is already wired to it via `anchor.setInput(0, input_node)`. If input_node is None for any reason, the fallback ensures the connected node is still probed.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None — stub nuke module pattern adapted from existing `node_layout/tests/` infrastructure. All tests passed first run after implementation.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 LINK-0x requirements now implemented and tested
- Stream type detection is generic (works for any future Nuke node class, not just 8 known types)
- 24 unit tests provide regression protection for probe behavior
- Phase 01 is complete: copy-paste semantics for all anchor/link/hidden-input node types

---
*Phase: 01-copy-paste-semantics*
*Completed: 2026-03-04*

## Self-Check: PASSED

All files and commits verified present.
