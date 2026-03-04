# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-03)

**Core value:** Copy and paste must reconnect predictably — anchors provide stable, navigable references; hidden inputs reconnect to their source without ceremony.
**Current focus:** Phase 1 — Copy-Paste Semantics

## Current Position

Phase: 1 of 4 (Copy-Paste Semantics)
Plan: 1 of ? in current phase
Status: In progress
Last activity: 2026-03-04 — Completed 01-01 (stream-type detection infrastructure)

Progress: [█░░░░░░░░░] 10%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 2 min
- Total execution time: 2 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-copy-paste-semantics | 1 | 2 min | 2 min |

**Recent Trend:**
- Last 5 plans: 2 min
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
- Channel-inspection heuristic uses prefix matching on rgba/depth/forward to distinguish 2D from 3D/geo streams (01-01)

### Pending Todos

None.

### Blockers/Concerns

- NAV-03 (browser-style forward/back history) is a stretch goal; if scope expands it may be deferred to v2 during planning

## Session Continuity

Last session: 2026-03-04
Stopped at: Completed 01-01-PLAN.md — stream-type detection infrastructure (constants.py, link.py, anchor.py)
Resume file: None
