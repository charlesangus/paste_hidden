---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
last_updated: "2026-03-10T03:38:52.050Z"
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 13
  completed_plans: 13
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-03)

**Core value:** Copy and paste must reconnect predictably — anchors provide stable, navigable references; hidden inputs reconnect to their source without ceremony.
**Current focus:** Phase 4 — Anchor Navigation (complete)

## Current Position

Phase: 4 of 5 (Anchor Navigation) — COMPLETE
Plan: 03 of 3 complete in current phase (W0=scaffold, 01=back-position, 02=backdrop picker)
Status: Phase 4 complete — all plans done; human-verified all 7 NAV-01/NAV-02/FIND-01 behaviors
Last activity: 2026-03-10 — Completed 04-02 Task 2 (human-verify approved); Phase 4 done

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 3.2 min
- Total execution time: 17 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-copy-paste-semantics | 3 | 7 min | 2.3 min |
| 02-cross-script-paste | 1 | 3 min | 3 min |
| 05-refactor-cross-script-dot-type | 1 | 7 min | 7 min |

**Recent Trend:**
- Last 5 plans: 3.2 min avg
- Trend: —

*Updated after each plan completion*
| Phase 05 P02 | 3 | 2 tasks | 4 files |
| Phase 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction P03 | 8 | 2 tasks | 3 files |
| Phase 03 P01 | 490 | 2 tasks | 4 files |
| Phase 03 P02 | 5 | 2 tasks | 1 files |
| Phase 04 PW0 | 2 | 1 tasks | 1 files |
| Phase 04 P01 | 2 | 2 tasks | 2 files |
| Phase 04-anchor-navigation P02 | 5 | 1 tasks | 1 files |
| Phase 04-anchor-navigation P03 | 1 | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Hidden-input Dots and Links are distinct systems — conflating them causes inconsistent reconnection (pending implementation)
- PostageStamp preferred for 2D links; NoOp fallback for all others (pending implementation)
- Color propagation only from our color picker, not raw tile_color changes (pending implementation)
- Cross-script reconnection for Links by name; Dots left disconnected (pending implementation)
- Detect link class once at anchor creation time and cache on hidden knob rather than re-deriving at paste time (01-01)
- NoOp is the safe fallback for all inconclusive detection cases including None input, API errors, and unknown channel types (01-01)
- Channel-inspection heuristic (rgba/depth/forward prefix matching) has been superseded by canSetInput probe (01-03)
- [Phase 01-copy-paste-semantics]: LINK_CLASSES branch ordered before HIDDEN_INPUT_CLASSES in copy_hidden() to prevent mis-routing of file nodes with hide_input set (01-02)
- [Phase 01-copy-paste-semantics]: Silent continue for unresolvable FQNNs in paste_hidden() — matches existing cross-script behavior in find_anchor_node() (01-02)
- [Phase 01-copy-paste-semantics]: canSetInput probe replaces channel-prefix heuristic for stream type detection: Nuke API answers definitively for any node class (01-03)
- [Phase 01-copy-paste-semantics]: _store_link_class_on_anchor resolves node_to_classify via anchor.input(0) when input_node is None (01-03)
- [Phase 02-cross-script-paste]: Dot anchors excluded from cross-script name lookup — Dot identity is positional, not name-stable across scripts (02-01)
- [Phase 02-cross-script-paste]: LINK_SOURCE_CLASSES frozenset replaces LINK_CLASSES dict; link class is determined at anchor creation time, not paste time (02-01)
- [Phase 02-cross-script-paste]: Qt/tabtabtab stub pattern established for offline tests that transitively import anchor.py (02-01)
- [Phase 05]: FQNN stem comparison used as cross-script gate for paste_hidden() Path B to prevent same-stem false positives (Bug 2 root cause)
- [Phase 05]: DOT_TYPE knob stamped at copy time (dot_type='link' for anchor-backed, dot_type='local' for plain-node-backed) gates all paste reconnect behavior
- [Phase 05]: rename_anchor_to Dot branch raises ValueError for empty sanitized name — consistent with NoOp path guard
- [Phase 05]: mark_dot_as_anchor() sets Dot node name to Anchor_<sanitized_label> on first call only; idempotent path (knob already present) returns early
- [Phase 05]: DOT_TYPE preservation via saved_dot_type before setup_link_node() — safer than changing setup_link_node() which is shared with anchor.py
- [Phase 05]: get_link_class_for_source() at paste time in Path A/C determines Dot vs NoOp link node class for Dot-anchor sources
- [Phase 03-01]: ColorPaletteDialog defined as None when Qt unavailable; callers guard with 'if ColorPaletteDialog is None: return'
- [Phase 03-01]: propagate_anchor_color() returns early for Dot anchors — Dot colors are system-managed
- [Phase 03-01]: create_anchor_named(color=None) falls back to find_anchor_color() for backward compatibility with create_anchor_silent()
- [Phase 03-01]: rename_anchor_to(color=None) skips propagation — explicit color opt-in only
- [Phase 03]: create_anchor() pre-selects ANCHOR_DEFAULT_COLOR when no input_node, or find_anchor_color(input_node) otherwise
- [Phase 03]: rename_anchor() reads current tile_color for ColorPaletteDialog initial_color pre-selection; calls propagate_anchor_color() when chosen_color is not None
- [Phase 04-W0]: nuke.zoom/center stubs return 1.0 and [0.0, 0.0] matching Nuke API call signatures; allNodes side_effect dispatches by class_name for BackdropNode vs anchor queries
- [Phase 04-01]: invoke() variable renamed from anchor_node to node to accommodate BackdropNode dispatch; navigate_to_backdrop() stub added for test patchability before Plan 02 body
- [Phase 04-01]: navigate_back() sets _back_position = None before calling nuke.zoom() to prevent double-restore on raise
- [Phase 04-anchor-navigation]: navigate_to_backdrop() body and invoke() BackdropNode dispatch were already in place from Plan 01 stub — no re-implementation needed in Plan 02
- [Phase 04-anchor-navigation]: get_items() uses for-loop append pattern for Backdrop entries to keep anchor/backdrop logic visually separate and readable
- [Phase 04-anchor-navigation]: NAV-03 (full browser-style forward/back history stack) formally recorded as deferred to v2 — single-slot back (NAV-01/02) is what shipped in Phase 4

### Pending Todos

None.

### Roadmap Evolution

- Phase 5 added: Refactor cross-script paste logic for hidden-input Dot vs Anchor Dot distinction

### Blockers/Concerns

- NAV-03 (browser-style forward/back history) is a stretch goal; if scope expands it may be deferred to v2 during planning

## Session Continuity

Last session: 2026-03-10
Stopped at: Completed 04-02-PLAN.md (Phase 4 complete — human-verified all 7 NAV-01/NAV-02/FIND-01 behaviors)
Resume file: None
