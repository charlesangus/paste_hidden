---
phase: 07-color-picker-redesign-and-preferences-panel
plan: "01"
subsystem: color-picker
tags: [colors, qt, dialog, swatch, staging, picker]
dependency_graph:
  requires: []
  provides:
    - "ColorPaletteDialog click-to-select behavior (PICKER-01/02)"
    - "ColorPaletteDialog group reordering (PICKER-04)"
    - "ColorPaletteDialog custom color staging via chosen_custom_colors() (PICKER-05)"
  affects:
    - "anchor.py callers of ColorPaletteDialog (must read chosen_custom_colors() on accept)"
tech_stack:
  added: []
  patterns:
    - "AST method extraction for unit-testing Qt-stubbed class methods"
    - "Dialog-local staging list returned via accessor on accept"
key_files:
  created: []
  modified:
    - "colors.py"
    - "tests/test_anchor_color_system.py"
decisions:
  - "Used AST source extraction (_extract_method_from_source) to test actual colors.py method implementations despite ColorPaletteDialog being a MagicMock in the test environment"
  - "_custom_group_next_col/row initialized to (0,0) and only updated via identity check (color_group is user_palette_colors) to correctly handle empty custom colors group"
metrics:
  duration: "8 minutes"
  completed_date: "2026-03-12"
  tasks_completed: 2
  files_modified: 2
---

# Phase 7 Plan 01: ColorPaletteDialog Redesign Summary

**One-liner:** Click-to-select ColorPaletteDialog with OK button, custom→backdrop→Nuke group ordering, and custom color staging via `chosen_custom_colors()`.

## What Was Built

Modified `ColorPaletteDialog` in `colors.py` to implement PICKER-01 through PICKER-05:

### Task 1: Click-to-select, OK button, group reordering (PICKER-01/02/04)

- **`_on_swatch_clicked`**: Removed `self.accept()` call; now updates `self._selected_color` and calls `self._refresh_swatch_borders()`.
- **`_refresh_swatch_borders`** (new method): Iterates `self._swatch_cells`; selected swatch gets `border: 2px solid white`, others get `border: 1px solid #555`. Uses `is not None` guard to correctly handle color int `0` (black).
- **Group ordering**: Reversed `all_color_groups` to `[user_palette_colors, backdrop_colors, nuke_pref_colors]`. Existing blank-row gap logic (`if group_col > 0: grid_row += 1`) preserved.
- **OK button**: Added `QPushButton("OK")` with `setAutoDefault(False)`, `NoFocus`, wired to `self.accept()`.
- **`setAutoDefault(False)`**: Applied to OK, Cancel, "Custom Color...", and all swatch buttons.
- **`keyPressEvent`**: Moved Enter/Return block OUTSIDE `if self._hint_mode:` guard so Enter confirms selection in both normal and hint modes.
- **`_staged_custom_colors`**: Initialized in `__init__` as `list(self._custom_colors)` (copy).

### Task 2: Custom Color staging (PICKER-05)

- **`_on_custom_color_clicked`**: Appends result to `self._staged_custom_colors`, sets `self._selected_color = result`, calls `self._append_swatch_to_custom_group(result)`, calls `self._refresh_swatch_borders()`. No `self.accept()`. Returns early if `result == 0`.
- **`_append_swatch_to_custom_group`** (new method): Creates a swatch button at `(self._custom_group_next_row, self._custom_group_next_col)` in the grid. Appends to `self._swatch_cells` and `self._cell_map`. Advances column counter, wrapping at `_SWATCHES_PER_ROW`.
- **`chosen_custom_colors`** (new public accessor): Returns `list(self._staged_custom_colors)` — a copy.
- **Custom group tracker**: Initialized to `(0, 0)` before the group loop. Updated via identity check (`color_group is user_palette_colors`) only when the actual custom colors group is processed. This correctly places dynamically appended swatches even when the initial custom colors list is empty.

## Tests Written

26 total tests pass in `tests/test_anchor_color_system.py`:

**New PICKER-01/02 tests (7):**
- `TestColorPaletteDialogClickToSelect` (4 tests): `_on_swatch_clicked` updates `_selected_color`, does not call `accept()`, calls `_refresh_swatch_borders()`, handles color 0 correctly.
- `TestColorPaletteDialogRefreshSwatchBorders` (3 tests): white border for selected, default for non-selected, color 0 identified as selected.

**New PICKER-05 tests (7):**
- `TestColorPaletteDialogCustomColorStaging` (7 tests): staged list is a copy, `_on_custom_color_clicked` appends without closing, `getColor() == 0` is no-op, `chosen_custom_colors()` returns staged list and returns a copy.

**Test infrastructure decision:** `ColorPaletteDialog` is a `MagicMock` in the test environment (Qt stubbed as MagicMock). Tests use `_extract_method_from_source()` (AST-based) to extract actual method definitions from `colors.py` source and run them against a plain Python `_PickerTestHarness` object with the same instance attributes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Custom group position tracker used wrong strategy**
- **Found during:** Task 2 implementation review
- **Issue:** Original `is_first_group` boolean tracked first non-empty group, but if `user_palette_colors` is empty (filtered out), the tracker would incorrectly point to the backdrop colors group's next slot instead of `(0, 0)`.
- **Fix:** Pre-initialize `_custom_group_next_col/row` to `(0, 0)` before the loop. Use identity check (`color_group is user_palette_colors`) to update only when the actual custom colors group is processed.
- **Files modified:** `colors.py`
- **Commit:** 362b604

## Self-Check: PASSED

Files verified:
- `/workspace/colors.py` — contains `_refresh_swatch_borders`, `_append_swatch_to_custom_group`, `chosen_custom_colors`, `_staged_custom_colors`, OK button, reversed group order, Enter key outside hint mode guard
- `/workspace/tests/test_anchor_color_system.py` — 26 tests all passing

Commits verified:
- d263228 (test RED phase Task 1)
- 90d386f (feat Task 1 implementation)
- 35d43a2 (test Task 2)
- 362b604 (feat Task 2 + tracker fix)
