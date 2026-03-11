---
phase: 06-preferences-infrastructure
plan: 03
subsystem: infra
tags: [python, nuke, preferences, plugin_enabled, link_classes_paste_mode, clipboard]

# Dependency graph
requires:
  - phase: 06-01
    provides: prefs.py singleton with plugin_enabled and link_classes_paste_mode module-level vars
provides:
  - plugin_enabled early-return guards in copy_hidden(), cut_hidden(), paste_hidden()
  - link_classes_paste_mode passthrough gate in copy_hidden() Path A LINK_SOURCE_CLASSES branch
  - paste_hidden.py now imports prefs and transparently falls through to Nuke defaults when disabled
affects:
  - 06-04
  - 07-prefs-dialog

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Early-return guard: plugin_enabled checked as first statement in each clipboard function, before any plugin logic executes
    - Passthrough continue: link_classes_paste_mode == 'passthrough' uses continue to skip FQNN stamping, allowing plain nuke.nodeCopy() at end of function to handle the node
    - Ungated fallback functions: copy_old/cut_old/paste_old remain entirely outside the plugin_enabled gate (always active regardless of prefs)

key-files:
  created: []
  modified:
    - paste_hidden.py

key-decisions:
  - "plugin_enabled guard placed as the very first statement in each function body — no plugin logic can execute when disabled"
  - "link_classes_paste_mode gate uses continue (not return) in copy_hidden() Path A loop — plain copy still happens via nuke.nodeCopy() at end of function"
  - "copy_old/cut_old/paste_old are explicitly not gated — they are always-available fallback commands independent of plugin state"

patterns-established:
  - "Guard ordering: plugin_enabled check first, then link_classes_paste_mode check within Path A — coarser gate before finer gate"

requirements-completed: [PREFS-03, PREFS-04]

# Metrics
duration: 3min
completed: 2026-03-11
---

# Phase 6 Plan 03: Preferences Infrastructure — plugin_enabled and link_classes_paste_mode gates in paste_hidden.py Summary

**plugin_enabled early-return guards and link_classes_paste_mode passthrough continue added to copy_hidden, cut_hidden, and paste_hidden, with copy_old/cut_old/paste_old explicitly left ungated**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-11T12:25:21Z
- **Completed:** 2026-03-11T12:28:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Added `import prefs` to paste_hidden.py after the local imports block
- copy_hidden(): calls nuke.nodeCopy() and returns immediately when plugin_enabled is False
- cut_hidden(): copies then deletes selected nodes using plain Nuke behavior and returns when plugin_enabled is False
- paste_hidden(): calls nuke.nodePaste() and returns its result when plugin_enabled is False
- copy_hidden() Path A: skips FQNN stamping for LINK_SOURCE_CLASSES nodes when link_classes_paste_mode is 'passthrough' — node still copied plainly via nuke.nodeCopy() at end of function
- copy_old/cut_old/paste_old left completely unchanged and always active

## Task Commits

Each task was committed atomically:

1. **Task 1: Gate copy_hidden, cut_hidden, paste_hidden on plugin_enabled and add passthrough gate** - `d76bd05` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `paste_hidden.py` - Added `import prefs`, three plugin_enabled early-return guards, one link_classes_paste_mode passthrough continue in Path A

## Decisions Made

- Guard placed as first statement in each function body so absolutely no plugin logic can execute when plugin is disabled
- `continue` used (not `return`) for the link_classes_paste_mode passthrough gate because copy_hidden() is a loop — the node still reaches `nuke.nodeCopy()` at the end of the function for plain copy behavior
- copy_old/cut_old/paste_old are standalone fallback commands always active regardless of plugin state; gating them would break explicit user intent to use old behavior

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The automated verification script (`python3 -c "import paste_hidden"`) cannot run outside the Nuke runtime due to `import nuke` being unavailable. Structural verification was confirmed via grep checks, which match the plan's overall verification section exactly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- paste_hidden.py is fully gated on prefs.plugin_enabled and prefs.link_classes_paste_mode
- Plan 06-04 can safely add its own prefs-driven gates to any remaining modules
- When plugin_enabled is False, all three clipboard functions transparently delegate to Nuke's built-in clipboard behavior

## Self-Check: PASSED

- FOUND: /workspace/paste_hidden.py
- FOUND commit: d76bd05 (feat(06-03): gate clipboard functions on plugin_enabled and link_classes_paste_mode)
- FOUND: `import prefs` at line 24
- FOUND: `if not prefs.plugin_enabled` at lines 35, 106, 135 (copy_hidden, cut_hidden, paste_hidden)
- FOUND: `prefs.link_classes_paste_mode == 'passthrough'` at line 48 (copy_hidden Path A)
- FOUND: copy_old at line 260, cut_old at line 264, paste_old at line 271 (all ungated)

---
*Phase: 06-preferences-infrastructure*
*Completed: 2026-03-11*
