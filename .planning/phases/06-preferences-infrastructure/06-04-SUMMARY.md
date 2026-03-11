---
phase: 06-preferences-infrastructure
plan: "04"
subsystem: plugin
tags: [nuke, prefs, menu, plugin_enabled, custom_colors, ColorPaletteDialog]

# Dependency graph
requires:
  - phase: 06-01
    provides: prefs.py singleton with plugin_enabled and custom_colors attributes
  - phase: 06-02
    provides: ColorPaletteDialog accepting custom_colors constructor argument
  - phase: 06-03
    provides: plugin_enabled gates on clipboard functions in paste_hidden.py

provides:
  - plugin_enabled early-return gates on all 6 anchor public entry points in anchor.py
  - plugin_enabled early-return gates on all 3 label public entry points in labels.py
  - custom_colors=prefs.custom_colors injection at all 3 ColorPaletteDialog call sites in anchor.py
  - _gated_menu_items list and set_anchors_menu_enabled() function in menu.py
  - Startup state application: set_anchors_menu_enabled(prefs.plugin_enabled)

affects:
  - 07-preferences-ui (Phase 7 calls set_anchors_menu_enabled after user toggles plugin_enabled)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Early-return gate pattern: if not prefs.plugin_enabled: return as first statement in each public entry point"
    - "Gated menu tracking: _add_gated_command() helper registers and tracks item references for enable/disable"
    - "hasattr guard for setEnabled: hasattr(menu_item, 'setEnabled') for Nuke version compatibility"

key-files:
  created: []
  modified:
    - anchor.py
    - labels.py
    - menu.py

key-decisions:
  - "set_anchors_menu_enabled() uses hasattr guard for setEnabled to ensure Nuke 13+ compatibility without breaking older versions"
  - "Startup call set_anchors_menu_enabled(prefs.plugin_enabled) at bottom of menu.py applies correct initial state when plugin loads with plugin_enabled=False"
  - "copy_old/cut_old/paste_old excluded from _gated_menu_items — always active as explicit fallback commands per plan specification"

patterns-established:
  - "Plugin gate pattern: import prefs at module level, if not prefs.plugin_enabled: return as first statement in each gated public entry point"
  - "Menu gating pattern: store addCommand return values in _gated_menu_items list, toggle via set_anchors_menu_enabled()"

requirements-completed:
  - PREFS-03

# Metrics
duration: 2min
completed: "2026-03-11"
---

# Phase 6 Plan 04: Entry Point Gates and Menu Gating Infrastructure Summary

**plugin_enabled gates on all 6 anchor and 3 label entry points; ColorPaletteDialog custom_colors injection at 3 call sites; menu.py _gated_menu_items + set_anchors_menu_enabled() for Phase 7 toggle support**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-11T12:29:16Z
- **Completed:** 2026-03-11T12:32:01Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `import prefs` and 6 `if not prefs.plugin_enabled: return` guards to anchor.py public entry points (create_anchor, rename_selected_anchor, anchor_shortcut, select_anchor_and_create, select_anchor_and_navigate, navigate_back)
- Injected `custom_colors=prefs.custom_colors` at all 3 ColorPaletteDialog call sites in anchor.py (set_anchor_color, rename_anchor, create_anchor)
- Added `import prefs` and 3 `if not prefs.plugin_enabled: return` guards to labels.py public entry points (create_large_label, create_medium_label, append_to_label)
- Rewrote menu.py with `_gated_menu_items` list, `_add_gated_command()` helper, `set_anchors_menu_enabled()` function with hasattr guard, and startup state application

## Task Commits

Each task was committed atomically:

1. **Task 1: Gate anchor and label entry points; inject custom_colors into ColorPaletteDialog calls** - `95654e2` (feat)
2. **Task 2: Add gated menu item infrastructure to menu.py** - `e09d0e8` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `anchor.py` - Added prefs import, 6 plugin_enabled gates, 3 custom_colors injections at ColorPaletteDialog call sites
- `labels.py` - Added prefs import, 3 plugin_enabled gates on all public label entry points
- `menu.py` - Added prefs import, _gated_menu_items list, _add_gated_command helper, set_anchors_menu_enabled() with hasattr guard, startup state application

## Decisions Made

- Used `hasattr(menu_item, 'setEnabled')` guard in set_anchors_menu_enabled() for Nuke 13+ compatibility without breaking older Nuke versions
- set_anchors_menu_enabled(prefs.plugin_enabled) call at bottom of menu.py applies correct initial disabled state when the plugin loads with plugin_enabled=False
- copy_old/cut_old/paste_old kept ungated per plan specification — these are explicit fallback commands that must remain always active

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The plan's verification scripts used `inspect.getsource()` which requires importing the modules. Since nuke is not available in the test environment without stubs, the verification was adapted to read the source files directly via file I/O instead of via module import. The same assertions were verified on the source text.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- anchor.py, labels.py, and menu.py all import prefs and are fully gated on plugin_enabled
- Phase 7 (preferences-ui) can call `menu.set_anchors_menu_enabled()` after the user toggles the plugin_enabled preference in the PrefsDialog
- The Preferences menu item Phase 7 adds to anchors_menu will be automatically excluded from _gated_menu_items since it will be added with a direct addCommand call outside _add_gated_command

---
*Phase: 06-preferences-infrastructure*
*Completed: 2026-03-11*

## Self-Check: PASSED

- anchor.py: FOUND
- labels.py: FOUND
- menu.py: FOUND
- 06-04-SUMMARY.md: FOUND
- Commit 95654e2 (Task 1): FOUND
- Commit e09d0e8 (Task 2): FOUND
