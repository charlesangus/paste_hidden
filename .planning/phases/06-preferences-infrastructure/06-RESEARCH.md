# Phase 6: Preferences Infrastructure - Research

**Researched:** 2026-03-10
**Domain:** Python module-level singleton pattern, JSON persistence, plugin gate logic, module migration
**Confidence:** HIGH

## Summary

Phase 6 introduces a `prefs.py` module providing a module-level preferences singleton loaded once at Nuke startup. The module persists to `~/.nuke/paste_hidden_prefs.json` and absorbs the old `paste_hidden_user_palette.json` via a lazy one-way migration. It gates all plugin clipboard and anchor functionality on `plugin_enabled`, and gates LINK_CLASSES copy behavior on `link_classes_paste_mode`.

The implementation is pure Python/JSON with no Qt dependency. All decisions are locked in CONTEXT.md. The main design risks are: circular-import prevention (solved by constructor injection on `ColorPaletteDialog`), correct gate placement (confirmed in `copy_hidden()` for `link_classes_paste_mode`), and menu item enable/disable (requires Nuke `nuke.menu()` item reference retention at registration time).

**Primary recommendation:** Build `prefs.py` as a module-level singleton that loads at import time with explicit `save()` function; gate `copy_hidden` / `cut_hidden` / `paste_hidden` via early-return to `nuke.nodeCopy()` / `nuke.nodePaste()`; gate anchor and label entry points with a one-line guard; drive menu enable/disable from stored item references in `menu.py`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Prefs module structure:** Module-level singleton: `import prefs; prefs.plugin_enabled`, `prefs.link_classes_paste_mode`, `prefs.custom_colors`. Loads `paste_hidden_prefs.json` at import time (Nuke startup — once per session). Phase 7 calls `prefs.save()` after the PrefsDialog closes.
- **Prefs file keys and defaults:** `plugin_enabled` — default `True`; `link_classes_paste_mode` — values: `"create_link"` (default) or `"passthrough"`; `custom_colors` — default `[]`
- **link_classes_paste_mode gate:** Lives in `copy_hidden()` where the FQNN stamp is written. When `"passthrough"`: skip FQNN stamping for LINK_CLASSES nodes entirely — plain `nuke.nodeCopy()` with no stamp and no `add_input_knob()` call for those nodes. Other copy paths (hidden Dots, anchors) are unaffected.
- **plugin_enabled scope:** When `False`: ALL plugin functionality is disabled — clipboard trio falls through to `nuke.nodeCopy()`/`nuke.nodePaste()`, AND all anchor operations (Create Anchor, Alt+A, Alt+Z, labels) are silent no-ops. All Anchors menu items are greyed out except the Preferences entry. Menu items re-enable/re-disable when user toggles the setting via Preferences dialog (Phase 7 triggers this). `link_classes_paste_mode` is a separate, independent pref for LINK_CLASSES behavior when the plugin IS enabled.
- **Migration from old palette file:** Lazy migration: on first load, if `paste_hidden_prefs.json` does not exist but `paste_hidden_user_palette.json` does, read colors from old file and populate `custom_colors` in the new prefs. Write new prefs file on first save; never write to `paste_hidden_user_palette.json` again. If old file has invalid/corrupt data: silently use empty `custom_colors`.
- **colors.py transition:** `load_user_palette()` and `save_user_palette()` are removed in Phase 6. `ColorPaletteDialog` receives `custom_colors` as a constructor parameter (no import of `prefs` from `colors.py` — prevents circular dependency). Callers that previously called `load_user_palette()` now read `prefs.custom_colors` directly. `ColorPaletteDialog` does not write custom_colors — write path stays with callers (unchanged).

### Claude's Discretion
- Error handling for corrupt/missing prefs file: silent fallback to defaults
- Exact JSON schema validation approach
- How `prefs.save()` is structured internally

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PREFS-01 | Preferences are persisted to `~/.nuke/paste_hidden_prefs.json` with keys: `plugin_enabled`, `link_classes_paste_mode`, `custom_colors` | Module-level singleton pattern with `os.path.expanduser`; JSON load/dump pattern already in `colors.py:load_user_palette()` |
| PREFS-02 | On first run with no prefs file, existing `paste_hidden_user_palette.json` custom colors migrate into the new prefs file; old file is never written again | Lazy migration: check prefs path non-existence then read old path; `USER_PALETTE_PATH` already defined in `constants.py` |
| PREFS-03 | When plugin is disabled, `copy_hidden()`, `cut_hidden()`, and `paste_hidden()` fall through to Nuke's default clipboard behavior silently | Early-return guard at top of each function in `paste_hidden.py`; fallback functions `copy_old()`, `cut_old()`, `paste_old()` already exist in same file |
| PREFS-04 | When `link_classes_paste_mode` is set to `passthrough`, copying a LINK_CLASSES node produces a plain Nuke copy with no anchor creation and no FQNN stamp | Guard on Path A inside `copy_hidden()` before `add_input_knob()` is called; when passthrough, skip the node entirely and let `nuke.nodeCopy()` at end of function handle it |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `json` (stdlib) | Python 3.x | Read/write prefs JSON | Already used in `colors.py`; no external dependencies needed |
| `os` (stdlib) | Python 3.x | Path expansion, makedirs | Already used in `colors.py` and `constants.py` with same `~/.nuke/` pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `typing` (stdlib) | Python 3.x | Optional type hints | Use only if adding type hints; project currently uses none |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Module-level globals | Class singleton with `__new__` | Module globals are simpler, consistent with how `constants.py` already works; class singleton adds complexity with no benefit |
| JSON | `configparser` / `.ini` | JSON is already used in `load_user_palette()`; consistent serialization; supports lists for `custom_colors` natively |
| Eager validation on load | Schema library (jsonschema) | Silent-fallback-to-defaults is the locked decision; full schema validation is overkill here |

**Installation:** No new packages required — all stdlib.

## Architecture Patterns

### Recommended Project Structure
```
prefs.py               # NEW: module-level singleton, load/save
constants.py           # ADD: PREFS_PATH constant
colors.py              # MODIFY: remove load/save_user_palette; add custom_colors param to ColorPaletteDialog
paste_hidden.py        # MODIFY: gate copy_hidden, cut_hidden, paste_hidden on plugin_enabled; gate Path A on link_classes_paste_mode
anchor.py              # MODIFY: gate create_anchor, rename_anchor, select_anchor_and_create, select_anchor_and_navigate, navigate_back on plugin_enabled
labels.py              # MODIFY: gate create_large_label, create_medium_label, append_to_label on plugin_enabled
menu.py                # MODIFY: store menu item references; add enable/disable helper callable by Phase 7
```

### Pattern 1: Module-Level Singleton Load at Import Time

**What:** `prefs.py` declares module-level variables with defaults, then immediately loads from disk on first import, overwriting defaults with persisted values. File write happens only via explicit `save()` call.

**When to use:** When a value must be available globally across all modules from startup with no initialization ceremony.

**Example:**
```python
# prefs.py
import json
import os
from constants import USER_PALETTE_PATH

PREFS_PATH = os.path.expanduser('~/.nuke/paste_hidden_prefs.json')

# Defaults — overwritten by _load() below
plugin_enabled = True
link_classes_paste_mode = "create_link"
custom_colors = []

def _load():
    """Load prefs from disk at import time. Silent fallback to defaults on any error."""
    global plugin_enabled, link_classes_paste_mode, custom_colors
    if not os.path.exists(PREFS_PATH):
        _migrate_from_old_palette()
        return
    try:
        with open(PREFS_PATH) as fh:
            data = json.load(fh)
        if isinstance(data.get('plugin_enabled'), bool):
            plugin_enabled = data['plugin_enabled']
        if data.get('link_classes_paste_mode') in ('create_link', 'passthrough'):
            link_classes_paste_mode = data['link_classes_paste_mode']
        if isinstance(data.get('custom_colors'), list):
            custom_colors = [int(c) for c in data['custom_colors'] if isinstance(c, (int, float))]
    except (OSError, ValueError, json.JSONDecodeError):
        pass  # silent fallback to defaults

def _migrate_from_old_palette():
    """One-way migration: read old palette colors into custom_colors. Never writes old file."""
    global custom_colors
    try:
        with open(USER_PALETTE_PATH) as fh:
            data = json.load(fh)
        custom_colors = [int(c) for c in data if isinstance(c, (int, float))]
    except (OSError, ValueError, json.JSONDecodeError):
        custom_colors = []

def save():
    """Persist current prefs to disk. Called by Phase 7 PrefsDialog on accept."""
    os.makedirs(os.path.dirname(PREFS_PATH), exist_ok=True)
    with open(PREFS_PATH, 'w') as fh:
        json.dump({
            'plugin_enabled': plugin_enabled,
            'link_classes_paste_mode': link_classes_paste_mode,
            'custom_colors': custom_colors,
        }, fh)

_load()  # execute at import time
```

### Pattern 2: Early-Return Gate for plugin_enabled

**What:** Each public entry point in `paste_hidden.py`, `anchor.py`, and `labels.py` checks `prefs.plugin_enabled` at the top and falls through to Nuke's default behavior (for clipboard functions) or silently returns (for anchor/label operations).

**When to use:** When disabling the plugin must be a complete and transparent no-op from the user's perspective.

**Example — paste_hidden.py:**
```python
import prefs

def copy_hidden(cut=False):
    if not prefs.plugin_enabled:
        nuke.nodeCopy(nukescripts.cut_paste_file())
        return
    # ... existing logic ...

def cut_hidden():
    if not prefs.plugin_enabled:
        selected_nodes = nuke.selectedNodes()
        nuke.nodeCopy(nukescripts.cut_paste_file())
        for node in selected_nodes:
            nuke.delete(node)
        return
    # ... existing logic ...

def paste_hidden():
    if not prefs.plugin_enabled:
        return nuke.nodePaste(nukescripts.cut_paste_file())
    # ... existing logic ...
```

**Example — anchor.py / labels.py:**
```python
import prefs

def create_anchor():
    if not prefs.plugin_enabled:
        return
    # ... existing logic ...
```

### Pattern 3: link_classes_paste_mode Gate in copy_hidden Path A

**What:** Inside `copy_hidden()`, Path A (LINK_SOURCE_CLASSES) checks `prefs.link_classes_paste_mode` before stamping. When `"passthrough"`, the node is skipped entirely — no `add_input_knob()`, no FQNN stamp. The node ends up in the clipboard via `nuke.nodeCopy()` at the end of the function as a plain copy.

**When to use:** When the gate should prevent stamping without affecting other copy paths (Dots, anchors).

**Example:**
```python
# Inside copy_hidden(), Path A section:
if node.Class() in LINK_SOURCE_CLASSES:
    if prefs.link_classes_paste_mode == 'passthrough':
        continue  # skip stamping; node copies plainly via nuke.nodeCopy() below
    if cut:
        # ... existing cut logic ...
```

### Pattern 4: Menu Item Enable/Disable

**What:** `menu.py` stores references to the menu item objects returned by `addCommand()`. A `set_plugin_enabled(state)` helper sets `.setEnabled()` on each stored reference. This helper is called by Phase 7 when the toggle changes.

**When to use:** When menu items must dynamically reflect plugin state without re-building the menu.

**Example:**
```python
# menu.py
_gated_menu_items = []  # items disabled when plugin_enabled=False

_item = anchors_menu.addCommand("Create Anchor", "anchor.create_anchor()")
_gated_menu_items.append(_item)

# ... repeat for all gated items ...

def set_anchors_menu_enabled(enabled):
    """Called by Phase 7 PrefsDialog after toggling plugin_enabled."""
    for item in _gated_menu_items:
        item.setEnabled(enabled)
```

**Important:** Nuke's `nuke.MenuItem.setEnabled()` exists in the Nuke Python API. The Preferences menu item must NOT be added to `_gated_menu_items` (Phase 7 adds it; Phase 6 prepares the infrastructure).

### Pattern 5: ColorPaletteDialog Constructor Injection

**What:** `colors.py` removes the `load_user_palette()` call from `_build_ui()`. The `ColorPaletteDialog.__init__()` gains a `custom_colors` parameter (default `None`). Callers pass `prefs.custom_colors` explicitly. This avoids `colors.py` importing `prefs.py`, which would create a circular import since `prefs.py` must load before `colors.py` is used but `colors.py` is imported by `anchor.py` which is imported early.

**Example:**
```python
# colors.py — modified signature
class ColorPaletteDialog(QtWidgets.QDialog):
    def __init__(self, initial_color=None, show_name_field=False,
                 initial_name="", custom_colors=None, parent=None):
        self._custom_colors = custom_colors if custom_colors is not None else []
        # ...

    def _build_ui(self, show_name_field, initial_name):
        # ...
        # OLD: user_palette_colors = load_user_palette()
        # NEW: user_palette_colors = self._custom_colors
        user_palette_colors = self._custom_colors
        # ...
```

**Callers in anchor.py** pass `custom_colors=prefs.custom_colors`:
```python
import prefs
dialog = ColorPaletteDialog(
    initial_color=int(pre_color),
    show_name_field=True,
    initial_name=suggested,
    custom_colors=prefs.custom_colors,
)
```

### Anti-Patterns to Avoid

- **Importing prefs from colors.py:** Circular import risk. `colors.py` must never `import prefs`. Use constructor injection instead.
- **Writing prefs file on every change:** `save()` should only be called explicitly (by Phase 7 on dialog accept). `_load()` is called once at import; module-level variables are mutated in memory during the session.
- **Using `setEnabled()` on an anonymous return value:** `addCommand()` must be called with the return value captured, or `setEnabled()` cannot be called later. If `addCommand()` returns `None` in a particular Nuke version, add a `None` guard before appending to `_gated_menu_items`.
- **Checking `plugin_enabled` in `paste_old()` / `cut_old()` / `copy_old()`:** These are the explicit fallback "old" commands exposed in the menu; they should always execute regardless of `plugin_enabled`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON read/write with error handling | Custom file format parser | `json.load()` + `(OSError, ValueError, json.JSONDecodeError)` catch | Edge cases: file locked, partial write, BOM, encoding errors — stdlib handles all |
| Path to `~/.nuke/` | Hardcoded path string | `os.path.expanduser('~/.nuke/...')` | Already the established pattern in `constants.py`; works on all platforms Nuke supports |
| Ensuring `~/.nuke/` dir exists on write | Checking `os.path.exists()` manually | `os.makedirs(..., exist_ok=True)` | Atomic, race-condition-safe; same pattern used in `colors.py:save_user_palette()` |

**Key insight:** All infrastructure patterns are already present in the codebase. This phase is primarily wiring existing patterns together, not introducing new technology.

## Common Pitfalls

### Pitfall 1: Circular Import Between prefs.py and colors.py

**What goes wrong:** If `colors.py` imports `prefs` to access `custom_colors`, and `anchor.py` imports both `colors` and `prefs`, Python's module import system may produce partial initialization or `ImportError` depending on import order.

**Why it happens:** `anchor.py` imports `colors` at module level (line 29: `from colors import ColorPaletteDialog`). If `colors.py` imports `prefs`, and `prefs.py` were to import anything that transitively imports `anchor`, the cycle is complete.

**How to avoid:** Pass `custom_colors` via the `ColorPaletteDialog` constructor parameter. `colors.py` never imports `prefs.py`. This is already a locked decision.

**Warning signs:** `ImportError: cannot import name 'X' from partially initialized module` at Nuke startup.

### Pitfall 2: nuke.MenuItem.setEnabled() Returns None (no-op guard needed)

**What goes wrong:** In some Nuke versions or menu contexts, `addCommand()` can return `None` if the menu item was not registered (e.g. duplicate command name, or called before the menu exists). Calling `None.setEnabled(False)` raises `AttributeError`.

**Why it happens:** Nuke's menu API is not fully documented; return values are version-dependent.

**How to avoid:** Guard with `if item is not None` before appending to `_gated_menu_items`, or check before calling `setEnabled()`. Write `set_anchors_menu_enabled()` to be `None`-safe.

**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'setEnabled'` in Nuke script editor.

### Pitfall 3: link_classes_paste_mode Gate Placed in paste_hidden() Instead of copy_hidden()

**What goes wrong:** If the gate is placed in `paste_hidden()`, a node copied with passthrough mode disabled could still have a FQNN stamp from a prior copy. Placing the gate at paste time means re-pasting from the clipboard file would bypass the gate.

**Why it happens:** Intuitive reading of "paste mode" suggests the gate belongs in paste, but the stamp is written during copy.

**How to avoid:** Gate is in `copy_hidden()` Path A, before `add_input_knob()` is called. This is the locked decision.

**Warning signs:** Nodes pasted from saved clipboard files getting unexpected link-replacement behavior when `passthrough` mode was toggled after the original copy.

### Pitfall 4: save() Called Without Prior Load — Overwrites Prefs with Defaults

**What goes wrong:** If `save()` is called before `_load()` has run (or if `_load()` silently failed), all values are defaults and any existing prefs are overwritten.

**Why it happens:** `_load()` is called at bottom of `prefs.py` module; if the module is somehow partially initialized, defaults persist.

**How to avoid:** `_load()` is the last statement in `prefs.py` so it runs at import time. `save()` should only be called by Phase 7 on explicit user action (dialog accept), not during startup or import.

**Warning signs:** Prefs file always contains defaults after Nuke restart even though user made changes.

### Pitfall 5: Old Palette File Written After Migration

**What goes wrong:** If `colors.py:save_user_palette()` is not removed and some code path still calls it, the old palette file continues to be written. Migration result is then overwritten on next startup.

**Why it happens:** Callers of `save_user_palette()` might be missed when refactoring.

**How to avoid:** Remove `save_user_palette()` from `colors.py`. Grep for all call sites before removing. Callers should write `prefs.custom_colors` directly and call `prefs.save()`.

**Warning signs:** `paste_hidden_user_palette.json` modification timestamp updates after a session where only the new prefs flow should have run.

## Code Examples

Verified patterns from existing codebase:

### Existing JSON Load Pattern (from colors.py:load_user_palette)
```python
# Source: /workspace/colors.py lines 28-38
def load_user_palette():
    try:
        with open(USER_PALETTE_PATH) as file_handle:
            data = json.load(file_handle)
        return [int(c) for c in data if isinstance(c, (int, float))]
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return []
```
**Use in prefs.py:** Expand this pattern to handle a dict with multiple keys and per-key type validation.

### Existing Path Pattern (from constants.py)
```python
# Source: /workspace/constants.py line 31
USER_PALETTE_PATH = os.path.expanduser('~/.nuke/paste_hidden_user_palette.json')
```
**New constant to add in constants.py:**
```python
PREFS_PATH = os.path.expanduser('~/.nuke/paste_hidden_prefs.json')
```

### Existing makedirs Pattern (from colors.py:save_user_palette)
```python
# Source: /workspace/colors.py lines 41-44
def save_user_palette(colors):
    os.makedirs(os.path.dirname(USER_PALETTE_PATH), exist_ok=True)
    with open(USER_PALETTE_PATH, 'w') as file_handle:
        json.dump(colors, file_handle)
```
**Use in prefs.save():** Same pattern, writing a dict instead of a list.

### Existing Nuke Default Clipboard Functions (from paste_hidden.py)
```python
# Source: /workspace/paste_hidden.py lines 245-257
def copy_old():
    nuke.nodeCopy(nukescripts.cut_paste_file())

def cut_old():
    selected_nodes = nuke.selectedNodes()
    nuke.nodeCopy(nukescripts.cut_paste_file())
    for node in selected_nodes:
        nuke.delete(node)

def paste_old():
    nuke.nodePaste(nukescripts.cut_paste_file())
```
**Use in PREFS-03 gate:** The `plugin_enabled=False` fallback bodies for `copy_hidden`, `cut_hidden`, and `paste_hidden` replicate these exact bodies inline (or delegate to these functions directly — same effect, simpler).

### Existing Menu Item Registration (from menu.py)
```python
# Source: /workspace/menu.py lines 28-34
anchors_menu.addCommand("Create Anchor",       "anchor.create_anchor()")
anchors_menu.addCommand("Rename Anchor",       "anchor.rename_selected_anchor()")
# ...
```
**Modified pattern for Phase 6:**
```python
_create_anchor_item = anchors_menu.addCommand("Create Anchor", "anchor.create_anchor()")
_gated_menu_items.append(_create_anchor_item)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `paste_hidden_user_palette.json` flat color list | `paste_hidden_prefs.json` dict with multiple keys | Phase 6 | Old file becomes read-once-on-migration artifact; never written again |
| `load_user_palette()` / `save_user_palette()` in colors.py | `prefs.custom_colors` module variable; `prefs.save()` | Phase 6 | Centralized persistence; no split-brain state between palette and other prefs |
| No plugin on/off switch | `plugin_enabled` pref + menu gates | Phase 6 | Full pass-through to Nuke defaults when disabled |
| LINK_CLASSES always stamped | `link_classes_paste_mode` pref | Phase 6 | User can opt into plain Nuke copy behavior for Read/Camera nodes |

**Deprecated/outdated in this phase:**
- `colors.py:load_user_palette()` — removed; callers read `prefs.custom_colors`
- `colors.py:save_user_palette()` — removed; callers set `prefs.custom_colors` and call `prefs.save()`
- `constants.py:USER_PALETTE_PATH` — kept for migration read in `prefs.py`; no longer used as write target

## Open Questions

1. **Does `nuke.MenuItem.setEnabled()` exist in all target Nuke versions?**
   - What we know: The Nuke Python API exposes menu item objects; `setEnabled()` is documented in Nuke 13+.
   - What's unclear: Minimum Nuke version for this plugin; whether PySide2-era Nuke versions support it identically.
   - Recommendation: Add a `hasattr(item, 'setEnabled')` guard in `set_anchors_menu_enabled()`; log a warning if unavailable rather than crashing.

2. **Should `PREFS_PATH` be defined in `constants.py` or `prefs.py`?**
   - What we know: `USER_PALETTE_PATH` is in `constants.py`. `prefs.py` needs the path. Phase 7 may also need `PREFS_PATH`.
   - What's unclear: Whether Phase 7 needs to reference `PREFS_PATH` directly.
   - Recommendation: Define `PREFS_PATH` in `constants.py` consistent with `USER_PALETTE_PATH`. Import it into `prefs.py`.

3. **Should anchor.py gate `navigate_back()` on plugin_enabled?**
   - What we know: CONTEXT.md says "all anchor operations (Create Anchor, Alt+A, Alt+Z, labels) are silent no-ops" when disabled. Alt+Z is `navigate_back`.
   - What's unclear: Whether restoring a previously saved DAG position when plugin is disabled makes semantic sense.
   - Recommendation: Gate `navigate_back()` with early return. The back-position is only set by navigate-to-anchor (itself gated), so `_back_position` will be `None` when plugin is disabled anyway — the gate is a safety belt.

## Sources

### Primary (HIGH confidence)
- `/workspace/colors.py` — existing `load_user_palette()` / `save_user_palette()` / `ColorPaletteDialog` patterns directly inspected
- `/workspace/constants.py` — `USER_PALETTE_PATH` and project constant patterns directly inspected
- `/workspace/paste_hidden.py` — `copy_hidden()` Path A structure and existing `copy_old()` fallbacks directly inspected
- `/workspace/anchor.py` — all public entry points to gate directly inspected
- `/workspace/labels.py` — all public entry points to gate directly inspected
- `/workspace/menu.py` — `addCommand()` registration pattern directly inspected
- `/workspace/.planning/phases/06-preferences-infrastructure/06-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)
- Nuke Python API documentation: `nuke.MenuItem.setEnabled()` available in Nuke 13+; verified by project knowledge and community usage. Cannot be confirmed with Context7 (no Nuke API library available).

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pure stdlib, patterns already in codebase
- Architecture: HIGH — all patterns derived from existing code; decisions locked in CONTEXT.md
- Pitfalls: HIGH — circular import and gate placement derived from direct code inspection; menu item edge case is MEDIUM (version-dependent)

**Research date:** 2026-03-10
**Valid until:** Stable (60 days) — pure Python stdlib, no external library dependencies
