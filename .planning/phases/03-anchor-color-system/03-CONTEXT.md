# Phase 3: Anchor Color System - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Anchor color is explicitly set by the user via a color palette dialog — at creation time, at rename time, and via a button on the anchor node's properties panel. Color propagates to all Link nodes referencing the anchor when changed through any of our pickers. The tabtabtab anchor picker reads tile_color directly instead of re-deriving it. Dot anchor colors are fixed by type and excluded from this system.

</domain>

<decisions>
## Implementation Decisions

### Color palette dialog (shared widget)

A single reusable color palette dialog is used across three entry points: creation, rename, and the anchor node "Set Color" button. It is NOT a raw `nuke.getColor()` call — it is a custom Qt Panel widget.

**Layout:** Grid of color swatches organized in rows and columns.

**Color sources (rows):**
1. Nuke node preferences colors — the built-in palette from Edit > Preferences > Colors (dynamic read at dialog open time)
2. Unique backdrop colors found in the current Nuke script (dynamic scan at open time)
3. User saved palette — an explicit JSON file of user-defined colors; includes add/remove capability

**Additional control:** A "Custom Color..." button opens `nuke.getColor()` for arbitrary color selection.

**Keyboard navigation (vim-style hint system):**
- Press **Tab** to enter hint mode — all swatches illuminate their row/column addresses
- Row and column addresses are shown as faint labels at the edges of the grid (like a table header/sidebar — subtle, not intrusive)
- Press **column** key → that column highlights
- Press **row** key → that cell highlights
- Press **Enter** to confirm the highlighted color
- Clicking a swatch directly also selects it without the hint system

### Creation dialog

- Combined `nuke.Panel` with both **name field** and **color palette** in one dialog
- Title: "Create Anchor"
- Color pre-selected on open: derived color from `find_anchor_color()` logic (backdrop if Read node input, input node color otherwise, default purple as fallback)
- On OK: creates anchor with the chosen name and chosen color (does not call `find_anchor_color()` again; uses the user's selection)

### Rename dialog

- Combined `nuke.Panel` with both **name field** and **color palette** in one dialog
- Title: "Rename Anchor"
- Name pre-filled with current anchor display name
- Color pre-selected on open: current anchor `tile_color` value (read directly from knob)
- On OK: renames anchor and applies chosen color; propagates color to all Link nodes

### "Set Color" button on anchor node properties panel

- Label: **"Set Color"**
- Added as a `PyScript_Knob` alongside the existing "Reconnect Child Links" and "Rename Anchor" buttons
- Opens the same color palette dialog (color-only, no name field)
- On confirm: sets anchor `tile_color` to chosen color; immediately propagates to all Link nodes referencing this anchor

### Color propagation

- Triggered by: creation dialog OK, rename dialog OK, "Set Color" button confirm
- Scope: anchor's `tile_color` + `tile_color` of all Link nodes that reference that anchor (found via standard anchor lookup)
- Propagation is synchronous (immediate, not deferred)
- NOT triggered by: direct manual edits to `tile_color` knob in Properties (only our pickers propagate)

### tabtabtab anchor picker color display

- `get_color()` in `AnchorPlugin` reads `anchor['tile_color'].value()` directly
- Does NOT call `find_anchor_color()` (which re-runs backdrop/input logic)
- What the user set is what the picker shows

### Dot anchor colors

- **Excluded from this system entirely**
- Link Dots: fixed default purple (`ANCHOR_DEFAULT_COLOR`)
- Local Dots: fixed burnt orange (`LOCAL_DOT_COLOR`)
- No color picker button on Dot anchors
- No propagation for Dot types

### User saved palette storage

- Stored as a JSON file alongside the plugin (e.g., `user_palette.json` in the plugin directory, or in a standard user preferences location)
- Claude decides exact path — somewhere persistent and user-writable
- Supports explicit add (from "Custom Color..." result) and remove

</decisions>

<specifics>
## Specific Ideas

- The keyboard navigation feel is deliberately vim-EasyMotion / web-hinting style: Tab activates hint mode, two keystrokes pick the color, Enter confirms. Fast for power users.
- Faint row/column address labels at the grid edges (like a spreadsheet with row numbers and column letters at the sides) — not on the swatches themselves. Subtle.
- The color palette dialog is a reusable widget (not three separate implementations). Same class, different instantiation parameters (show name field or not, pre-selected color).

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `add_reconnect_anchor_knob(node)` / `add_rename_anchor_knob(node)` in `anchor.py` — established pattern for adding `PyScript_Knob` buttons to anchor nodes; "Set Color" button follows the same pattern
- `find_anchor_color(anchor)` in `anchor.py` — existing derivation logic; still used for creation pre-selection, but NOT for tabtabtab display (which reads tile_color directly)
- `AnchorPlugin.get_color()` in `anchor.py` — currently calls `find_anchor_color()`; needs to be changed to read `tile_color` directly
- `tabtabtab.py` — existing Qt dialog infrastructure; custom color palette dialog can be a new `TabTabTabPlugin` subclass or a standalone Qt widget following the same patterns
- `ANCHOR_DEFAULT_COLOR`, `LOCAL_DOT_COLOR` in `constants.py` — fixed Dot colors; no changes needed for Dot color behavior

### Established Patterns
- `nuke.Panel` used in `anchor.py` (Make Dot Anchor dialog) — model for combined Panels
- PySide2/PySide6 detection at module load with `try/except ImportError` — color palette widget must follow the same guard
- `PyScript_Knob` pattern for anchor utility buttons — "Set Color" follows this exactly
- No explicit type hints in codebase — don't add them

### Integration Points
- `create_anchor()` in `anchor.py`: replace `nuke.getInput()` with combined Panel
- `rename_anchor()` in `anchor.py`: replace `nuke.getInput()` with combined Panel
- `create_anchor_named()` in `anchor.py`: accepts color param; uses it instead of calling `find_anchor_color()` at node creation
- `rename_anchor_to()` in `anchor.py`: apply color + propagate after rename
- New helper needed: `propagate_anchor_color(anchor_node, color)` — sets anchor tile_color + all Link node tile_colors
- New widget: color palette dialog (likely in `anchor.py` or a new `colors.py` module)
- `menu.py` — no new menu items needed (color flows through existing anchor creation/rename shortcuts)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-anchor-color-system*
*Context gathered: 2026-03-07*
