---
phase: 06-preferences-infrastructure
plan: 01
subsystem: infra
tags: [json, preferences, singleton, persistence, python]

# Dependency graph
requires: []
provides:
  - prefs.py singleton module with plugin_enabled, link_classes_paste_mode, custom_colors module-level vars
  - PREFS_PATH constant in constants.py
  - _load() auto-called at import time, reads ~/.nuke/paste_hidden_prefs.json
  - save() writes all three preference keys as JSON
  - _migrate_from_old_palette() reads legacy palette colors when prefs file absent
affects:
  - 06-02
  - 06-03
  - 06-04
  - 07-prefs-dialog

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Module-level singleton: module-level variables overwritten by _load() at import time, no class needed
    - Constructor injection: downstream consumers (e.g. ColorPaletteDialog) receive custom_colors via argument, never import prefs directly — prevents circular import
    - Per-key validation: each loaded value checked for type before assignment so corrupt values do not poison valid ones

key-files:
  created:
    - prefs.py
  modified:
    - constants.py

key-decisions:
  - "PREFS_PATH placed immediately after USER_PALETTE_PATH in constants.py for colocation"
  - "Migration function reads only, never writes old palette file — one-way migration on first save"
  - "save() is not called automatically — called only by Phase 7 PrefsDialog on accept"

patterns-established:
  - "Silent fallback: all disk IO in _load() wrapped in broad except; defaults survive any failure"
  - "Descriptive variable names used throughout (color_value, file_handle, data — not c, f, d)"

requirements-completed: [PREFS-01, PREFS-02]

# Metrics
duration: 2min
completed: 2026-03-11
---

# Phase 6 Plan 01: Preferences Infrastructure — prefs.py singleton and PREFS_PATH constant

**JSON-backed preferences singleton loading plugin_enabled, link_classes_paste_mode, and custom_colors at Nuke startup, with silent fallback and one-way migration from the legacy palette file**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-11T12:21:18Z
- **Completed:** 2026-03-11T12:23:14Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added PREFS_PATH to constants.py pointing to `~/.nuke/paste_hidden_prefs.json`
- Created prefs.py with module-level singleton (plugin_enabled, link_classes_paste_mode, custom_colors) loaded automatically at import time
- Implemented save() to persist all three keys as JSON, creating ~/.nuke/ directory as needed
- Implemented _migrate_from_old_palette() to populate custom_colors from legacy palette file when new prefs file is absent

## Task Commits

Each task was committed atomically:

1. **Task 1: Add PREFS_PATH to constants.py** - `408443f` (feat)
2. **Task 2: Create prefs.py singleton module** - `f945f98` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `constants.py` - Added PREFS_PATH = os.path.expanduser('~/.nuke/paste_hidden_prefs.json') after USER_PALETTE_PATH
- `prefs.py` - New module-level preferences singleton with _load(), _migrate_from_old_palette(), save()

## Decisions Made

- PREFS_PATH placed directly after USER_PALETTE_PATH in constants.py for logical colocation of related path constants
- Migration is read-only from the old palette file — new prefs are written only on an explicit save() call from Phase 7
- save() excluded from being called within this module to maintain Phase 7 ownership of persistence lifecycle

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- prefs.py is ready for Plans 02-04 to import (`import prefs; prefs.plugin_enabled`, etc.)
- No circular import risk: colors.py does not import prefs; downstream gating modules will import prefs directly
- PREFS_PATH and USER_PALETTE_PATH both available from constants for any module that needs path references

## Self-Check: PASSED

- FOUND: /workspace/prefs.py
- FOUND: /workspace/constants.py
- FOUND: /workspace/.planning/phases/06-preferences-infrastructure/06-01-SUMMARY.md
- FOUND commit: 408443f (feat(06-01): add PREFS_PATH constant to constants.py)
- FOUND commit: f945f98 (feat(06-01): create prefs.py preferences singleton module)

---
*Phase: 06-preferences-infrastructure*
*Completed: 2026-03-11*
