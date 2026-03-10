# Stack Research

**Domain:** Nuke plugin — preferences panel and color picker redesign
**Researched:** 2026-03-10
**Confidence:** HIGH

## Context: This Is a Targeted Milestone

v1.0 shipped with a validated stack: Python 3 (Nuke embedded), PySide2/PySide6 conditional import guard,
JSON file persistence, Qt `QDialog` + `QGridLayout` + `QPushButton` swatches. This research covers
only the incremental additions needed for v1.1 — nothing already in use is re-evaluated.

---

## Recommended Stack

### Core Technologies (unchanged — do not re-evaluate)

| Technology | Version | Purpose | Notes |
|------------|---------|---------|-------|
| Python 3 | 3.9 (Nuke 14), 3.11 (Nuke 16) | Plugin runtime | Embedded — no package manager |
| PySide2 | 5.15 (Nuke 14/15) | Qt UI in Nuke < 16 | Import-guarded by `nuke.NUKE_VERSION_MAJOR` |
| PySide6 | 6.5 (Nuke 16) | Qt UI in Nuke 16+ | VFX Reference Platform 2024 |
| JSON / `json` stdlib | — | File persistence | Already used for `USER_PALETTE_PATH` |

### New for v1.1: Preferences Persistence

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `json` stdlib | stdlib | Preferences file read/write | Already used for user palette; no new dependency |
| `os.path.expanduser` | stdlib | `~/.nuke/paste_hidden_prefs.json` path resolution | Same pattern as `USER_PALETTE_PATH` in `constants.py` |

**Pattern: Prefs singleton class** — consistent with sibling Nuke tools (Labelmaker, tabtabtab-nuke):

```python
class Prefs:
    """Singleton for paste_hidden plugin preferences."""
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._data = {}
        self._load()

    def _load(self):
        try:
            with open(PREFS_PATH) as file_handle:
                self._data = json.load(file_handle)
        except (FileNotFoundError, json.JSONDecodeError):
            self._data = {}

    def save(self):
        os.makedirs(os.path.dirname(PREFS_PATH), exist_ok=True)
        with open(PREFS_PATH, 'w') as file_handle:
            json.dump(self._data, file_handle, indent=2)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
```

**Yes, paste_hidden should follow the same pattern.** The sibling pattern is validated and
consistent. Store at `~/.nuke/paste_hidden_prefs.json`, separate from the existing
`paste_hidden_user_palette.json` (which remains the color palette store — different lifecycle,
possibly different reset semantics).

### New for v1.1: Color Picker Redesign — Qt Widgets

| Widget | Module | Purpose | Notes |
|--------|--------|---------|-------|
| `QListWidget` | `QtWidgets` | Custom color management list (add/edit/remove) | Convenience class; sufficient for this use case |
| `QListWidgetItem` | `QtWidgets` | Per-color list entries with inline swatch | Use `setData(Qt.DecorationRole, QPixmap)` for color swatch |
| `QPixmap` | `QtGui` | 16×16 color swatch for `DecorationRole` | Create solid-color pixmap per entry |
| `QPainter` | `QtGui` | Fill swatch pixmap with color | Already in scope via existing `QtGui` import |
| `QHBoxLayout` | `QtWidgets` | Button row (Add / Edit / Remove) beside list | Standard layout — already used in existing dialogs |

**For the color management list specifically:** `QListWidget` + `QListWidgetItem` with
`Qt.DecorationRole` is the correct choice over `QListView` + `QAbstractListModel`. The dataset
is small (≤ ~20 custom colors), the operations are simple (append, remove, reorder), and
`QListWidget`'s convenience API avoids the model/view boilerplate that would add complexity
without benefit at this scale.

**Color swatch rendering pattern:**

```python
def _make_color_pixmap(color_int):
    red = (color_int >> 24) & 0xFF
    green = (color_int >> 16) & 0xFF
    blue = (color_int >> 8) & 0xFF
    pixmap = QPixmap(16, 16)
    pixmap.fill(QtGui.QColor(red, green, blue))
    return pixmap

item = QListWidgetItem("My color name")
item.setData(Qt.DecorationRole, _make_color_pixmap(color_int))
```

This pattern works identically in PySide2 and PySide6 — `Qt.DecorationRole` is available
in both (PySide6 retains the shorthand; no migration needed for this enum).

### New for v1.1: Color Picker Dialog Behavior Changes

These are behavioral changes to the existing `ColorPaletteDialog` — no new widgets required,
but specific Qt behavior must be understood:

**Click-to-select without closing:**
- Current: `_on_swatch_clicked` calls `self.accept()` immediately
- New behavior: First click selects (highlights border), second click or Enter accepts
- Implementation: Track `_pending_color` separately from `_selected_color`; call `accept()` only on confirmation
- No new widgets needed — just behavioral logic change

**Enter key accepts selected color:**
- Qt default: `QPushButton` inside a `QDialog` has `autoDefault=True`, meaning Enter triggers the focused button automatically
- This is the *cause* of the current problem — swatch buttons intercept Enter and close the dialog
- Fix: Call `button.setAutoDefault(False)` on all swatch buttons, then handle `Qt.Key_Return` / `Qt.Key_Enter` in `keyPressEvent` to call `accept()` if a color is pending
- This pattern already exists partially in the `keyPressEvent` override — it just needs the `autoDefault` fix on swatch buttons

**Custom color persistence:**
- `nuke.getColor()` returns a color int; save result to `load_user_palette()` / `save_user_palette()` immediately
- No new widget needed — existing `save_user_palette()` function handles this

**Swatch order (custom → backdrop → Nuke defaults):**
- Current order in `_build_ui`: Nuke prefs → backdrop → user palette
- New order: user palette → backdrop → Nuke prefs
- Change is purely in the `all_color_groups` list ordering in `_build_ui`

**Default color highlight:**
- Already implemented (`if color_int == self._selected_color` in `_build_ui`)
- Verify it survives the click-to-select refactor — `_selected_color` init from `initial_color` must be preserved

---

## Installation

No new packages. All additions draw from:
- Python stdlib: `json`, `os` (already imported in `colors.py` and `constants.py`)
- PySide2/PySide6: `QListWidget`, `QListWidgetItem`, `QPixmap` (already imported from `QtWidgets` / `QtGui`)

No `pip install`, no `requirements.txt` changes.

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `QListWidget` for color management | `QListView` + `QAbstractListModel` | Overkill for ≤20 items; model/view adds ~100 lines of boilerplate with no user-visible benefit at this scale |
| Separate `paste_hidden_prefs.json` | Add prefs to existing `paste_hidden_user_palette.json` | Different data with different semantics — palette is colors only, prefs are plugin settings. Mixing creates coupling and makes selective resets impossible |
| `Prefs` singleton with lazy load | Module-level dict | Singleton matches sibling tools (Labelmaker, tabtabtab-nuke), survives multiple imports within a session, and has clear ownership of save/load |
| `setAutoDefault(False)` + `keyPressEvent` | `QDialogButtonBox` with OK/Cancel | `QDialogButtonBox` would change the dialog chrome; existing keyboard shortcut system (`_hint_mode` via Tab) must be preserved — manual key handling is required here |
| `Qt.DecorationRole` (shorthand) | `Qt.ItemDataRole.DecorationRole` (fully qualified) | Both work in PySide6; shorthand also works in PySide2; using shorthand keeps the guard-free code consistent across both versions |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `QColorDialog` | Nuke has its own `nuke.getColor()` that returns Nuke-native color ints (0xRRGGBBAA); `QColorDialog` returns `QColor` requiring conversion, and misses Nuke's color management | `nuke.getColor()` — already used in `_on_custom_color_clicked` |
| `QStyledItemDelegate` with custom `paint()` | Necessary only if swatch + text layout cannot be achieved with `DecorationRole`; adds 40-60 lines of boilerplate | `QListWidgetItem.setData(Qt.DecorationRole, QPixmap(...))` — sufficient for a 16×16 swatch left of text |
| `qtpy` compatibility shim | Adds a third-party dependency; existing guard (`nuke.NUKE_VERSION_MAJOR >= 16`) already handles PySide2/PySide6 switching cleanly | Existing version-guarded conditional import in `colors.py` and `anchor.py` |
| Module-level singleton (i.e., `PREFS = Prefs()` at import time) | Executes disk I/O at import, not at first use; if `~/.nuke` does not exist yet, this can fail silently during plugin load | `Prefs.instance()` lazy initialization |

---

## Stack Patterns by Variant

**If Nuke < 16 (PySide2, Python 3.9):**
- `from PySide2 import QtWidgets, QtGui, QtCore` — existing guard covers this
- `Qt.DecorationRole` works as-is in PySide2
- `QPixmap.fill(QColor(...))` works in PySide2

**If Nuke 16+ (PySide6, Python 3.11):**
- `from PySide6 import QtWidgets, QtGui, QtCore` — existing guard covers this
- `Qt.DecorationRole` still works (PySide6 retains shorthand for backwards compatibility)
- No enum migration needed for the specific roles used here

**If Qt unavailable (headless / test environment):**
- Existing `try/except ImportError` guard at top of `colors.py` sets `QtWidgets = None`
- `ColorPaletteDialog = None` guard already present
- Prefs class must be defined outside any Qt guard — it is pure Python/JSON, no Qt dependency

---

## Version Compatibility

| Component | Nuke 14 | Nuke 15 | Nuke 16 |
|-----------|---------|---------|---------|
| Python | 3.9 | 3.10/3.11 | 3.11 |
| Qt | 5.15.2 | 5.15 | 6.5 |
| PySide | PySide2 5.15 | PySide2 5.15 | PySide6 6.5 |
| `Qt.DecorationRole` | Yes | Yes | Yes (shorthand retained) |
| `QListWidget` | Yes | Yes | Yes |
| `QPixmap.fill(QColor)` | Yes | Yes | Yes |
| `setAutoDefault(False)` | Yes | Yes | Yes |

Confidence: MEDIUM — Nuke 14 Python version is confirmed (3.9) from release notes; Nuke 15
exact Python subversion is less certain but 3.10/3.11 range is consistent with VFX RP 2023.

---

## Sources

- Erwan Leroy, "Updating Your Python Scripts for Nuke 16 and PySide6" — PySide2→PySide6 guard pattern, enum compatibility
- Foundry support article Q100715 — PySide6 migration in Nuke 16
- Foundry release notes Nuke 14.0 — Python 3.9, PySide2 5.15 confirmed
- Qt for Python official docs (doc.qt.io/qtforpython-6/) — QListWidget, QListWidgetItem, QStyledItemDelegate, QPushButton.setAutoDefault
- WebSearch: Qt DecorationRole enum backwards compatibility in PySide6 (MEDIUM confidence — not tested in Nuke runtime)
- Existing codebase: `colors.py`, `constants.py` — confirmed existing patterns for JSON persistence, Qt guard, QDialog structure

---
*Stack research for: paste_hidden v1.1 — preferences panel and color picker redesign*
*Researched: 2026-03-10*
