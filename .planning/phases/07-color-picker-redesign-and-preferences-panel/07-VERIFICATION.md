---
phase: 07-color-picker-redesign-and-preferences-panel
verified: 2026-03-12T00:00:00Z
status: human_needed
score: 12/12 must-haves verified
human_verification:
  - test: "Open the color picker for an anchor (create one or use Rename Anchor). Click a swatch. Confirm the dialog does NOT close and the swatch gets a border highlight. Confirm clicking OK then closes the dialog."
    expected: "Swatch shows a colored border on click; dialog stays open until OK or Enter is pressed."
    why_human: "Qt visual behavior and dialog lifecycle cannot be tested without a running Nuke session."
  - test: "Open the color picker with an anchor that has an existing color. Confirm the previously set color has a border highlight immediately on open."
    expected: "initial_color is pre-highlighted on dialog open."
    why_human: "Requires running Nuke with a real Qt palette — cannot be verified from source alone."
  - test: "In the color picker, click Custom Color..., pick a color. Confirm a new swatch appears and is auto-selected. Then click Cancel. Reopen — confirm the new color did NOT persist."
    expected: "Staged color is discarded on Cancel; only persists if OK is pressed."
    why_human: "Requires interactive session with nuke.getColor() and dialog lifecycle."
  - test: "Open Anchors menu. Confirm Preferences... item is visible, separated from Copy(old)/Cut(old)/Paste(old) by a separator, and is clickable when plugin is disabled."
    expected: "Preferences... always active regardless of plugin_enabled state."
    why_human: "Nuke menu rendering and active/disabled states require a live Nuke session."
  - test: "Open Preferences..., toggle Enable paste_hidden plugin OFF, click OK. Restart Nuke. Open Preferences... again — confirm toggle shows unchecked."
    expected: "plugin_enabled = False persists across Nuke restarts."
    why_human: "Persistence across sessions requires actual disk writes and Nuke restart."
  - test: "In Preferences..., add a custom color, edit it, remove it. Confirm Edit and Remove are greyed until a swatch is selected."
    expected: "Add/Edit/Remove all function correctly; Edit/Remove gated on selection."
    why_human: "Requires interactive nuke.getColor() calls in a Qt event loop."
  - test: "Click Cancel in Preferences... after making changes. Confirm prefs module variables are unchanged."
    expected: "Cancel leaves prefs.plugin_enabled, prefs.link_classes_paste_mode, prefs.custom_colors all unchanged."
    why_human: "Requires verifying module state after dialog cancel in a live session."
---

# Phase 7: Color Picker Redesign and Preferences Panel Verification Report

**Phase Goal:** Redesign the color picker dialog (ColorPaletteDialog) for better UX, and build a Preferences dialog (PrefsDialog) for managing plugin settings. Wire Preferences into the Anchors menu.
**Verified:** 2026-03-12
**Status:** human_needed (all automated checks pass; 7 interactive flows require Nuke UAT)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Clicking a swatch highlights it without closing the dialog | VERIFIED | `_on_swatch_clicked` (colors.py:243) only sets `_selected_color` and calls `_refresh_swatch_borders()` — no `accept()` call |
| 2 | Pressing Enter or OK confirms selection and closes | VERIFIED | Enter block at line 311 is outside `if self._hint_mode:` guard (line 319); OK button wired to `self.accept()` at line 229 |
| 3 | initial_color is pre-highlighted on open | VERIFIED | `_refresh_swatch_borders()` called at end of `_build_ui` (line 241); uses `self._selected_color` which is set to `initial_color` in `__init__` |
| 4 | Swatch groups ordered: custom → backdrop → Nuke defaults | VERIFIED | Line 145-148: `[user_palette_colors, backdrop_colors, nuke_pref_colors]` |
| 5 | Blank row gap separates non-empty groups; empty groups omitted | VERIFIED | `if group` filter at line 147 omits empty; `if group_col > 0: grid_row += 1` at line 215 adds gap |
| 6 | Custom Color... stages in memory, appends swatch, dialog stays open | VERIFIED | `_on_custom_color_clicked` (line 279) appends to `_staged_custom_colors`, calls `_append_swatch_to_custom_group()`, no `accept()` call; returns early on `result == 0` |
| 7 | Cancel discards staged colors; caller only receives on accept | VERIFIED | `chosen_custom_colors()` returns `_staged_custom_colors` — caller is only expected to call this when `dialog.result() == Accepted`; all three accept sites in anchor.py check this |
| 8 | PrefsDialog opens with checkboxes seeded from prefs | VERIFIED | `__init__` does local `import prefs`; seeds `_local_plugin_enabled`, `_local_link_mode`, `_local_custom_colors` from prefs module |
| 9 | User can toggle plugin enabled/disabled and LINK_CLASSES mode | VERIFIED | `_plugin_checkbox` and `_link_mode_checkbox` both present with `setChecked()` from local copies |
| 10 | OK writes all three prefs values, calls save(), calls set_anchors_menu_enabled() | VERIFIED | `_on_accept` (line 614): flushes all three, calls `prefs_module.save()`, calls `menu_module.set_anchors_menu_enabled()`, then `self.accept()` |
| 11 | Cancel leaves prefs module variables unchanged | VERIFIED | `_button_box.rejected` connected to `self.reject()` (line 508); `_on_accept` (which alone mutates prefs) is only connected to `accepted` signal |
| 12 | Anchors menu contains always-active Preferences... item | VERIFIED | menu.py line 71-75: `addSeparator()` + `addCommand("Preferences...", ...)` using plain `addCommand` (not `_add_gated_command`) |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `colors.py` | ColorPaletteDialog with click-to-select, OK button, reordered groups, custom-color staging | VERIFIED | 631 lines; all methods present; syntax valid |
| `colors.py` | `_refresh_swatch_borders` method | VERIFIED | Line 256; uses `_highlight_color_name()` for palette-aware border color |
| `colors.py` | `chosen_custom_colors()` accessor | VERIFIED | Line 412; returns `list(self._staged_custom_colors)` |
| `colors.py` | `PrefsDialog` class | VERIFIED | Line 425; full implementation present |
| `colors.py` | `PrefsDialog = None` null guard | VERIFIED | Line 68; symmetric with `ColorPaletteDialog = None` on same line |
| `menu.py` | Preferences... command registered on anchors_menu | VERIFIED | Lines 71-75; uses plain `addCommand`, preceded by `addSeparator()` |
| `anchor.py` | `_persist_custom_colors_from_dialog` helper | VERIFIED | Line 122; called at all three `ColorPaletteDialog` accept sites (set_anchor_color, rename_anchor, create_anchor) |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `ColorPaletteDialog._on_swatch_clicked` | `self._selected_color` + `_refresh_swatch_borders()` | removes `accept()` call | WIRED | Line 243-245: only sets `_selected_color` and calls `_refresh_swatch_borders()` |
| `ColorPaletteDialog` OK button | `self.accept()` | `QPushButton.clicked` | WIRED | Line 226-229: `ok_button.setAutoDefault(False)`, wired to `self.accept` |
| `ColorPaletteDialog._on_custom_color_clicked` | `self._staged_custom_colors` | appends without calling accept | WIRED | Lines 285-288: appends, sets `_selected_color`, calls `_append_swatch_to_custom_group`, then `_refresh_swatch_borders` |
| `PrefsDialog.__init__` | `prefs.plugin_enabled`, `prefs.link_classes_paste_mode`, `prefs.custom_colors` | local `import prefs` inside `__init__` | WIRED | Lines 435-439: local import + seed to `self._local_*` |
| `PrefsDialog._on_accept` | `prefs.save()` and `menu.set_anchors_menu_enabled()` | local imports inside `_on_accept` | WIRED | Lines 616-631: both local imports present; both called before `self.accept()` |
| `PrefsDialog` swatch buttons | `_on_swatch_selected(index)` | clicked signal with captured index | WIRED | Lines 525-527: `lambda checked=False, i=index: self._on_swatch_selected(i)` |
| Anchors menu Preferences... item | `PrefsDialog` in colors.py | `addCommand` callback string | WIRED | Line 74: `"from colors import PrefsDialog; dlg = PrefsDialog(); dlg.exec_()"` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| PANEL-01 | 07-03-PLAN.md | User can open a preferences dialog from the Anchors menu | SATISFIED | menu.py lines 71-75: `addCommand("Preferences...", "from colors import PrefsDialog; dlg = PrefsDialog(); dlg.exec_()")` — NOTE: REQUIREMENTS.md traceability table still shows "Pending" for PANEL-01; this is a documentation staleness issue, not an implementation gap |
| PANEL-02 | 07-02-PLAN.md | User can toggle plugin enabled/disabled; persists | SATISFIED | `_plugin_checkbox` in PrefsDialog; `_on_accept` flushes to `prefs_module.plugin_enabled` and calls `prefs_module.save()` |
| PANEL-03 | 07-02-PLAN.md | User can toggle LINK_CLASSES paste mode; persists | SATISFIED | `_link_mode_checkbox` in PrefsDialog; `_on_accept` flushes to `prefs_module.link_classes_paste_mode` |
| PANEL-04 | 07-02-PLAN.md | User can view saved custom colors in preferences dialog | SATISFIED | `_populate_swatch_grid()` fills grid from `self._local_custom_colors` |
| PANEL-05 | 07-02-PLAN.md | User can add a new custom color via color picker | SATISFIED | `_on_add_color()` calls `nuke.getColor()`, appends to `_local_custom_colors`, calls `_rebuild_swatch_grid()` |
| PANEL-06 | 07-02-PLAN.md | User can remove a custom color | SATISFIED | `_on_remove_color()` deletes from `_local_custom_colors`, calls `_rebuild_swatch_grid()` |
| PANEL-07 | 07-02-PLAN.md | User can edit (replace) an existing custom color | SATISFIED | `_on_edit_color()` calls `nuke.getColor()`, replaces element, calls `_rebuild_swatch_grid()` |
| PICKER-01 | 07-01-PLAN.md | Clicking swatch selects without closing dialog | SATISFIED | `_on_swatch_clicked`: no `accept()` call; only state update |
| PICKER-02 | 07-01-PLAN.md | Enter key or OK button confirms and closes | SATISFIED | OK button wired to `accept()`; Enter block outside hint mode guard |
| PICKER-03 | 07-01-PLAN.md | initial_color pre-highlighted on open | SATISFIED | `_refresh_swatch_borders()` called at end of `_build_ui`; `_selected_color` initialized to `initial_color` |
| PICKER-04 | 07-01-PLAN.md | Group order: custom → backdrop → Nuke defaults | SATISFIED | Line 145-148 confirms order |
| PICKER-05 | 07-01-PLAN.md | Custom colors staged in memory until accept | SATISFIED | `_staged_custom_colors` list; `chosen_custom_colors()` accessor; `_persist_custom_colors_from_dialog()` in anchor.py |

**Documentation gap:** REQUIREMENTS.md line 55 shows `[ ] **PANEL-01**` (checkbox unchecked) and the traceability table at line 118 shows `Pending`. The implementation is complete. REQUIREMENTS.md should be updated to check PANEL-01 and mark it Complete.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_anchor_color_system.py` | 27, 184, 189 | Word "placeholder" | Info | These appear in test infrastructure comments describing Qt stubs — not empty implementations. Not a concern. |

No blockers or warnings found. No empty return stubs, no `return {}` or `return []` without real logic, no `console.log`-only handlers found in production code.

---

### Human Verification Required

The automated checks all pass. Seven interactive flows require testing in a running Nuke session:

#### 1. Color Picker Click-to-Select

**Test:** Open the color picker for an anchor (create one or use Rename Anchor). Click a swatch.
**Expected:** Dialog stays open; clicked swatch gets a colored border. No other swatch is highlighted.
**Why human:** Qt visual behavior and dialog lifecycle require a live Nuke session.

#### 2. Color Picker Initial Highlight

**Test:** Open the color picker for an anchor that has an existing color set.
**Expected:** The previously set color swatch is highlighted with a border immediately on dialog open.
**Why human:** Requires running Nuke with a real Qt palette context.

#### 3. Custom Color Staging and Discard

**Test:** In the color picker, click Custom Color... and pick a color. Confirm a new swatch appears auto-selected. Then click Cancel. Reopen the dialog.
**Expected:** New color is not present on reopen — staged color discarded on Cancel.
**Why human:** Requires interactive nuke.getColor() and dialog lifecycle.

#### 4. Preferences Menu Entry

**Test:** Open Anchors menu. Disable plugin (see step 5). Open Anchors menu again.
**Expected:** Preferences... item is always visible and clickable, separated from Copy(old) group by a separator, active even when gated items are greyed.
**Why human:** Menu active/disabled state requires a live Nuke session.

#### 5. Plugin Toggle Persistence

**Test:** Open Preferences..., toggle Enable paste_hidden plugin OFF, click OK. Restart Nuke. Open Preferences...
**Expected:** Toggle shows unchecked after restart.
**Why human:** Requires actual disk write and Nuke restart.

#### 6. Custom Colors CRUD in PrefsDialog

**Test:** Open Preferences..., click Add → pick a color → confirm it appears in the swatch grid. Select it, click Edit → pick different color → confirm it replaced in-place. Select a swatch, click Remove → confirm it disappears. Open a fresh Preferences... with no swatch selected — confirm Edit and Remove are greyed.
**Expected:** All CRUD operations work; Edit/Remove disabled until selection.
**Why human:** Requires interactive nuke.getColor() calls in a Qt event loop.

#### 7. Cancel Does Not Mutate Prefs

**Test:** Open Preferences..., toggle both checkboxes, add a color. Click Cancel. Open Preferences... again.
**Expected:** All values unchanged — dialog shows the original state.
**Why human:** Requires verifying module state across dialog open/close in a live session.

---

### Automated Test Results

**32 tests, 0 failures** (`python3 -m unittest tests/test_anchor_color_system.py`)

All 32 tests in `tests/test_anchor_color_system.py` pass, covering:
- `TestColorPaletteDialogClickToSelect` (4 tests): `_on_swatch_clicked` contract
- `TestColorPaletteDialogRefreshSwatchBorders` (3 tests): palette-aware highlight border
- `TestColorPaletteDialogCustomColorStaging` (7 tests): staging lifecycle
- `TestColorPaletteDialogGroupLabels` (2 tests): section label presence
- `TestPrefsDialogButtonsCreatedBeforePopulate` (2 tests): initialization order regression
- `TestPersistCustomColorsFromDialog` (2 tests): `_persist_custom_colors_from_dialog` logic
- Additional existing tests for anchor color propagation, knob management (12 tests)

---

### Syntax Verification

All modified files pass AST syntax check:
- `/workspace/colors.py` — OK
- `/workspace/menu.py` — OK
- `/workspace/anchor.py` — OK

---

### Gaps Summary

No gaps blocking goal achievement. All 12 observable truths are verified in code. All 12 requirement IDs (PANEL-01 through PANEL-07, PICKER-01 through PICKER-05) are implemented.

One documentation staleness item: REQUIREMENTS.md has PANEL-01 marked as `[ ]` (not checked) and "Pending" in the traceability table, even though the implementation is complete in menu.py. This should be updated.

All remaining items are interactive UAT flows that require a Nuke session.

---

_Verified: 2026-03-12_
_Verifier: Claude (gsd-verifier)_
