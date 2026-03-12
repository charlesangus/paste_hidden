# Phase 7: Color Picker Redesign and Preferences Panel - Research

**Researched:** 2026-03-11
**Domain:** PySide2/PySide6 Qt dialog design within Nuke; in-process state staging; menu integration
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Color picker: click-to-select behavior**
- Clicking a swatch highlights it (white border) without closing the dialog
- Enter key OR OK button confirms the selection and closes
- OK button sits beside Cancel (not above — horizontal button row)
- Pre-selected `initial_color` opens with white border highlight

**Color picker: "Custom Color..." button**
- Opens `nuke.getColor()` as before; if result is non-zero, the color is staged in memory
- A new swatch is dynamically appended to the custom colors group in the grid
- The new swatch is auto-highlighted (selected); dialog stays open
- User must still press Enter or OK to confirm — Cancel discards the staged color
- Consistent with PICKER-01: clicking never closes, only Enter/OK does

**Color picker: swatch group ordering and separation**
- Order: custom colors → backdrop colors → Nuke defaults (reversed from current)
- Groups separated by a blank row gap (no labels, no separator lines)
- Empty groups are omitted entirely (current `if group` filter preserved)

**Preferences dialog: controls**
- Plugin toggle: `QCheckBox` labeled "Enable paste_hidden plugin"
- LINK_CLASSES mode: `QCheckBox` labeled "Input nodes paste as links"
  - Checked = `create_link` (default), Unchecked = `passthrough`
- Dialog buttons: OK (saves + closes) and Cancel (discards) — horizontal, bottom-right
- On OK: write all three prefs, call `prefs.save()`, call `menu.set_anchors_menu_enabled(prefs.plugin_enabled)`

**Preferences dialog: custom color management**
- Custom colors displayed as a wrapping grid of 24×24 swatch buttons (same style as color picker)
- Swatches wrap to additional rows if needed (no horizontal scroll)
- Click a swatch to select it (white border highlight); nothing selected = Edit/Remove greyed out
- Add button: always active; opens `nuke.getColor()` directly; appends new color to the list
- Edit button: greyed until a swatch is selected; opens `nuke.getColor()`; replaces the selected color in-place
- Remove button: greyed until a swatch is selected; removes selected color; grid refreshes
- Changes are staged in the dialog's local copy of custom_colors; only written to `prefs.custom_colors` on OK

### Claude's Discretion
- Exact swatch button layout within the prefs panel (QGridLayout column count, spacing)
- How the swatch grid in PrefsDialog refreshes after add/remove/edit (rebuild vs dynamic update)
- How the Preferences menu item is added to the Anchors menu (position, separator)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PANEL-01 | User can open a preferences dialog from the Anchors menu | Menu integration pattern in menu.py — ungated addCommand after existing always-active block |
| PANEL-02 | User can toggle the plugin enabled/disabled in the preferences dialog; change persists across sessions | QCheckBox + prefs.save() + set_anchors_menu_enabled() on OK |
| PANEL-03 | User can toggle LINK_CLASSES paste mode; change persists | QCheckBox (checked=create_link) + prefs.save() on OK |
| PANEL-04 | User can view the list of saved custom colors in the preferences dialog | QGridLayout wrapping swatch grid seeded from prefs.custom_colors |
| PANEL-05 | User can add a new custom color via color picker in prefs dialog | Add button → nuke.getColor() → append to local staged list → refresh grid |
| PANEL-06 | User can remove a custom color from the saved list | Remove button (greyed until selection) → splice from local staged list → refresh grid |
| PANEL-07 | User can edit (replace) an existing custom color via color picker | Edit button (greyed until selection) → nuke.getColor() → replace in-place → refresh grid |
| PICKER-01 | Clicking a color swatch selects/highlights it without closing the dialog | Change _on_swatch_clicked to update self._selected_color + update stylesheet only; remove self.accept() |
| PICKER-02 | User confirms selection with Enter key or OK button; dialog closes | Add OK button; extend keyPressEvent Enter handling outside hint mode |
| PICKER-03 | Pre-selected color (initial_color) is visually highlighted when dialog opens | Already implemented in _build_ui; maintained through refactor |
| PICKER-04 | Swatch groups ordered: custom → backdrop → Nuke defaults, with separation | Reorder all_color_groups list; blank row gap between groups |
| PICKER-05 | Custom colors via "Custom Color..." staged in memory; only persisted on accept (not Cancel) | _on_custom_color_clicked appends to self._staged_custom_colors; caller reads via chosen_custom_colors() accessor |
</phase_requirements>

---

## Summary

Phase 7 has two parallel workstreams: (1) redesigning `ColorPaletteDialog` in `colors.py` to use click-to-highlight instead of click-to-close, and (2) creating a new `PrefsDialog` in `colors.py` that manages plugin preferences and custom color CRUD. Both dialogs share the same Qt swatch button idiom and the same PySide2/PySide6 compatibility guard already present in the file.

The critical design insight for this phase is that **all changes are staged in dialog-local state and only flushed to the `prefs` module on `accept()`**. `Cancel` must leave `prefs.*` module-level variables exactly as they were before the dialog opened. This staging discipline is already established in Phase 6 architecture decisions and must be preserved consistently across both dialogs.

The existing `ColorPaletteDialog._on_swatch_clicked` calls `self.accept()` — removing that single call and instead updating `self._selected_color` plus re-styling the active swatch is the core change for PICKER-01/02. The rest of the picker changes (group reordering, blank row gaps, Enter/OK path, "Custom Color..." staging) are additive. The `PrefsDialog` is a new class that reuses the swatch button style from `_color_int_to_rgb()` and the same overall layout pattern.

**Primary recommendation:** Implement `ColorPaletteDialog` redesign first (it's a contained refactor with known blast radius), then build `PrefsDialog` as an entirely new class in the same file, then wire the menu entry last.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide2 / PySide6 | Nuke-bundled | Qt dialogs, widgets, layouts | Nuke's built-in Qt binding; already guarded in colors.py |
| nuke (Python API) | Nuke-bundled | nuke.getColor(), nuke.menu() | Only available way to open native color chooser and register menu items |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| prefs module | project | Persistence singleton | Write to prefs.* only on dialog accept; read at dialog open for initial values |
| menu module | project | Menu registration and enable/disable | Called after PrefsDialog accept to apply plugin_enabled live |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| QGridLayout for swatch grid | QFlowLayout | QGridLayout is standard Qt; QFlowLayout requires third-party or custom implementation — not worth it for fixed column count |
| Rebuild entire swatch grid on change | Partial dynamic update | Rebuilding the grid is simpler, avoids index tracking bugs; performance is irrelevant at palette scale (< 50 swatches) |

---

## Architecture Patterns

### Recommended File Structure

Both new dialogs live in `colors.py` inside the existing `if QtWidgets is None: ... else:` guard:

```
colors.py
├── _get_nuke_pref_colors()          # unchanged
├── _get_script_backdrop_colors()    # unchanged
├── _color_int_to_rgb()              # unchanged — shared by both dialogs
├── if QtWidgets is None:
│     ColorPaletteDialog = None      # unchanged
│     PrefsDialog = None             # NEW — symmetric guard
│   else:
│     _SWATCHES_PER_ROW = 8         # unchanged (used by picker and prefs grid)
│     class ColorPaletteDialog(QDialog)   # MODIFIED
│     class PrefsDialog(QDialog)          # NEW
```

### Pattern 1: Click-to-Select Swatch (PICKER-01)

**What:** Swatch click updates `self._selected_color` and re-applies stylesheet to all swatches. Only the newly selected swatch gets the white border; all others get the default border.
**When to use:** Both `ColorPaletteDialog` and the custom color grid in `PrefsDialog`

```python
# In ColorPaletteDialog
def _on_swatch_clicked(self, color_int):
    self._selected_color = color_int
    self._refresh_swatch_borders()

def _refresh_swatch_borders(self):
    for grid_col, grid_row, color_int, button in self._swatch_cells:
        red, green, blue = _color_int_to_rgb(color_int)
        if color_int == self._selected_color:
            button.setStyleSheet(
                f"background-color: rgb({red},{green},{blue}); "
                "border: 2px solid white; border-radius: 2px;"
            )
        else:
            button.setStyleSheet(
                f"background-color: rgb({red},{green},{blue}); "
                "border: 1px solid #555; border-radius: 2px;"
            )
```

### Pattern 2: Enter/OK Confirmation (PICKER-02)

**What:** Enter key and OK button both call `self.accept()`. `keyPressEvent` handles Enter OUTSIDE hint mode too (currently it only handles Enter inside hint mode).

```python
# In ColorPaletteDialog.keyPressEvent — extend the non-hint-mode path:
if event.key() in (Qt.Key_Return, Qt.Key_Enter):
    if self._selected_color is not None:
        if self._name_edit is not None:
            self.chosen_name = self._name_edit.text()
        self.accept()
    event.accept()
    return
```

The OK button is wired directly to `self.accept()` — no extra logic needed since `self._selected_color` is already updated by click.

### Pattern 3: Group Ordering with Blank Row Gap (PICKER-04)

**What:** Reorder `all_color_groups` to `[user_palette_colors, backdrop_colors, nuke_pref_colors]` and add a blank row gap between groups. The current "move to next group row" logic at end of each group loop is the gap — it already adds one blank row; verify it still works after reversal.

```python
all_color_groups = [
    group for group in [user_palette_colors, backdrop_colors, nuke_pref_colors]
    if group
]
# The existing end-of-group grid_row += 1 after "if group_col > 0" already
# creates the blank-row visual gap — no structural change needed here.
```

### Pattern 4: "Custom Color..." Staging (PICKER-05)

**What:** `_on_custom_color_clicked` appends to `self._staged_custom_colors` (a dialog-local list, not `prefs.custom_colors`). A new swatch is dynamically added to the grid and auto-highlighted. The caller reads the staged list via `chosen_custom_colors()` and decides whether to persist (i.e., on accept only).

```python
def __init__(self, ..., custom_colors=None, ...):
    self._custom_colors = list(custom_colors) if custom_colors else []
    self._staged_custom_colors = list(self._custom_colors)  # local working copy
    ...

def _on_custom_color_clicked(self):
    result = nuke.getColor()
    if result == 0:
        return
    self._staged_custom_colors.append(result)
    self._selected_color = result
    # Dynamically add swatch to grid
    self._append_swatch_to_grid(result)
    self._refresh_swatch_borders()
    # Dialog stays open — no self.accept()

def chosen_custom_colors(self):
    """Return staged custom colors (may include newly added; caller persists on accept)."""
    return list(self._staged_custom_colors)
```

### Pattern 5: PrefsDialog Layout

**What:** Standard QDialog with QVBoxLayout containing two QCheckBox widgets, a horizontal separator (QFrame), a "Custom Colors" label, a QWidget holding the swatch QGridLayout, three action buttons (Add/Edit/Remove), a second QFrame separator, and a QDialogButtonBox (OK/Cancel).

```python
class PrefsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        import prefs  # local import avoids circular dependency concern
        # Seed local working copies from prefs module
        self._plugin_enabled = prefs.plugin_enabled
        self._link_mode = prefs.link_classes_paste_mode
        self._local_custom_colors = list(prefs.custom_colors)
        self._selected_swatch_index = None  # index into _local_custom_colors
        self._build_ui()
```

### Pattern 6: Swatch Grid Refresh (Claude's Discretion: rebuild approach)

**What:** When Add/Edit/Remove changes `self._local_custom_colors`, clear and rebuild the grid widget rather than splicing individual cells. This eliminates index-tracking bugs at the cost of a brief visual flicker that is imperceptible at palette scale.

```python
def _rebuild_swatch_grid(self):
    # Clear all widgets from the QGridLayout
    while self._swatch_grid_layout.count():
        item = self._swatch_grid_layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.deleteLater()
    self._swatch_cells_prefs = []
    self._selected_swatch_index = None
    self._populate_swatch_grid()
    self._update_edit_remove_buttons()
```

### Pattern 7: Menu Integration (Claude's Discretion)

**What:** Add "Preferences..." as a permanently-active command after the Copy(old)/Cut(old)/Paste(old) block. Add a separator before it to visually separate fallback commands from the preferences entry.

```python
# In menu.py — after existing always-active block:
anchors_menu.addSeparator()
anchors_menu.addCommand(
    "Preferences...",
    "from colors import PrefsDialog; dlg = PrefsDialog(); dlg.exec_()"
)
```

### Anti-Patterns to Avoid

- **Calling `prefs.save()` inside `ColorPaletteDialog`:** The picker dialog must never call `prefs.save()`. Only `PrefsDialog.accept()` persists. The picker returns staged custom colors for the caller to handle.
- **Importing prefs at module level inside colors.py:** Circular import risk. Use `import prefs` inside `PrefsDialog.__init__` or `_on_accept`.
- **Using `QAutoDefault` for the OK button:** All buttons in dialogs that also have swatch buttons must set `setAutoDefault(False)` to prevent Enter interception by buttons. The Enter key is handled by `keyPressEvent`.
- **Mutating `prefs.custom_colors` directly from the picker:** The picker's staged list is a copy; the anchor-creation callers (anchor.py) already pass `custom_colors` via constructor injection. The caller that calls `prefs.save()` is exclusively `PrefsDialog`.
- **Checking `if not self._selected_color`:** Use `if self._selected_color is None` — the value `0` is a valid (black) color int.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Horizontal OK/Cancel button row | Custom HBoxLayout of QPushButton | `QDialogButtonBox(QDialogButtonBox.Ok \| QDialogButtonBox.Cancel)` | Handles platform-specific button order, styling, default key routing automatically |
| PySide2/PySide6 guard | Re-derive from nuke version each time | Existing try/except guard at top of colors.py | Pattern already established; copy for PrefsDialog guard |
| Color int → RGB conversion | Inline bit-shifting | `_color_int_to_rgb()` | Already tested, already used in ColorPaletteDialog |

**Key insight:** The swatch styling and `_color_int_to_rgb()` helper are the only shared rendering primitives needed. Everything else in the dialogs is standard Qt layout composition.

---

## Common Pitfalls

### Pitfall 1: `setAutoDefault` omission on new buttons
**What goes wrong:** A newly-added QPushButton in the dialog (e.g., OK, Add, Edit, Remove) defaults `autoDefault=True`, intercepting Enter key and accepting/triggering the button instead of routing to `keyPressEvent`.
**Why it happens:** Qt's default button policy enables autoDefault for QPushButton inside a QDialog.
**How to avoid:** Call `button.setAutoDefault(False)` on every QPushButton in both dialogs, as established by Phase 6 decision.
**Warning signs:** Pressing Enter triggers unexpected button click rather than confirming swatch selection.

### Pitfall 2: Checking selected color with falsy test
**What goes wrong:** `if self._selected_color:` evaluates to False when the selected color is `0` (black / no color in Nuke terms), silently rejecting a valid selection.
**Why it happens:** Python's truthiness treats integer 0 as False.
**How to avoid:** Always use `if self._selected_color is not None:` for color presence checks.
**Warning signs:** Black swatches cannot be confirmed; clicking them appears to do nothing.

### Pitfall 3: `nuke.getColor()` return value semantics
**What goes wrong:** `nuke.getColor()` returns `0` both when the user cancels AND when they pick pure black.
**Why it happens:** Nuke's API uses 0 as sentinel for cancellation.
**How to avoid:** This is a known limitation; treat 0 as cancel (consistent with existing `_on_custom_color_clicked` behavior). Document clearly in code comments. Black cannot be added as a custom color via the getColor dialog — this is acceptable and pre-existing behavior.
**Warning signs:** No action on Add/Edit when user picks black (correct behavior, not a bug).

### Pitfall 4: Circular import between colors.py and prefs.py
**What goes wrong:** If `colors.py` imports `prefs` at module level (e.g., `import prefs`), and `prefs.py` ever imports from `colors`, a circular import occurs.
**Why it happens:** Module-level imports execute immediately at import time.
**How to avoid:** `PrefsDialog.__init__` or `_on_accept` should import prefs locally (`import prefs`). The existing pattern in `ColorPaletteDialog` is constructor injection — maintain that pattern; `PrefsDialog` reads `prefs.*` inside its `__init__` only.
**Warning signs:** `ImportError: cannot import name 'X' from partially initialized module`.

### Pitfall 5: Stale prefs module-level variables after PrefsDialog accept
**What goes wrong:** `PrefsDialog` updates `prefs.plugin_enabled = new_value` but does not call `menu.set_anchors_menu_enabled()`, leaving the menu in its old state for the rest of the session.
**Why it happens:** Forgetting the live-apply step — `prefs.save()` writes to disk but does not update runtime behavior.
**How to avoid:** The `_on_accept` slot must (in order): update all three `prefs.*` module-level variables, call `prefs.save()`, call `menu.set_anchors_menu_enabled(prefs.plugin_enabled)`. This sequence is locked in CONTEXT.md.
**Warning signs:** Preferences appear saved (survive restart) but the menu enable state is wrong until next Nuke launch.

### Pitfall 6: `exec_()` vs `exec()` PySide2/PySide6 compatibility
**What goes wrong:** PySide2 uses `dialog.exec_()` while PySide6 deprecated `exec_()` in favor of `exec()`. Using the wrong one raises `AttributeError` or `DeprecationWarning`.
**Why it happens:** PySide API changed between versions.
**How to avoid:** Use `exec_()` — it works in both PySide2 and PySide6 (PySide6 maintains it as an alias). Alternatively, use `getattr(dialog, 'exec_', dialog.exec)()` for strict correctness. The existing codebase uses `exec_()` — stay consistent.
**Warning signs:** `AttributeError: 'PrefsDialog' object has no attribute 'exec'` or equivalent.

### Pitfall 7: QGridLayout column count for wrapping swatch grid in PrefsDialog
**What goes wrong:** If column count is too large, narrow Preferences dialogs have wide empty rows. Too small and the grid becomes tall with many rows.
**Why it happens:** QGridLayout does not auto-wrap; the developer controls columns explicitly.
**How to avoid:** Use `_SWATCHES_PER_ROW = 8` (already defined for the picker grid) as the column count for the PrefsDialog swatch grid. This maintains visual consistency.
**Warning signs:** PrefsDialog swatch grid looks misaligned or disproportionately wide/narrow compared to the picker.

---

## Code Examples

### Verified: Existing swatch click path (to be modified for PICKER-01)

```python
# Source: /workspace/colors.py line 192-196 — CURRENT behavior (closes dialog)
def _on_swatch_clicked(self, color_int):
    self._selected_color = color_int
    if self._name_edit is not None:
        self.chosen_name = self._name_edit.text()
    self.accept()  # <-- THIS LINE is removed in Phase 7
```

### Verified: Existing keyPressEvent Enter handling (hint-mode only — to be extended)

```python
# Source: /workspace/colors.py lines 245-255 — CURRENT: Enter only handled in hint mode
if event.key() in (Qt.Key_Return, Qt.Key_Enter):
    # Accept with currently highlighted cell if any
    if self._selected_color is not None:
        if self._name_edit is not None:
            self.chosen_name = self._name_edit.text()
        self.accept()
    event.accept()
    return
# The super().keyPressEvent(event) path at line 257 is reached for Enter outside hint mode
# Phase 7 must move this block OUTSIDE the `if self._hint_mode:` guard
```

### Verified: menu.py always-active command registration pattern

```python
# Source: /workspace/menu.py lines 67-69 — always-active ungated commands
anchors_menu.addCommand("Copy (old)",  "paste_hidden.copy_old()")
anchors_menu.addCommand("Cut (old)",   "paste_hidden.cut_old()")
anchors_menu.addCommand("Paste (old)", "paste_hidden.paste_old()", "+^D")
# CONTEXT.md confirms: Preferences item follows the same always-active pattern
```

### Verified: prefs module-level variables and save() signature

```python
# Source: /workspace/prefs.py lines 20-22, 68-83
plugin_enabled = True                    # bool
link_classes_paste_mode = "create_link"  # 'create_link' | 'passthrough'
custom_colors = []                       # list of int

def save():
    # writes plugin_enabled, link_classes_paste_mode, custom_colors to PREFS_PATH
```

### Verified: PySide2/PySide6 guard pattern

```python
# Source: /workspace/colors.py lines 5-16 — PrefsDialog must use same guard
try:
    if hasattr(nuke, 'NUKE_VERSION_MAJOR') and nuke.NUKE_VERSION_MAJOR >= 16:
        from PySide6 import QtCore, QtGui, QtWidgets
        from PySide6.QtCore import Qt
    else:
        from PySide2 import QtGui, QtWidgets, QtCore
        from PySide2.QtCore import Qt
except ImportError:
    QtGui = None
    QtWidgets = None
    QtCore = None
    Qt = None

# PrefsDialog null guard (parallel to ColorPaletteDialog):
if QtWidgets is None:
    PrefsDialog = None
else:
    class PrefsDialog(QtWidgets.QDialog): ...
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Click swatch → immediate close | Click swatch → highlight; Enter/OK → close | Phase 7 | PICKER-01/02 — more deliberate selection UX |
| Nuke defaults → backdrop → custom group order | Custom → backdrop → Nuke defaults | Phase 7 | PICKER-04 — user's own colors appear first |
| No preferences UI | PrefsDialog accessible from Anchors menu | Phase 7 | PANEL-01 through PANEL-07 |
| Custom colors in separate palette file | Custom colors in unified prefs.json | Phase 6 | Migration complete; PrefsDialog writes to prefs.json only |

**Deprecated/outdated:**
- `load_user_palette()` / `save_user_palette()` in colors.py: removed in Phase 6 — do not reference or recreate these.
- The separate `paste_hidden_user_palette.json` file: migration writes it once on first run if found; after that it is never written and effectively dead.

---

## Open Questions

1. **`QDialogButtonBox` vs manual OK/Cancel buttons**
   - What we know: CONTEXT.md specifies "OK and Cancel — horizontal, bottom-right", which is exactly what `QDialogButtonBox.Ok | QDialogButtonBox.Cancel` produces.
   - What's unclear: Whether the planner should use `QDialogButtonBox` (standard Qt) or two explicit `QPushButton` widgets (manual). Either works.
   - Recommendation: Use `QDialogButtonBox` for PrefsDialog — it handles platform button ordering and is the idiomatic Qt approach. For `ColorPaletteDialog`, keep existing Cancel `QPushButton` and add OK as a second `QPushButton` to minimize diff scope.

2. **`setAutoDefault(False)` on QDialogButtonBox buttons**
   - What we know: `QDialogButtonBox` buttons may have autoDefault behavior managed by Qt itself.
   - What's unclear: Whether setting `autoDefault(False)` on `QDialogButtonBox` buttons is necessary or whether the dialog-level `keyPressEvent` override takes precedence.
   - Recommendation: `ColorPaletteDialog` has a full `keyPressEvent` override that calls `super()` only in the non-hint, non-Enter path — the OK button's `clicked` signal is sufficient; no Enter-key routing through the button is needed. For PrefsDialog, there is no hint-mode complexity; standard `QDialogButtonBox` behavior (Enter confirms) is correct and desired. Only the swatch buttons in PrefsDialog need `setAutoDefault(False)`.

3. **Inline import of `menu` module inside `PrefsDialog._on_accept`**
   - What we know: `menu.py` imports `prefs` at module level. `colors.py` does not currently import `menu`. If `colors.py` imports `menu` at module level, and `menu.py` imports `colors`, a circular import would occur.
   - What's unclear: Whether `menu.py` will ever import from `colors`. Currently it does not.
   - Recommendation: Import `menu` inside `PrefsDialog._on_accept` (local import, executed only when dialog accepts) to eliminate any circular import risk now and in the future. Consistent with the established pattern of keeping colors.py free of module-level imports of other project files.

---

## Sources

### Primary (HIGH confidence)
- `/workspace/colors.py` — full source of `ColorPaletteDialog`, swatch grid implementation, `_color_int_to_rgb()`, PySide guard
- `/workspace/prefs.py` — full source of prefs singleton, save(), `_load()`, module-level variable names
- `/workspace/menu.py` — full source of anchors_menu registration, `_gated_menu_items`, `set_anchors_menu_enabled()`
- `/workspace/constants.py` — `PREFS_PATH`, `USER_PALETTE_PATH`, `ANCHOR_DEFAULT_COLOR`
- `.planning/phases/07-color-picker-redesign-and-preferences-panel/07-CONTEXT.md` — all locked implementation decisions

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` accumulated decisions — confirmed Phase 6 architecture constraints that Phase 7 must respect
- `.planning/REQUIREMENTS.md` — PANEL-01 through PANEL-07 and PICKER-01 through PICKER-05 requirement text

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — entire stack is in-repo source code; no external dependencies
- Architecture: HIGH — patterns derived directly from existing implementation in colors.py, prefs.py, menu.py
- Pitfalls: HIGH — identified from code reading (actual line references); PySide2/6 compat issues from known API delta
- Implementation scope: HIGH — CONTEXT.md fully specifies all UI decisions; no ambiguity in locked decisions

**Research date:** 2026-03-11
**Valid until:** Stable — internal codebase; not subject to external library churn
