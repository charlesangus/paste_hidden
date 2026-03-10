# Phase 3: Anchor Color System - Research

**Researched:** 2026-03-07
**Domain:** PySide2/PySide6 Qt widgets, Nuke knob API, color propagation
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Color palette dialog (shared widget)**
A single reusable color palette dialog is used across three entry points: creation, rename, and the anchor node "Set Color" button. It is NOT a raw `nuke.getColor()` call — it is a custom Qt Panel widget.

- Layout: Grid of color swatches organized in rows and columns.
- Color sources (rows):
  1. Nuke node preferences colors — the built-in palette from Edit > Preferences > Colors (dynamic read at dialog open time)
  2. Unique backdrop colors found in the current Nuke script (dynamic scan at open time)
  3. User saved palette — an explicit JSON file of user-defined colors; includes add/remove capability
- Additional control: A "Custom Color..." button opens `nuke.getColor()` for arbitrary color selection.
- Keyboard navigation (vim-style hint system):
  - Press Tab to enter hint mode — all swatches illuminate their row/column addresses
  - Row and column addresses are shown as faint labels at the edges of the grid (like a table header/sidebar — subtle, not intrusive)
  - Press column key → that column highlights
  - Press row key → that cell highlights
  - Press Enter to confirm the highlighted color
  - Clicking a swatch directly also selects it without the hint system

**Creation dialog**
- Combined `nuke.Panel` with both name field and color palette in one dialog
- Title: "Create Anchor"
- Color pre-selected on open: derived color from `find_anchor_color()` logic
- On OK: creates anchor with the chosen name and chosen color (does not call `find_anchor_color()` again; uses the user's selection)

**Rename dialog**
- Combined `nuke.Panel` with both name field and color palette in one dialog
- Title: "Rename Anchor"
- Name pre-filled with current anchor display name
- Color pre-selected on open: current anchor `tile_color` value (read directly from knob)
- On OK: renames anchor and applies chosen color; propagates color to all Link nodes

**"Set Color" button on anchor node properties panel**
- Label: "Set Color"
- Added as a `PyScript_Knob` alongside the existing "Reconnect Child Links" and "Rename Anchor" buttons
- Opens the same color palette dialog (color-only, no name field)
- On confirm: sets anchor `tile_color` to chosen color; immediately propagates to all Link nodes referencing this anchor

**Color propagation**
- Triggered by: creation dialog OK, rename dialog OK, "Set Color" button confirm
- Scope: anchor's `tile_color` + `tile_color` of all Link nodes that reference that anchor (found via standard anchor lookup)
- Propagation is synchronous (immediate, not deferred)
- NOT triggered by: direct manual edits to `tile_color` knob in Properties (only our pickers propagate)

**tabtabtab anchor picker color display**
- `get_color()` in `AnchorPlugin` reads `anchor['tile_color'].value()` directly
- Does NOT call `find_anchor_color()` (which re-runs backdrop/input logic)

**Dot anchor colors**
- Excluded from this system entirely
- Link Dots: fixed default purple (ANCHOR_DEFAULT_COLOR)
- Local Dots: fixed burnt orange (LOCAL_DOT_COLOR)
- No color picker button on Dot anchors
- No propagation for Dot types

**User saved palette storage**
- Stored as a JSON file alongside the plugin (e.g., `user_palette.json` in the plugin directory, or in a standard user preferences location)
- Claude decides exact path — somewhere persistent and user-writable
- Supports explicit add (from "Custom Color..." result) and remove

### Claude's Discretion

- Exact path for `user_palette.json`

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COLOR-01 | Tabtabtab picker reads anchor's actual `tile_color` knob value at invocation time (not re-derived from backdrop/input logic) | One-line change: replace `find_anchor_color(menuobj)` with `menuobj['tile_color'].value()` in both `AnchorPlugin.get_color()` and `AnchorNavigatePlugin.get_color()` in anchor.py |
| COLOR-02 | Anchor creation dialog includes a color picker | Replace `nuke.getInput()` in `create_anchor()` with combined name+color panel; pass chosen color to `create_anchor_named()` |
| COLOR-03 | Anchor rename dialog includes a color picker | Replace `nuke.getInput()` in `rename_anchor()` with combined name+color panel; call `propagate_anchor_color()` on save |
| COLOR-04 | Anchor node has a color picker button/knob in its properties panel | Add `PyScript_Knob("set_anchor_color", "Set Color", ...)` via new `add_set_color_anchor_knob()` function following existing pattern |
| COLOR-05 | When anchor color is changed via our color picker, all linked nodes update their color to match | New `propagate_anchor_color(anchor_node, color)` helper: sets anchor tile_color, iterates `get_links_for_anchor()`, sets each link's tile_color |
</phase_requirements>

## Summary

This phase adds an explicit color management system for anchor nodes. The core work has three parts: (1) a standalone reusable Qt widget (the color palette dialog) that is new to the codebase, (2) surgery on `create_anchor()` and `rename_anchor()` to replace simple `nuke.getInput()` calls with the new combined panel, and (3) a new `propagate_anchor_color()` helper plus a "Set Color" knob button added to anchor nodes at creation time.

The codebase already has all the infrastructure needed: `get_links_for_anchor()` returns all link nodes for an anchor, `PyScript_Knob` is the established pattern for anchor utility buttons, `add_reconnect_anchor_knob()` / `add_rename_anchor_knob()` are the exact templates for the new "Set Color" button, and the PySide2/PySide6 detection guard is already established. The color palette widget is the only genuinely new code surface.

The `nuke.Panel` approach used in `_offer_make_dot_anchor()` is the right model for modal dialogs, but the color palette grid requires a custom `QtWidgets.QDialog` subclass — `nuke.Panel` only supports built-in knob types (text fields, pulldowns, etc.) and cannot host arbitrary Qt layouts. The color palette grid must be a separate Qt widget, shown modally from within `create_anchor()` / `rename_anchor()` / the "Set Color" knob script.

**Primary recommendation:** Implement the color palette dialog as a standalone `QtWidgets.QDialog` subclass (following the tabtabtab pattern), place it in a new `colors.py` module, and wire it into `anchor.py` via import. This keeps `anchor.py` from growing unwieldy and makes the widget independently testable.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 / PySide2 | Already in project | Qt GUI widgets for color palette dialog | Project already uses PySide6≥Nuke16, PySide2 otherwise; same guard applies |
| `json` (stdlib) | stdlib | User palette persistence | Already used by tabtabtab for weights; zero new dependency |
| `nuke` | Nuke runtime | `nuke.getColor()`, `nuke.toNode("preferences")`, knob access | Already in every module |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `os.path.expanduser` | stdlib | Resolve `~/.nuke/` path for user palette | For user-writable location outside plugin dir |
| `QtWidgets.QDialog` | PySide2/PySide6 | Color palette dialog base class | Modal dialog that blocks until user confirms or cancels |
| `QtWidgets.QGridLayout` | PySide2/PySide6 | Swatch grid | Lays out N×M color buttons |
| `QtWidgets.QPushButton` | PySide2/PySide6 | Individual swatches + "Custom Color..." button | Clickable colored cells |
| `QtGui.QColor` | PySide2/PySide6 | Color conversion for swatch painting | Convert 0xRRGGBBAA int to RGB for display |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `QtWidgets.QDialog` subclass | `nuke.Panel` | `nuke.Panel` cannot host arbitrary Qt layouts; only supports built-in knob types (addSingleLineInput, addEnumerationPulldown, etc.) — cannot render a color swatch grid |
| Separate `colors.py` module | Embed in `anchor.py` | `anchor.py` is already 464 lines; a ~200-line widget class makes it 650+ lines and conflates UI with orchestration |
| `~/.nuke/` for user palette | Plugin directory | `~/.nuke/` is the established Nuke user preferences location (tabtabtab weights already use `~/.nuke/`); plugin directory may be read-only in some installations |

**Installation:** No new packages required. All dependencies are already available in the Nuke Python environment.

## Architecture Patterns

### Recommended Project Structure

```
anchor.py          # Modified: create_anchor(), rename_anchor(), add_set_color_anchor_knob(),
                   #           propagate_anchor_color(), AnchorPlugin.get_color() (reads tile_color directly)
colors.py          # New: ColorPaletteDialog, load_user_palette(), save_user_palette()
constants.py       # Modified: add ANCHOR_SET_COLOR_KNOB_NAME, USER_PALETTE_PATH
tests/
└── test_anchor_color_system.py   # New: unit tests for color propagation + palette loading
```

### Pattern 1: PyScript_Knob for "Set Color" Button

**What:** The existing `add_reconnect_anchor_knob()` / `add_rename_anchor_knob()` pattern, copied exactly for "Set Color".
**When to use:** Any anchor utility button added to the node's Properties panel.

```python
# In anchor.py — follows established pattern exactly
ANCHOR_SET_COLOR_KNOB_NAME = "set_anchor_color"  # in constants.py

def add_set_color_anchor_knob(node):
    if ANCHOR_SET_COLOR_KNOB_NAME in node.knobs():
        return
    knob = nuke.PyScript_Knob(ANCHOR_SET_COLOR_KNOB_NAME, "Set Color",
        """import anchor
anchor.set_anchor_color(nuke.thisNode())""")
    node.addKnob(knob)
```

The `set_anchor_color(anchor_node)` function opens the color palette dialog (color-only mode) and calls `propagate_anchor_color()` on confirm. This knob script string runs in the Nuke Python environment where `nuke.thisNode()` is defined, matching the exact pattern of the existing knobs.

### Pattern 2: Color Propagation Helper

**What:** Centralized helper that sets the anchor's tile_color and iterates all link nodes.
**When to use:** Called from creation OK, rename OK, and "Set Color" confirm.

```python
# In anchor.py
def propagate_anchor_color(anchor_node, color_int):
    """Set anchor tile_color to color_int and propagate to all Link nodes."""
    anchor_node['tile_color'].setValue(color_int)
    for link_node in get_links_for_anchor(anchor_node):
        link_node['tile_color'].setValue(color_int)
```

`get_links_for_anchor()` already exists in `anchor.py` and returns all link nodes whose `KNOB_NAME` value matches the anchor's FQNN. This is the complete implementation of COLOR-05.

### Pattern 3: tabtabtab get_color() Fix (COLOR-01)

**What:** One-line change in each of `AnchorPlugin.get_color()` and `AnchorNavigatePlugin.get_color()`.

```python
# Before (current):
def get_color(self, menuobj):
    color_int = find_anchor_color(menuobj)  # re-runs backdrop/input logic

# After:
def get_color(self, menuobj):
    color_int = menuobj['tile_color'].value()  # reads what was actually set
```

The color packing/unpacking logic (shift by 24/16/8, mask with 0xFF) stays identical. Both `AnchorPlugin` and `AnchorNavigatePlugin` have this pattern and both need the same fix.

### Pattern 4: ColorPaletteDialog Qt Widget

**What:** A `QtWidgets.QDialog` subclass that displays a grid of color swatches and returns the selected color as a 0xRRGGBBAA integer, or `None` on cancel.
**When to use:** Opened by `create_anchor()`, `rename_anchor()`, and `set_anchor_color()`.

Key design points:
- Constructor takes `initial_color` (int, 0xRRGGBBAA) and `show_name_field` (bool) — this single class serves all three entry points
- Three swatch row groups: Nuke prefs colors, backdrop colors, user saved palette
- "Custom Color..." button calls `nuke.getColor()` and returns its result
- Keyboard hint mode: `keyPressEvent` intercepts Tab to toggle hint mode; subsequent key presses in hint mode select column then row
- `exec_()` blocks until user accepts or cancels; returns `QtWidgets.QDialog.Accepted` / `Rejected`
- Accepted: `.selected_color` attribute holds the int; `.chosen_name` holds the name string (when `show_name_field=True`)

```python
# In colors.py
class ColorPaletteDialog(QtWidgets.QDialog):
    def __init__(self, initial_color=None, show_name_field=False,
                 initial_name="", parent=None):
        super().__init__(parent)
        # ... build grid layout, swatch buttons, optional name field ...

    def selected_color_int(self):
        """Return selected color as 0xRRGGBBAA int, or None."""
        ...
```

### Pattern 5: Nuke Preferences Color Reading

**What:** Reading the node color palette from `nuke.toNode("preferences")` — same approach as `find_node_default_color()` in `link.py`.

```python
# In colors.py, for the first row of swatches
def _get_nuke_pref_colors():
    """Return list of color ints from Nuke's Edit > Preferences > Colors."""
    prefs = nuke.toNode("preferences")
    if prefs is None:
        return []
    colors = []
    for knob_name in prefs.knobs():
        if knob_name.startswith("NodeColourChoice"):
            val = prefs[knob_name].value()
            if val and val != 0:
                colors.append(int(val))
    return colors
```

The `NodeColourSlot*` / `NodeColourChoice*` knob pattern is already proven in `link.py`'s `find_node_default_color()`. The same knob names apply here.

### Pattern 6: Backdrop Color Scanning

**What:** Iterating `nuke.allNodes('BackdropNode')` and collecting unique tile_color values — same pattern used in `find_smallest_containing_backdrop()`.

```python
def _get_script_backdrop_colors():
    """Return list of unique backdrop tile_color ints from the current script."""
    seen = set()
    colors = []
    for bd in nuke.allNodes('BackdropNode'):
        color = bd['tile_color'].value()
        if color and color not in seen:
            seen.add(color)
            colors.append(color)
    return colors
```

### Pattern 7: User Palette JSON

**What:** Simple JSON file of color ints, read/written with stdlib `json`. No schema beyond a list of integers.

```python
# Recommended path (Claude's discretion): ~/.nuke/paste_hidden_user_palette.json
USER_PALETTE_PATH = os.path.expanduser('~/.nuke/paste_hidden_user_palette.json')

def load_user_palette():
    try:
        with open(USER_PALETTE_PATH) as file_handle:
            data = json.load(file_handle)
        return [int(c) for c in data if isinstance(c, (int, float))]
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return []

def save_user_palette(colors):
    os.makedirs(os.path.dirname(USER_PALETTE_PATH), exist_ok=True)
    with open(USER_PALETTE_PATH, 'w') as file_handle:
        json.dump(colors, file_handle)
```

The `~/.nuke/` prefix matches `tabtabtab`'s weights files (`~/.nuke/paste_hidden_anchor_weights.json`). Using the same `paste_hidden_` prefix keeps all plugin files together.

### Anti-Patterns to Avoid

- **Calling `find_anchor_color()` in tabtabtab:** The whole point of COLOR-01 is to stop doing this. After this phase, `find_anchor_color()` is only called during creation pre-selection (to pick a sensible starting color for the dialog).
- **Propagating color on direct `tile_color` knob edits:** Per the locked decisions, propagation only happens via our pickers. Do not add `knobChanged` callbacks that watch `tile_color`.
- **Adding "Set Color" button to Dot anchors:** Per the locked decisions, Dot anchor colors are fixed and excluded. The `add_set_color_anchor_knob()` function should guard on `node.Class() != 'Dot'`.
- **Three separate dialog implementations:** There is one `ColorPaletteDialog` class parameterized by `show_name_field`. The planner should create one task for the widget class, not separate tasks for creation vs rename vs "Set Color".
- **Using `nuke.Panel` for the color grid:** `nuke.Panel` supports `addSingleLineInput()`, `addEnumerationPulldown()`, etc. — not arbitrary `QGridLayout` children. The swatch grid requires a real `QDialog`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Arbitrary color picker (raw) | Custom color wheel | `nuke.getColor()` for the "Custom Color..." button | Nuke's built-in color picker handles all edge cases, matches Nuke's UI language |
| Color int ↔ RGB conversion | Bit-shift logic from scratch | The same logic already in `AnchorPlugin.get_color()` (shift 24/16/8, mask 0xFF) | Copy the existing, proven pattern |
| Link node enumeration | Custom graph traversal | `get_links_for_anchor(anchor_node)` already in `anchor.py` | Already correct; handles FQNN matching |
| Nuke prefs color reading | Parse preferences UI files | `nuke.toNode("preferences")` + `NodeColourSlot*`/`NodeColourChoice*` knob names | Already proven in `link.py` |

**Key insight:** The color int format used throughout the codebase is 0xRRGGBBAA (alpha in lowest byte). `nuke.getColor()` returns in the same format. `QtGui.QColor` takes 0-255 RGB components, so the conversion is: `r = (color_int >> 24) & 0xFF`, `g = (color_int >> 16) & 0xFF`, `b = (color_int >> 8) & 0xFF`. This pattern already exists in both `AnchorPlugin.get_color()` and `AnchorNavigatePlugin.get_color()`.

## Common Pitfalls

### Pitfall 1: nuke.Panel Cannot Host QGridLayout

**What goes wrong:** Attempting to embed the swatch grid as a `nuke.Panel` widget. The grid simply won't render; `nuke.Panel` only supports its own knob-type add methods.
**Why it happens:** `_offer_make_dot_anchor()` uses `nuke.Panel` successfully, leading to the assumption that all dialogs should use it.
**How to avoid:** Use `QtWidgets.QDialog` for any dialog that needs arbitrary layout. Use `nuke.Panel` only for simple text + pulldown dialogs (as in the existing code).
**Warning signs:** If you're trying to add a QWidget to a nuke.Panel, you're going the wrong way.

### Pitfall 2: PyScript_Knob Script String Must Use nuke.thisNode()

**What goes wrong:** The knob script string runs in a fresh Python context inside Nuke; local variables from the add function are not available.
**Why it happens:** The string is serialized to the .nk file and re-evaluated at button press time.
**How to avoid:** The knob script string must be self-contained, using `nuke.thisNode()` and `import anchor` — exactly as the existing `add_reconnect_anchor_knob()` and `add_rename_anchor_knob()` do. The "Set Color" button string will be:
```python
"""import anchor
anchor.set_anchor_color(nuke.thisNode())"""
```

### Pitfall 3: Dot Anchors Must Be Excluded from "Set Color" Button

**What goes wrong:** `add_set_color_anchor_knob()` called on a Dot anchor, giving it a color button that should be absent per design.
**Why it happens:** `create_anchor_named()` calls all three add-knob helpers; if "Set Color" is added to that call chain naively, Dot anchors get it too.
**How to avoid:** Dot anchors go through `mark_dot_as_anchor()` / `_offer_make_dot_anchor()`, not `create_anchor_named()`. Add the "Set Color" knob only in `create_anchor_named()` (which creates NoOp anchors). Do NOT add it in `mark_dot_as_anchor()`.
**Warning signs:** If `is_anchor(node) and node.Class() == 'Dot'` and the node has `set_anchor_color` in its knobs, something went wrong.

### Pitfall 4: Color Propagation Must Skip Dot Anchors

**What goes wrong:** `propagate_anchor_color()` called with a Dot anchor, which per design should have fixed color.
**Why it happens:** The "Set Color" button should not exist on Dot anchors, but defensive coding matters.
**How to avoid:** Guard `propagate_anchor_color()` with an early return if `anchor_node.Class() == 'Dot'`, or add the guard in `set_anchor_color()` before calling it.

### Pitfall 5: `nuke.getColor()` Returns 0 on Cancel

**What goes wrong:** User clicks Cancel in the native color picker; `nuke.getColor()` returns `0` rather than raising or returning `None`.
**Why it happens:** Nuke API convention — 0 means no color / cancelled.
**How to avoid:** After `result = nuke.getColor()`, check `if result == 0: return` (treat as cancel). Do not apply 0 as a color.
**Warning signs:** Anchors turning black (0x000000FF) after a user cancelled the custom color picker.

### Pitfall 6: Qt Module Guard Must Wrap the Dialog Class Definition

**What goes wrong:** `ColorPaletteDialog` class body references `QtWidgets.QDialog` at class definition time; if Qt failed to import, this raises `TypeError`.
**Why it happens:** The `try/except ImportError` guard at the top of `anchor.py` sets `QtWidgets = None`; using `None` as a base class fails.
**How to avoid:** In `colors.py`, use the same `try/except ImportError` guard. If `QtWidgets is None`, define `ColorPaletteDialog = None` (or skip the class body). In `anchor.py`, guard calls to the dialog with `if ColorPaletteDialog is None: return`. This mirrors how `select_anchor_and_create()` guards on `if QtWidgets is None: return`.

### Pitfall 7: KeyPressEvent in Hint Mode Must Not Conflict with Existing Qt Shortcuts

**What goes wrong:** The Tab key-to-hint-mode behavior fires in the color grid's key handler, but the dialog's parent Qt event loop also intercepts Tab for focus traversal.
**Why it happens:** Qt's default Tab behavior moves focus between widgets.
**How to avoid:** In the dialog's `keyPressEvent`, call `event.accept()` after handling Tab/column/row keys to stop propagation. Also set the dialog's `Qt.NoFocus` policy on the swatch buttons if needed to prevent tab focus from leaving the search-like input mode.

## Code Examples

Verified patterns from existing codebase:

### Color Int Unpacking (from anchor.py AnchorPlugin.get_color)
```python
# Source: /workspace/anchor.py lines 328-334
def get_color(self, menuobj):
    color_int = find_anchor_color(menuobj)  # 0xRRGGBBAA
    r = (color_int >> 24) & 0xFF
    g = (color_int >> 16) & 0xFF
    b = (color_int >> 8) & 0xFF
    color = QtGui.QColor(r, g, b)
    return (color, color)
```

### PyScript_Knob Button Pattern (from anchor.py)
```python
# Source: /workspace/anchor.py lines 76-79
knob = nuke.PyScript_Knob(ANCHOR_RECONNECT_KNOB_NAME, "Reconnect Child Links",
    """import anchor
anchor.reconnect_anchor_node(nuke.thisNode())""")
node.addKnob(knob)
```

### get_links_for_anchor (from anchor.py)
```python
# Source: /workspace/anchor.py lines 111-114
def get_links_for_anchor(anchor_node):
    """Return all link nodes in the current script that reference *anchor_node*."""
    fqnn = get_fully_qualified_node_name(anchor_node)
    return [node for node in nuke.allNodes() if is_link(node) and node[KNOB_NAME].getText() == fqnn]
```

### Nuke Prefs Color Pattern (from link.py)
```python
# Source: /workspace/link.py lines 26-33
def find_node_default_color(node):
    prefs = nuke.toNode("preferences")
    node_colour_slots = [prefs[knob_name].value().split(' ') for knob_name in prefs.knobs() if knob_name.startswith("NodeColourSlot")]
    node_colour_choices = [prefs[knob_name].value() for knob_name in prefs.knobs() if knob_name.startswith("NodeColourChoice")]
    ...
```

### Qt/tabtabtab Stub Pattern for Tests (from tests/test_cross_script_paste.py)
```python
# Source: /workspace/tests/test_cross_script_paste.py lines 23-46
# Must be installed in sys.modules BEFORE importing any local modules
_pyside6_stub = _make_stub_qt_module('PySide6')
...
sys.modules['PySide6'] = _pyside6_stub
_tabtabtab_stub = types.ModuleType('tabtabtab')
_tabtabtab_stub.TabTabTabPlugin = MagicMock
sys.modules['tabtabtab'] = _tabtabtab_stub
```

### nuke.Panel for Simple Modal Dialogs (from anchor.py)
```python
# Source: /workspace/anchor.py lines 339-344
panel = nuke.Panel("Make Dot Anchor")
panel.addEnumerationPulldown("Label size", "Medium Large")
if not panel.show():
    return
size = panel.value("Label size")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `nuke.getInput()` for anchor name | Same (being replaced) | Phase 3 | Creation and rename dialogs get combined name+color UI |
| `find_anchor_color()` in tabtabtab | Direct `tile_color.value()` read | Phase 3 | Picker shows what user set, not re-derived color |

**Deprecated/outdated:**
- `find_anchor_color()` called from `get_color()` in tabtabtab plugins: replaced by direct `tile_color.value()` read (still used for creation pre-selection only)

## Open Questions

1. **How many columns in the swatch grid?**
   - What we know: The CONTEXT.md specifies a grid of rows and columns with keyboard navigation; row addresses match color source groups (prefs, backdrops, user palette)
   - What's unclear: The number of columns per row; whether all three groups always appear even when empty; minimum/maximum grid dimensions
   - Recommendation: Default to 8 columns per row (matches typical Nuke color palette width); hide empty rows entirely; this is a display detail the planner can decide during task breakdown

2. **What keyboard keys serve as row/column addresses in hint mode?**
   - What we know: Vim-EasyMotion style; column key then row key selects a cell
   - What's unclear: Whether to use a-z / A-Z, digits, or a mix; what happens when there are more swatches than available single-key addresses
   - Recommendation: Use lowercase letters a-z for columns, digits 1-9 + 0 for rows (10 rows max); limit user palette to keep addresses manageable; this is implementation detail for the task

3. **`create_anchor_named()` signature change for color parameter**
   - What we know: CONTEXT.md says `create_anchor_named()` "accepts color param; uses it instead of calling `find_anchor_color()` at node creation"
   - What's clear: Add `color=None` parameter; if `None`, fall back to `find_anchor_color()` (preserves backward compatibility for `create_anchor_silent()`)
   - Recommendation: `def create_anchor_named(name, input_node=None, color=None)` — fully backward compatible

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `unittest` (stdlib) |
| Config file | none — tests use `python3 -m unittest discover` |
| Quick run command | `python3 -m unittest tests.test_anchor_color_system -v` |
| Full suite command | `python3 -m unittest discover -s tests -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COLOR-01 | `AnchorPlugin.get_color()` reads `tile_color.value()` not `find_anchor_color()` | unit | `python3 -m unittest tests.test_anchor_color_system.TestAnchorPickerColorReadsFromKnob -v` | ❌ Wave 0 |
| COLOR-01 | `AnchorNavigatePlugin.get_color()` same fix | unit | `python3 -m unittest tests.test_anchor_color_system.TestAnchorNavigatePickerColorReadsFromKnob -v` | ❌ Wave 0 |
| COLOR-02 | `create_anchor_named()` accepts and applies explicit color param | unit | `python3 -m unittest tests.test_anchor_color_system.TestCreateAnchorNamedColorParam -v` | ❌ Wave 0 |
| COLOR-03 | `rename_anchor_to()` / `rename_anchor()` propagates color to links | unit | `python3 -m unittest tests.test_anchor_color_system.TestRenameAnchorColorPropagation -v` | ❌ Wave 0 |
| COLOR-04 | `add_set_color_anchor_knob()` adds knob; not added to Dot anchors | unit | `python3 -m unittest tests.test_anchor_color_system.TestSetColorKnob -v` | ❌ Wave 0 |
| COLOR-05 | `propagate_anchor_color()` sets anchor + all link tile_colors | unit | `python3 -m unittest tests.test_anchor_color_system.TestPropagateAnchorColor -v` | ❌ Wave 0 |
| COLOR-05 | `propagate_anchor_color()` skips Dot anchors | unit | `python3 -m unittest tests.test_anchor_color_system.TestPropagateAnchorColorSkipsDot -v` | ❌ Wave 0 |

Note: The `ColorPaletteDialog` Qt widget itself cannot be unit tested offline (requires a running Qt event loop and Nuke environment). Its behavior is validated via integration: the logic functions it calls (`_get_nuke_pref_colors`, `_get_script_backdrop_colors`, `load_user_palette`, `save_user_palette`) can be unit tested independently with mocked `nuke` module.

### Sampling Rate
- **Per task commit:** `python3 -m unittest discover -s tests -v`
- **Per wave merge:** `python3 -m unittest discover -s tests -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_anchor_color_system.py` — covers COLOR-01 through COLOR-05 (all unit-testable logic)
- [ ] Existing Qt/nuke stub pattern from `tests/test_cross_script_paste.py` must be replicated in new test file preamble

## Sources

### Primary (HIGH confidence)
- Direct codebase read — `/workspace/anchor.py` (464 lines), `/workspace/link.py`, `/workspace/constants.py`, `/workspace/tabtabtab.py`, `/workspace/tests/test_cross_script_paste.py` — all integration points, existing patterns, and test infrastructure confirmed by reading actual code
- `/workspace/.planning/phases/03-anchor-color-system/03-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)
- `nuke.Panel` limitations (cannot host QGridLayout): confirmed by reviewing the existing `nuke.Panel` usage in `_offer_make_dot_anchor()` which only uses `addEnumerationPulldown()` and `addSingleLineInput()`-style methods; no evidence of arbitrary Qt widget embedding
- `nuke.getColor()` returns 0 on cancel: well-established Nuke API behavior; consistent with how `tile_color.value()` returns 0 for unset colors throughout the codebase

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; everything is stdlib + existing Qt + nuke
- Architecture: HIGH — all patterns verified in existing codebase; COLOR-01 is a trivial 1-line fix; COLOR-05 uses existing `get_links_for_anchor()`; the new `colors.py` module is the only genuinely new surface
- Pitfalls: HIGH — PyScript_Knob string serialization and nuke.Panel limitations are verified by reading existing code; Qt guard pattern is verified; `nuke.getColor()` cancel behavior is verified by codebase convention

**Research date:** 2026-03-07
**Valid until:** Stable — no external dependencies; valid until Nuke Python API changes
