---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
last_updated: "2026-03-05T13:38:44.433Z"
progress:
  total_phases: 3
  completed_phases: 3
  total_plans: 5
  completed_plans: 5
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-03)

**Core value:** Copy and paste must reconnect predictably — anchors provide stable, navigable references; hidden inputs reconnect to their source without ceremony.
**Current focus:** Phase 5 — Refactor cross-script paste logic for hidden-input Dot vs Anchor Dot distinction (complete)

## Current Position

Phase: 5 of 5 (Refactor Cross-Script Paste Logic for DOT_TYPE Distinction)
Plan: 1 of 1 in current phase (phase complete)
Status: Phase 5 complete
Last activity: 2026-03-05 — Completed 05-01 (DOT_TYPE knob stamped at copy; Link Dots reconnect cross-script; Local Dots are no-op cross-script; same-stem false positive fixed)

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

### Pending Todos

None.

### Roadmap Evolution

- Phase 5 added: Refactor cross-script paste logic for hidden-input Dot vs Anchor Dot distinction

### Blockers/Concerns

- NAV-03 (browser-style forward/back history) is a stretch goal; if scope expands it may be deferred to v2 during planning

## Session Continuity

Last session: 2026-03-05
Stopped at: Completed 05-01-PLAN.md — DOT_TYPE knob distinction for Link/Local Dot cross-script paste
Resume file: None
