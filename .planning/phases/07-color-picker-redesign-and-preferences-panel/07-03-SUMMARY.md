---
phase: 07-color-picker-redesign-and-preferences-panel
plan: "03"
subsystem: menu-integration-and-uat
tags: [menu, uat, bugfix, colors, prefs, qt, dialog, persistence]
dependency_graph:
  requires:
    - "07-02 (PrefsDialog)"
    - "07-01 (ColorPaletteDialog)"
  provides:
    - "Preferences... menu entry in Anchors menu (PANEL-01)"
    - "Full Phase 7 feature set verified end-to-end via UAT"
  affects:
    - "anchor.py (custom color persistence from ColorPaletteDialog callers)"
    - "colors.py (PrefsDialog crash fix, highlight color, group labels)"
tech_stack:
  added: []
  patterns:
    - "QPalette.Highlight for theme-aware swatch selection indicator"
    - "AST line-number comparison for initialization-order regression tests"
    - "_persist_custom_colors_from_dialog helper consolidates caller-side save logic"
key_files:
  created: []
  modified:
    - "menu.py (Task 1 — Preferences... command)"
    - "colors.py (UAT fixes — PrefsDialog crash, highlight color, group labels)"
    - "anchor.py (UAT fix — custom color persistence)"
    - "tests/test_anchor_color_system.py (updated + new regression tests)"
decisions:
  - "QPalette.Highlight used for swatch selection border so it matches the user's Qt theme rather than hardcoded white"
  - "_refresh_swatch_borders() called at end of _build_ui to apply palette-based pre-highlight — build-time stylesheet is default, corrected after construction"
  - "Group labels (Custom Colors / Backdrop Colors / Nuke Defaults) added as QLabel rows spanning full grid width via addWidget(label, row, 0, 1, _SWATCHES_PER_ROW)"
  - "Add/Edit/Remove buttons created before _populate_swatch_grid() call so _update_edit_remove_buttons() never sees an AttributeError on _edit_button"
  - "_persist_custom_colors_from_dialog() extracted as a module-level helper in anchor.py to consolidate persistence logic across three ColorPaletteDialog call sites"
metrics:
  duration: "35 minutes"
  completed_date: "2026-03-12"
  tasks_completed: 2
  files_modified: 4
---

# Phase 7 Plan 03: Preferences Menu Entry and Full Phase 7 UAT Summary

**One-liner:** Preferences... wired to Anchors menu as ungated command; five UAT bugs fixed — PrefsDialog crash, QPalette highlight color, group labels, custom color pre-highlight, and caller-side custom color persistence.

## What Was Built

### Task 1: Add Preferences... command to Anchors menu (committed 2bb07c9)

- Added `addSeparator()` and `addCommand("Preferences...", ...)` to `menu.py` after the always-active Copy(old)/Cut(old)/Paste(old) commands
- Used plain `addCommand()` (not `_add_gated_command()`) to keep item active when `plugin_enabled` is False

### Task 2 (UAT Fix Cycle): Five bugs discovered during UAT and fixed

**Fix 1 — PrefsDialog crash (AttributeError on _edit_button):**
Reordered `_build_ui` in `PrefsDialog` so Add/Edit/Remove buttons are created **before** `_populate_swatch_grid()` is called. `_populate_swatch_grid()` calls `_update_edit_remove_buttons()` which references `self._edit_button` — this reference was failing because the button was created after the populate call.

**Fix 2 — Highlight color (QPalette instead of hardcoded white):**
Added `_highlight_color_name()` helper to `ColorPaletteDialog` that returns `self.palette().color(QtGui.QPalette.Highlight).name()`. All `border: 2px solid white` stylesheet strings in `_refresh_swatch_borders()` replaced with `border: 2px solid {highlight_color}`.

**Fix 3 — Custom colors pre-highlight on dialog reopen:**
Removed the build-time inline pre-highlight (which applied the old hardcoded white) and replaced with a call to `self._refresh_swatch_borders()` at the end of `_build_ui`. This ensures the pre-highlight uses the palette color and covers all swatch groups including custom colors.

**Fix 4 — Custom colors section display:**
Added group section labels as `QLabel` rows inside the swatch `QGridLayout`, spanning all 8 columns (`addWidget(label, grid_row, 0, 1, _SWATCHES_PER_ROW)`). Labels: "Custom Colors", "Backdrop Colors", "Nuke Defaults". Each label is inserted on its own row before the group's swatches, making the sections visually distinct.

**Fix 5 — Custom colors not persisting across sessions:**
Added `_persist_custom_colors_from_dialog(dialog)` module-level helper in `anchor.py`. Reads `dialog.chosen_custom_colors()`, compares to `prefs.custom_colors`, and calls `prefs.save()` only when they differ. Called at all three `ColorPaletteDialog` accept sites: `set_anchor_color`, `rename_anchor`, `create_anchor`.

## Tests Written

32 total tests pass (was 26 before UAT fixes; 6 new tests added):

**Updated tests (2):**
- `test_refresh_swatch_borders_applies_highlight_border_to_selected`: updated assertion from `border: 2px solid white` to use `_PickerTestHarness.HARNESS_HIGHLIGHT_COLOR` sentinel — verifies palette-based color is used
- `test_refresh_swatch_borders_handles_zero_selected_color`: same assertion update

**`_PickerTestHarness` update:**
- Added `_highlight_color_name()` method returning `HARNESS_HIGHLIGHT_COLOR = "#4a90d9"` sentinel so the extracted `_refresh_swatch_borders` method works in offline tests

**New tests (6):**
- `TestPrefsDialogButtonsCreatedBeforePopulate.test_update_edit_remove_buttons_references_edit_and_remove_button`: verifies method body references the right attributes
- `TestPrefsDialogButtonsCreatedBeforePopulate.test_build_ui_source_order_buttons_before_populate`: AST line-number comparison ensures `self._edit_button` assignment precedes `self._populate_swatch_grid()` call
- `TestColorPaletteDialogGroupLabels.test_build_ui_source_adds_group_labels_via_qlabel`: verifies `QLabel` is called in `_build_ui`
- `TestColorPaletteDialogGroupLabels.test_group_label_texts_in_source`: verifies "Custom Colors", "Backdrop Colors", "Nuke Defaults" strings present
- `TestPersistCustomColorsFromDialog.test_persist_saves_custom_colors_when_staged_differs_from_prefs`: `prefs.save()` called once when staged differs
- `TestPersistCustomColorsFromDialog.test_persist_skips_save_when_staged_matches_prefs`: `prefs.save()` NOT called when unchanged

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] PrefsDialog._build_ui initialization order caused AttributeError**
- **Found during:** Task 2 UAT (UAT item 5 — hard blocker)
- **Issue:** `_update_edit_remove_buttons()` referenced `self._edit_button` inside `_populate_swatch_grid()`, but `_edit_button` was assigned after the `_populate_swatch_grid()` call in `_build_ui`. Opening `Preferences...` crashed unconditionally.
- **Fix:** Moved button creation (Add/Edit/Remove) before the `_populate_swatch_grid()` call.
- **Files modified:** `colors.py`
- **Commit:** 48e8c07

**2. [Rule 1 - Bug] Hardcoded `border: 2px solid white` ignored Qt palette Highlight color**
- **Found during:** Task 2 UAT (UAT item 1)
- **Issue:** Selected swatch border used hardcoded white instead of the widget's QPalette Highlight color.
- **Fix:** Added `_highlight_color_name()` helper; `_refresh_swatch_borders()` now uses it.
- **Files modified:** `colors.py`
- **Commit:** 48e8c07

**3. [Rule 1 - Bug] Custom colors pre-highlight used build-time hardcoded white**
- **Found during:** Task 2 UAT (UAT item 2)
- **Issue:** Pre-highlight was applied inline during grid construction with hardcoded white. On reopen, custom colors were not highlighted because the new palette-based highlight was only applied via `_refresh_swatch_borders()` on click, not on open.
- **Fix:** Removed build-time inline highlight; added `self._refresh_swatch_borders()` call at end of `_build_ui`.
- **Files modified:** `colors.py`
- **Commit:** 48e8c07

**4. [Rule 1 - Bug] Custom colors group had no visual separator from other swatch groups**
- **Found during:** Task 2 UAT (UAT item 3 — display)
- **Issue:** All swatch groups were rendered as raw color swatches with only a blank row gap between them, making "Custom Colors" appear mixed with backdrop and Nuke colors.
- **Fix:** Added `QLabel` group headers ("Custom Colors", "Backdrop Colors", "Nuke Defaults") as full-width label rows above each group.
- **Files modified:** `colors.py`
- **Commit:** 48e8c07

**5. [Rule 2 - Missing critical functionality] Custom colors not persisted after ColorPaletteDialog accept**
- **Found during:** Task 2 UAT (UAT item 3 — persistence)
- **Issue:** None of the three `ColorPaletteDialog` call sites in `anchor.py` called `dialog.chosen_custom_colors()` and saved to prefs. Colors added via "Custom Color..." were discarded on dialog close.
- **Fix:** Added `_persist_custom_colors_from_dialog()` helper; called at all three accept sites.
- **Files modified:** `anchor.py`
- **Commit:** ad06178

## Self-Check: PASSED

Files verified:
- `/workspace/colors.py` — contains `_highlight_color_name`, `_refresh_swatch_borders` uses it, buttons created before `_populate_swatch_grid`, group labels present
- `/workspace/anchor.py` — contains `_persist_custom_colors_from_dialog`, called from `set_anchor_color`, `rename_anchor`, `create_anchor`
- `/workspace/tests/test_anchor_color_system.py` — 32 tests all passing

Commits verified:
- 2bb07c9 (feat Task 1 — Preferences... menu command)
- 48e8c07 (fix — PrefsDialog crash, highlight color, group labels)
- ad06178 (fix — custom color persistence in anchor.py)
- 1b277da (test — regression tests for all UAT fixes)
