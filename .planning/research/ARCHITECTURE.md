# Architecture Research

**Domain:** Nuke plugin — preferences panel and color picker redesign (v1.1)
**Researched:** 2026-03-10
**Confidence:** HIGH — derived from direct codebase inspection and sibling project pattern (milestone context)

---

## Standard Architecture

### System Overview (current v1.0)

```
┌─────────────────────────────────────────────────────────────────┐
│                         menu.py                                  │
│  (keybindings → paste_hidden, anchor, labels)                   │
├───────────────────┬───────────────────┬─────────────────────────┤
│   paste_hidden.py │    anchor.py      │      labels.py          │
│  copy_hidden()    │  create_anchor()  │  create_large_label()   │
│  paste_hidden()   │  rename_anchor()  │  append_to_label()      │
│                   │  set_anchor_color │                         │
├───────────────────┴──────────┬────────┴─────────────────────────┤
│             link.py          │            colors.py              │
│  is_anchor(), is_link()      │  ColorPaletteDialog              │
│  setup_link_node()           │  load_user_palette()             │
│  find_anchor_node()          │  save_user_palette()             │
│  get_link_class_for_source() │  _get_nuke_pref_colors()         │
│  add_input_knob()            │  _get_script_backdrop_colors()   │
├──────────────────────────────┴──────────────────────────────────┤
│                          constants.py                            │
│  LINK_SOURCE_CLASSES (frozenset)   USER_PALETTE_PATH            │
│  ANCHOR_DEFAULT_COLOR              HIDDEN_INPUT_CLASSES         │
│  KNOB_NAME, TAB_NAME, et al.                                    │
├─────────────────────────────────────────────────────────────────┤
│                 Persistence (file system)                        │
│  ~/.nuke/paste_hidden_user_palette.json  (custom colors)        │
│  ~/.nuke/paste_hidden_anchor_weights.json                       │
│  ~/.nuke/paste_hidden_anchor_navigate_weights.json              │
└─────────────────────────────────────────────────────────────────┘
```

### System Overview (v1.1 target — new components shaded)

```
┌─────────────────────────────────────────────────────────────────┐
│  menu.py  +  "Preferences..." menu item → prefs.open_prefs()   │
├───────────────────┬──────────────┬──────────────────────────────┤
│   paste_hidden.py │  anchor.py   │   [NEW] prefs.py             │
│  copy_hidden()    │  (unchanged) │   Prefs singleton            │
│  paste_hidden()   │              │   PrefsDialog                │
│  [reads Prefs for │              │   open_prefs()               │
│   LINK_CLASSES    │              │                              │
│   paste mode]     │              │                              │
├───────────────────┴──────────────┴──────────────────────────────┤
│  link.py (unchanged)  │  colors.py [MODIFIED]                   │
│                       │  ColorPaletteDialog (click-to-select,   │
│                       │    Enter-accepts, highlight pre-sel.)    │
│                       │  load_user_palette() → delegates to     │
│                       │    Prefs OR reads own section           │
│                       │  save_user_palette() → same             │
├───────────────────────┴─────────────────────────────────────────┤
│  constants.py [MODIFIED]                                        │
│  + PREFS_PATH = ~/.nuke/paste_hidden_prefs.json                 │
│  USER_PALETTE_PATH kept for migration / backward compat         │
├─────────────────────────────────────────────────────────────────┤
│                 Persistence (file system)                        │
│  ~/.nuke/paste_hidden_prefs.json  ← NEW, absorbs palette        │
│  ~/.nuke/paste_hidden_user_palette.json  ← deprecated / migrated│
└─────────────────────────────────────────────────────────────────┘
```

---

## Question-by-Question Answers

### Q1: Should paste_hidden_prefs.json absorb user_palette.json or keep them separate?

**Recommendation: Absorb. Use a single `paste_hidden_prefs.json` with a `"custom_colors"` key.**

Rationale:
- The sibling pattern (Labelmaker, tabtabtab-nuke) uses one `<plugin>_prefs.json` per plugin — following the established convention avoids inventing a new pattern.
- The user palette is a preference, not distinct state. Separating it creates two files for one conceptual settings surface.
- A unified file simplifies the `Prefs` API: `prefs.custom_colors` is one attribute, not a second file path.
- Migration is trivial at load time: if `paste_hidden_prefs.json` exists, use it; otherwise check for `paste_hidden_user_palette.json` and import its contents into the new file on first write.

**Prefs JSON schema:**

```json
{
  "link_classes_paste_mode": "replace",
  "custom_colors": [1855176959, 1124073727],
  "plugin_enabled": true
}
```

- `"link_classes_paste_mode"`: `"replace"` (default, current behaviour — file nodes paste as links) or `"passthrough"` (paste file nodes as-is without link replacement).
- `"custom_colors"`: list of 0xRRGGBBAA ints, replaces `paste_hidden_user_palette.json`.
- `"plugin_enabled"`: boolean; when `false`, `copy_hidden` / `paste_hidden` / `anchor_shortcut` skip all plugin logic and delegate to Nuke's native behaviour.

`USER_PALETTE_PATH` stays in `constants.py` only as a migration source reference. `PREFS_PATH` is the new canonical constant.

---

### Q2: Where does the Prefs singleton live — new prefs.py or in constants.py?

**Recommendation: New `prefs.py` module.**

`constants.py` must stay import-safe at module load time with zero side effects — it is imported by `link.py`, `anchor.py`, `paste_hidden.py`, and `colors.py`. Placing a singleton with file I/O and JSON parsing there violates that contract and creates circular-import risk if `Prefs` later needs to import from any of those modules.

`prefs.py` is a thin dedicated module:

```
prefs.py
  Prefs          — singleton class, loaded once, holds in-memory state
  PrefsDialog    — PySide2/PySide6 QDialog (Qt-guarded, like ColorPaletteDialog)
  open_prefs()   — entry point called by menu
  load_prefs()   — module-level helper (reads JSON, returns Prefs instance)
```

`constants.py` gains only `PREFS_PATH`:

```python
PREFS_PATH = os.path.expanduser('~/.nuke/paste_hidden_prefs.json')
```

`Prefs` class structure (conceptual):

```python
class Prefs:
    """Singleton: plugin-wide preferences, backed by ~/.nuke/paste_hidden_prefs.json."""
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls._load()
        return cls._instance

    @classmethod
    def _load(cls): ...  # reads PREFS_PATH, migrates old palette if needed

    def save(self): ...  # writes PREFS_PATH

    # Properties
    plugin_enabled: bool
    link_classes_paste_mode: str       # "replace" | "passthrough"
    custom_colors: list                # list of 0xRRGGBBAA ints
```

`colors.py` replaces its direct `USER_PALETTE_PATH` / `load_user_palette()` / `save_user_palette()` calls with delegation to `Prefs.instance().custom_colors` and `prefs.save()`. The standalone `load_user_palette()` / `save_user_palette()` functions can be removed or retained as thin wrappers for one release cycle to avoid breaking any external callers (none exist in this single-artist codebase, so immediate removal is fine).

Import chain with `prefs.py` added:

```
constants.py         (no imports from plugin)
  ↑
link.py              (imports constants)
  ↑
colors.py            (imports constants, prefs)
anchor.py            (imports constants, colors, link)
paste_hidden.py      (imports constants, anchor, link, prefs)
labels.py            (imports constants, link)
prefs.py             (imports constants, colors [for dialog init])
  ↑
menu.py              (imports all of the above)
```

No circular imports. `prefs.py` imports `colors` only for building the PrefsDialog's custom-color management widget; `colors.py` imports `prefs` for reading/writing `custom_colors`. This creates a potential cycle. **Resolution:** `colors.py` receives custom colors as a parameter at `ColorPaletteDialog` construction time (injected by callers) and calls back through a callable rather than importing `prefs` directly. See Architecture Patterns below.

---

### Q3: How does LINK_CLASSES paste mode pref integrate with copy_hidden() logic?

**The pref gates Path A in `copy_hidden()` only. `paste_hidden()` needs no change.**

Current `copy_hidden()` Path A:

```python
if node.Class() in LINK_SOURCE_CLASSES:
    # … stamps anchor FQNN, prepares for link replacement on paste
```

`LINK_SOURCE_CLASSES` is a module-level `frozenset` in `constants.py`. In `passthrough` mode the plugin should not stamp the `KNOB_NAME` knob on file nodes at all — then `paste_hidden()` simply skips them (the `KNOB_NAME not in node.knobs()` guard at the top of its loop already handles this correctly).

**Integration point:** At the top of `copy_hidden()`, read `Prefs.instance()` once:

```python
def copy_hidden(cut=False):
    from prefs import Prefs
    effective_link_classes = (
        LINK_SOURCE_CLASSES
        if Prefs.instance().link_classes_paste_mode == "replace"
        else frozenset()
    )
    # ... rest of function uses effective_link_classes instead of LINK_SOURCE_CLASSES
```

Using a deferred `from prefs import Prefs` inside the function body avoids adding a module-level import to `paste_hidden.py` that could introduce load-order issues during Nuke startup. Alternatively a module-level import is fine if `prefs.py` is always loaded before `paste_hidden.py` (which `menu.py` controls).

`paste_hidden()` requires no change: if `KNOB_NAME` was never stamped (passthrough mode at copy time), the paste loop's guard `if KNOB_NAME not in node.knobs(): continue` skips the node silently.

The `plugin_enabled` pref is a separate gate. When `False`, `copy_hidden()` delegates to `copy_old()` and `paste_hidden()` delegates to `paste_old()`. This gate is checked at the `menu.py` entry-point level or at the top of each public function — the latter is safer because keybindings are already registered and cannot be un-registered cleanly without Nuke restart.

---

### Q4: What changes are needed to ColorPaletteDialog for click-to-select-without-closing and highlighted pre-selection?

**The dialog needs a "selected vs confirmed" state split.**

Current problem: `_on_swatch_clicked()` sets `_selected_color` and immediately calls `self.accept()`. There is no intermediate "highlighted" state.

**Required state changes:**

| State variable | Purpose |
|---|---|
| `_selected_color` | Currently selected (highlighted) swatch — survives navigation |
| `_confirmed` | Whether the user has confirmed (Enter / second click / OK button) |

**Behaviour model:**
- Single click on swatch → highlight it (update `_selected_color`, redraw border), do NOT close.
- Enter key → if `_selected_color` is set, call `self.accept()`.
- Double-click on swatch → call `self.accept()` immediately (optional, but natural).
- Dedicated "OK" / "Accept" button at bottom → call `self.accept()`.
- Escape → `self.reject()` (unchanged).

**Highlight rendering:** The current approach inlines `setStyleSheet()` on each button individually at construction time for the pre-selected color. For click-to-select, the highlight must be dynamically updated: a `_redraw_swatch_highlights()` method iterates `_swatch_cells` and applies the highlighted border to the currently selected button, clearing it from others.

```python
def _redraw_swatch_highlights(self):
    for grid_col, grid_row, color_int, button in self._swatch_cells:
        r, g, b = _color_int_to_rgb(color_int)
        if color_int == self._selected_color:
            border = "2px solid white"
        else:
            border = "1px solid #555"
        button.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border: {border}; border-radius: 2px;"
        )
```

**`_on_swatch_clicked` revised behaviour:**

```python
def _on_swatch_clicked(self, color_int):
    self._selected_color = color_int
    if self._name_edit is not None:
        self.chosen_name = self._name_edit.text()
    self._redraw_swatch_highlights()
    # Do NOT call self.accept() here — user must press Enter or OK
```

**Enter key in non-hint mode:** Currently `keyPressEvent` only handles Enter inside `_hint_mode`. It must also handle Enter in normal mode:

```python
if event.key() in (Qt.Key_Return, Qt.Key_Enter):
    if self._selected_color is not None:
        if self._name_edit is not None:
            self.chosen_name = self._name_edit.text()
        self.accept()
    event.accept()
    return
```

This goes in the top-level (non-hint-mode) branch of `keyPressEvent`, before the `super()` call.

**Custom color flow:** `_on_custom_color_clicked` currently sets `_selected_color` from `nuke.getColor()` and calls `self.accept()`. After the redesign, calling `self.accept()` immediately after `nuke.getColor()` is still correct — the user made an explicit selection in the native color picker, so confirmation is implicit. This path does not need to change.

**Pre-selection highlight:** The current construction-time `setStyleSheet` override for the pre-selected swatch is correct. After the redesign, `_redraw_swatch_highlights()` is called once at the end of `_build_ui()` to replace the inline override, giving a single canonical rendering path.

**OK button:** Add an "OK" / "Apply" `QPushButton` alongside "Cancel". Assign `Qt.Key_Return` to it as the default button (`button.setDefault(True)`) so Enter triggers it without needing custom `keyPressEvent` handling. However, since the dialog has `FocusPolicy.NoFocus` on swatches and `_name_edit` may capture Enter, explicit `keyPressEvent` handling is more reliable.

---

## Component Boundaries (v1.1)

| Component | Responsibility | New / Modified |
|-----------|---------------|----------------|
| `constants.py` | Named constants only — adds `PREFS_PATH` | Modified (additive) |
| `prefs.py` | `Prefs` singleton, `PrefsDialog`, `open_prefs()` | **New** |
| `colors.py` | `ColorPaletteDialog` (redesigned), `_get_nuke_pref_colors()`, `_get_script_backdrop_colors()` | Modified |
| `paste_hidden.py` | Reads `Prefs.instance()` once per `copy_hidden()` call to resolve effective link classes | Modified (minimal) |
| `anchor.py` | Unchanged — calls `ColorPaletteDialog` with same interface | Unchanged |
| `link.py` | Unchanged | Unchanged |
| `labels.py` | Unchanged | Unchanged |
| `menu.py` | Adds "Preferences..." menu item | Modified (additive) |
| `tests/` | New tests for `Prefs` load/save/migrate; `ColorPaletteDialog` state; `copy_hidden` passthrough mode | Modified (additive) |

---

## Recommended Project Structure (v1.1)

```
paste_hidden/
├── anchor.py             # unchanged
├── colors.py             # ColorPaletteDialog redesign, delegates custom_colors to prefs
├── constants.py          # adds PREFS_PATH; keeps USER_PALETTE_PATH for migration ref
├── labels.py             # unchanged
├── link.py               # unchanged
├── menu.py               # adds Preferences menu item
├── paste_hidden.py       # reads Prefs for link_classes_paste_mode
├── prefs.py              # NEW — Prefs singleton + PrefsDialog
├── tabtabtab.py          # unchanged
├── util.py               # unchanged
└── tests/
    ├── test_prefs.py          # NEW — Prefs load, save, migrate, defaults
    ├── test_color_picker.py   # NEW — click-to-select, Enter-accept, highlight state
    ├── test_passthrough_mode.py # NEW — copy_hidden with link_classes_paste_mode=passthrough
    └── ... (existing tests unchanged)
```

---

## Architectural Patterns

### Pattern 1: Dependency Injection for Prefs → Colors (avoid circular import)

**What:** `colors.py` cannot `import prefs` if `prefs.py` imports `colors` for `ColorPaletteDialog` construction inside `PrefsDialog`. Circular import at module level would crash Nuke startup.

**Solution:** `ColorPaletteDialog` receives `custom_colors` as a constructor parameter (list of ints) and a `on_custom_colors_changed` callable. It never imports `prefs` directly.

```python
class ColorPaletteDialog(QtWidgets.QDialog):
    def __init__(
        self,
        initial_color=None,
        show_name_field=False,
        initial_name="",
        custom_colors=None,         # injected — list of 0xRRGGBBAA ints
        on_save_custom_colors=None, # injected — callable(list) → None
        parent=None,
    ):
```

Callers (`anchor.py`, `prefs.py`) load `Prefs.instance().custom_colors` and pass it in. This is the established injection pattern in single-file Nuke plugins.

**Trade-off:** Slightly more verbose call sites; eliminates all circular import risk.

---

### Pattern 2: Deferred Prefs Loading (avoid Nuke startup cost)

**What:** `Prefs.instance()` is not called at module import time — only at first use. This matches how Nuke plugins must behave: module-level code runs during `.nk` script load and must be near-instant.

```python
# In prefs.py
_prefs_instance = None

def get_prefs():
    global _prefs_instance
    if _prefs_instance is None:
        _prefs_instance = _load_from_disk()
    return _prefs_instance
```

A module-level function (`get_prefs()`) rather than a class classmethod is simpler and avoids accidentally calling class machinery before Nuke is fully initialized.

**Trade-off:** Global mutable state; acceptable for a single-artist plugin with no concurrency.

---

### Pattern 3: Migration at First Write (not at load time)

**What:** On startup, `get_prefs()` reads `paste_hidden_prefs.json` if it exists. If the file is absent but `paste_hidden_user_palette.json` exists, it reads the old palette into `custom_colors` in memory. It does NOT write the new file immediately — it writes on the next `save()` call (when the user changes a setting or the dialog closes with changes). This avoids a spurious file write on every clean Nuke startup.

```python
def _load_from_disk():
    if os.path.exists(PREFS_PATH):
        return _parse_prefs_json(PREFS_PATH)
    # Migration path
    migrated_custom_colors = load_user_palette()  # from colors module, or inline
    return PrefsData(custom_colors=migrated_custom_colors)  # defaults for all other fields
```

**Trade-off:** One extra existence-check per Nuke session until the new file is created. Negligible.

---

### Pattern 4: Swatch Highlight as Ephemeral Render State

**What:** The highlighted swatch border is not stored in the model — it is derived from `_selected_color` on every `_redraw_swatch_highlights()` call. This avoids stale state where a button's `styleSheet` disagrees with `_selected_color`.

Do not store `_highlighted_button` as a separate reference. Always redraw all swatches from `_selected_color`. With ~30–80 swatches this is trivially fast.

**Trade-off:** Slightly more work per click than tracking a single reference; eliminates an entire class of highlight-desync bugs.

---

## Data Flow

### Flow 1: Color Picker — click-to-select, then Enter to confirm

```
User clicks swatch
    ↓
_on_swatch_clicked(color_int)
    → sets _selected_color = color_int
    → _redraw_swatch_highlights()   (updates all button borders)
    → does NOT call accept()

User presses Enter
    ↓
keyPressEvent(Key_Return)
    → _selected_color is not None
    → chosen_name = _name_edit.text() (if present)
    → self.accept()

Caller receives dialog.exec_() == Accepted
    → dialog.selected_color_int()
    → dialog.chosen_name
```

### Flow 2: Prefs change for LINK_CLASSES paste mode

```
User opens Preferences (menu item)
    ↓
open_prefs() → PrefsDialog.exec_()
    → user toggles link_classes_paste_mode radio button
    → user clicks OK

PrefsDialog.accept()
    → get_prefs().link_classes_paste_mode = new_value
    → get_prefs().save()

Next copy_hidden() call
    ↓
effective_link_classes = (
    LINK_SOURCE_CLASSES if get_prefs().link_classes_paste_mode == "replace"
    else frozenset()
)
```

### Flow 3: Custom color persisted via color picker

```
User opens ColorPaletteDialog → clicks "Custom Color..."
    ↓
nuke.getColor() → result
    → _selected_color = result
    → self.accept()   (implicit confirmation)

Caller (anchor.set_anchor_color or prefs.PrefsDialog)
    ↓
chosen = dialog.selected_color_int()
if chosen not in existing custom_colors:
    get_prefs().custom_colors.append(chosen)
    get_prefs().save()
```

### Flow 4: Prefs migration on first Nuke session after upgrade

```
Nuke starts → menu.py imports
    ↓ (prefs.py loaded but get_prefs() not called yet)

User invokes Create Anchor → anchor.create_anchor()
    ↓
ColorPaletteDialog(custom_colors=get_prefs().custom_colors, ...)
    ↓
get_prefs() called for first time
    ↓
_load_from_disk():
    paste_hidden_prefs.json absent?
    → check paste_hidden_user_palette.json
    → if found: load palette into custom_colors
    → return PrefsData(custom_colors=[...], defaults for rest)

Dialog shows with migrated colors.
User changes a color → get_prefs().save()
    → paste_hidden_prefs.json created
    → old file stays (not deleted; user can clean up)
```

---

## Integration Points

### Internal Module Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `paste_hidden.py` ↔ `prefs.py` | Direct call `get_prefs()` inside `copy_hidden()` | Deferred import or module-level import both work; deferred safer |
| `anchor.py` ↔ `colors.py` | Unchanged — `ColorPaletteDialog(custom_colors=get_prefs().custom_colors, on_save_custom_colors=...)` | `anchor.py` gains two keyword args to its dialog calls |
| `colors.py` ↔ `prefs.py` | Zero — injection only (no import) | Critical for avoiding circular import |
| `prefs.py` ↔ `colors.py` | `prefs.py` imports `colors.ColorPaletteDialog` for use inside `PrefsDialog` custom-color management | One-way import |
| `constants.py` ↔ all | Unchanged — gains `PREFS_PATH` | Purely additive |
| `menu.py` ↔ `prefs.py` | `import prefs; prefs.open_prefs()` from new menu item | Additive |

### External Integration

| System | Integration | Notes |
|--------|-------------|-------|
| Nuke Preferences node | `_get_nuke_pref_colors()` reads it | Unchanged |
| Nuke `nuke.getColor()` | Used by `_on_custom_color_clicked` | Unchanged |
| File system `~/.nuke/` | `PREFS_PATH` written by `Prefs.save()` | New file; old palette file kept for migration |

---

## Anti-Patterns

### Anti-Pattern 1: Putting Prefs in constants.py

**What people do:** Add a `Prefs` class or `load_prefs()` call to `constants.py` for convenience.

**Why it's wrong:** `constants.py` is imported first by the entire import chain. Any side effect (file I/O, JSON parsing, OS calls beyond `os.path.expanduser`) at module load time blocks Nuke startup and risks import ordering errors. A `Prefs` class there would also invite circular imports as it grows.

**Do this instead:** Isolate `Prefs` in `prefs.py` with lazy loading via `get_prefs()`.

---

### Anti-Pattern 2: Keeping user_palette.json as a parallel active file

**What people do:** Leave `load_user_palette()` / `save_user_palette()` writing to the old path alongside the new prefs file.

**Why it's wrong:** Two files with overlapping state diverge. After a prefs save, the old file is stale; if the plugin later reads from it during migration it will overwrite user customizations.

**Do this instead:** After migration, `custom_colors` lives exclusively in `paste_hidden_prefs.json`. The old file is read once (migration), never written again. `USER_PALETTE_PATH` becomes a read-only migration-source constant.

---

### Anti-Pattern 3: Accepting dialog on first swatch click (current behaviour)

**What people do:** Call `self.accept()` in `_on_swatch_clicked()` (current `ColorPaletteDialog`).

**Why it's wrong:** Forces accidental selections. Any mis-click closes the dialog with an unwanted color. Users cannot browse swatches before committing. The v1.1 requirement explicitly calls this out.

**Do this instead:** Separate highlight (click) from confirmation (Enter or OK button). See Pattern 4 above.

---

### Anti-Pattern 4: Module-level import of prefs in paste_hidden.py

**What people do:** `from prefs import get_prefs` at the top of `paste_hidden.py`.

**Why it's wrong (mild risk):** `paste_hidden.py` is imported at Nuke startup via `menu.py`. If `prefs.py` has any import-time side effect, it runs at startup. More importantly, `prefs.py` imports `colors.py` which imports Qt — if Qt is unavailable (headless render), the import chain must not crash.

**Do this instead:** `from prefs import get_prefs` inside `copy_hidden()` function body, or ensure `prefs.py` has the same Qt guard as `colors.py` and the module-level import is safe. The inline import approach mirrors the existing `from constants import ANCHOR_PREFIX` pattern already used inside `paste_hidden._extract_display_name_from_fqnn()`.

---

## Suggested Build Order

Dependencies must be built bottom-up. This order ensures each piece is testable before the next is built.

| Step | Work item | Depends on |
|------|-----------|------------|
| 1 | Add `PREFS_PATH` to `constants.py` | — |
| 2 | Create `prefs.py` — `Prefs` data class + `get_prefs()` + JSON load/save + migration logic | Step 1, `colors.load_user_palette()` |
| 3 | Write `tests/test_prefs.py` — load, save, defaults, migration | Step 2 |
| 4 | Redesign `ColorPaletteDialog` — constructor injection, click-to-select, Enter-accept, `_redraw_swatch_highlights()` | Step 1 (no new prefs dep yet) |
| 5 | Write `tests/test_color_picker.py` — state machine tests for highlight / confirm | Step 4 |
| 6 | Update `anchor.py` call sites to pass `custom_colors=get_prefs().custom_colors, on_save_custom_colors=...` | Steps 2, 4 |
| 7 | Update `paste_hidden.copy_hidden()` to read `get_prefs().link_classes_paste_mode` | Steps 2, 3 |
| 8 | Write `tests/test_passthrough_mode.py` | Step 7 |
| 9 | Create `PrefsDialog` in `prefs.py` | Steps 2, 4 |
| 10 | Add "Preferences..." to `menu.py` | Step 9 |
| 11 | Integration smoke-test in Nuke | Steps 1–10 |

Steps 4–5 (color picker redesign) and Steps 2–3 (Prefs core) are independent and can be built in parallel if desired.

---

## Sources

- Direct inspection: `/workspace/colors.py`, `constants.py`, `anchor.py`, `paste_hidden.py`, `link.py`, `menu.py`, `labels.py` — v1.0 codebase
- Sibling plugin pattern: Labelmaker and tabtabtab-nuke Prefs pattern described in milestone context (Prefs class + PrefsDialog + `~/.nuke/<plugin>_prefs.json`)
- `PROJECT.md` v1.1 milestone requirements

---
*Architecture research for: paste_hidden v1.1 — preferences panel and color picker redesign*
*Researched: 2026-03-10*
