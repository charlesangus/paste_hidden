---
phase: 03-anchor-color-system
plan: 01
subsystem: anchor-color
tags: [tdd, colors, qt-widget, palette, color-propagation, constants]
dependency_graph:
  requires: []
  provides:
    - colors.ColorPaletteDialog
    - colors.load_user_palette
    - colors.save_user_palette
    - colors._get_nuke_pref_colors
    - colors._get_script_backdrop_colors
    - anchor.propagate_anchor_color
    - anchor.add_set_color_anchor_knob
    - anchor.set_anchor_color
    - anchor.create_anchor_named (color param)
    - anchor.rename_anchor_to (color param)
    - constants.ANCHOR_SET_COLOR_KNOB_NAME
    - constants.USER_PALETTE_PATH
  affects:
    - anchor.AnchorPlugin.get_color (COLOR-01 fixed)
    - anchor.AnchorNavigatePlugin.get_color (COLOR-01 fixed)
tech_stack:
  added: []
  patterns:
    - PySide2/PySide6 Qt guard replicated in colors.py
    - PyScript_Knob button pattern for add_set_color_anchor_knob
    - TDD: red-green cycle with unittest discover
key_files:
  created:
    - colors.py
    - tests/test_anchor_color_system.py
  modified:
    - constants.py
    - anchor.py
decisions:
  - "ColorPaletteDialog defined as None when Qt unavailable — callers guard with 'if ColorPaletteDialog is None: return'"
  - "propagate_anchor_color() returns early for Dot anchors — Dot colors are system-managed"
  - "create_anchor_named() color=None falls back to find_anchor_color() for backward compatibility"
  - "rename_anchor_to() color=None skips propagation — only explicit color triggers propagate_anchor_color()"
  - "Test stub ordering fix: _ensure_qt_stubs_support_mock_attributes() patches stubs back to MagicMock before reload when discover overwrites them"
metrics:
  duration_seconds: 490
  completed_date: "2026-03-08"
  tasks_completed: 2
  files_changed: 4
---

# Phase 03 Plan 01: Color System Foundation Summary

**One-liner:** ColorPaletteDialog Qt widget in new colors.py, ANCHOR_SET_COLOR_KNOB_NAME/USER_PALETTE_PATH constants added, and COLOR-01 one-liner fixed (both get_color methods read tile_color.value() directly).

## What Was Built

### colors.py (new module)
- `ColorPaletteDialog(QtWidgets.QDialog)`: color swatch grid dialog; supports `show_name_field`, `initial_color`, hint-mode keyboard navigation (Tab→column key→row key), "Custom Color..." button calling `nuke.getColor()`, Cancel button
- `load_user_palette()`: reads `~/.nuke/paste_hidden_user_palette.json`; returns `[]` on any error
- `save_user_palette(colors)`: writes to the same path with `os.makedirs(..., exist_ok=True)`
- `_get_nuke_pref_colors()`: reads `NodeColourChoice*` knobs from `nuke.toNode("preferences")`
- `_get_script_backdrop_colors()`: collects unique `tile_color` values from `nuke.allNodes('BackdropNode')`
- Qt guard: identical to anchor.py's pattern; `ColorPaletteDialog = None` when Qt unavailable

### constants.py (modified)
- Added `import os`
- Added `ANCHOR_SET_COLOR_KNOB_NAME = "set_anchor_color"`
- Added `USER_PALETTE_PATH = os.path.expanduser('~/.nuke/paste_hidden_user_palette.json')`

### anchor.py (modified)
- **COLOR-01 fix:** Both `AnchorPlugin.get_color()` and `AnchorNavigatePlugin.get_color()` now call `menuobj['tile_color'].value()` instead of `find_anchor_color(menuobj)`
- `add_set_color_anchor_knob(node)`: adds `set_anchor_color` PyScript_Knob; skips Dot nodes; idempotent
- `propagate_anchor_color(anchor_node, color_int)`: sets anchor tile_color and all referencing Link tile_colors; returns early for Dot anchors
- `set_anchor_color(anchor_node)`: dialog entry point for the "Set Color" PyScript_Knob
- `create_anchor_named(name, input_node=None, color=None)`: new `color` param; uses `find_anchor_color()` fallback when `color=None`; calls `add_set_color_anchor_knob()` at creation
- `rename_anchor_to(anchor_node, name, color=None)`: new `color` param; calls `propagate_anchor_color()` when provided

### tests/test_anchor_color_system.py (new)
15 unit tests covering COLOR-01 through COLOR-05 and palette round-trip logic.

## Decisions Made

1. `ColorPaletteDialog = None` when Qt unavailable — identical guard pattern to `anchor.py`
2. `propagate_anchor_color()` returns early for Dot anchors — Dot colors are system-managed (ANCHOR_DEFAULT_COLOR / LOCAL_DOT_COLOR)
3. `create_anchor_named(color=None)` falls back to `find_anchor_color()` — preserves backward compatibility for `create_anchor_silent()`
4. `rename_anchor_to(color=None)` skips propagation — explicit color opt-in only
5. Test stub ordering: `_ensure_qt_stubs_support_mock_attributes()` in setUp patches Qt module stubs back to MagicMock when `discover` loads test files alphabetically and `test_cross_script_paste.py` overwrites our MagicMock stubs with `types.ModuleType` stubs

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test stub ordering issue in discover mode**
- **Found during:** Task 2 (GREEN phase verification)
- **Issue:** `python3 -m unittest discover -s tests -v` loads test files alphabetically. `test_cross_script_paste.py` overwrites `sys.modules['PySide6.QtGui']` with a `types.ModuleType` stub (no auto-attribute creation). This caused `anchor.QtGui.QColor` to raise `AttributeError` when COLOR-01 tests reloaded anchor.py.
- **Fix:** Added `_ensure_qt_stubs_support_mock_attributes()` helper that patches `PySide6.Qt*` stubs back to `MagicMock` and sets `nuke.NUKE_VERSION_MAJOR = 16` if missing, called in `setUp()` of affected test classes before `importlib.reload(anchor_mod)`.
- **Files modified:** `tests/test_anchor_color_system.py`
- **Commit:** 50e3253

## Test Results

```
Ran 58 tests in 0.083s
OK
```

All 15 new tests pass. No regressions in the 43 pre-existing tests.

## Self-Check

- [x] `colors.py` exists
- [x] `tests/test_anchor_color_system.py` exists
- [x] `constants.py` has ANCHOR_SET_COLOR_KNOB_NAME and USER_PALETTE_PATH
- [x] Both `get_color()` methods use `tile_color.value()` (lines 403 and 507 in anchor.py)
- [x] Commits 67dab09 and 50e3253 present
- [x] Full suite: 58 tests, OK

## Self-Check: PASSED
