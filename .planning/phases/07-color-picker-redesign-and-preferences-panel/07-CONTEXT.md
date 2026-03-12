# Phase 7: Color Picker Redesign and Preferences Panel - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Redesign `ColorPaletteDialog` to support click-to-select (no immediate close), Enter/OK to confirm, custom color staging in memory, swatch reordering (custom → backdrop → Nuke defaults), and initial color pre-highlight. Build a new `PrefsDialog` accessible from the Anchors menu with plugin enable/disable, LINK_CLASSES paste mode toggle, and custom color management (add/remove/edit).

</domain>

<decisions>
## Implementation Decisions

### Color picker: click-to-select behavior
- Clicking a swatch highlights it (white border) without closing the dialog
- Enter key OR OK button confirms the selection and closes
- OK button sits beside Cancel (not above — horizontal button row)
- Pre-selected `initial_color` opens with white border highlight

### Color picker: "Custom Color..." button
- Opens `nuke.getColor()` as before; if result is non-zero, the color is staged in memory
- A new swatch is dynamically appended to the custom colors group in the grid
- The new swatch is auto-highlighted (selected); dialog stays open
- User must still press Enter or OK to confirm — Cancel discards the staged color
- This is consistent with PICKER-01: clicking never closes, only Enter/OK does

### Color picker: swatch group ordering and separation
- Order: custom colors → backdrop colors → Nuke defaults (reversed from current)
- Groups separated by a blank row gap (no labels, no separator lines)
- Empty groups are omitted entirely (current `if group` filter preserved)

### Preferences dialog: controls
- Plugin toggle: `QCheckBox` labeled "Enable paste_hidden plugin"
- LINK_CLASSES mode: `QCheckBox` labeled "Input nodes paste as links"
  - Checked = `create_link` (default), Unchecked = `passthrough`
- Dialog buttons: OK (saves + closes) and Cancel (discards) — horizontal, bottom-right
- On OK: write all three prefs, call `prefs.save()`, call `menu.set_anchors_menu_enabled(prefs.plugin_enabled)`

### Preferences dialog: custom color management
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

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `colors.py:ColorPaletteDialog` — the dialog being redesigned; receives `custom_colors` via constructor injection already; `_on_swatch_clicked` currently calls `self.accept()` — this must change to highlight-only
- `colors.py:_color_int_to_rgb()` — utility for swatch styling; reuse in PrefsDialog swatch grid
- `colors.py:_get_nuke_pref_colors()`, `_get_script_backdrop_colors()` — group collection helpers; reuse in redesigned `_build_ui()`
- `prefs.py` — singleton with `plugin_enabled`, `link_classes_paste_mode`, `custom_colors`; `save()` called by PrefsDialog on OK
- `menu.py:set_anchors_menu_enabled()` — called by PrefsDialog after OK to apply `plugin_enabled` live
- `menu.py:anchors_menu` — the menu where a "Preferences" item must be added (ungated, always active)

### Established Patterns
- `QPushButton.setAutoDefault(False)` on all swatch buttons — Enter handled at dialog level (decided Phase 6)
- PySide2/PySide6 conditional guard in `colors.py` — PrefsDialog must follow the same guard pattern
- `keyPressEvent` in `ColorPaletteDialog` already handles Escape and Tab; Enter handling needs to be extended outside hint mode

### Integration Points
- `menu.py` — add Preferences command to `anchors_menu` (not in `_gated_menu_items`)
- `prefs.py:save()` — called on PrefsDialog accept
- `menu.py:set_anchors_menu_enabled()` — called on PrefsDialog accept with updated `prefs.plugin_enabled`

</code_context>

<specifics>
## Specific Ideas

- PrefsDialog layout sketch:
  ```
  ┌─────────────────────────────────────────┐
  │  paste_hidden Preferences               │
  ├─────────────────────────────────────────┤
  │  [✓] Enable paste_hidden plugin         │
  │  [✓] Input nodes paste as links         │
  │  ─────────────────────────────────────  │
  │  Custom Colors                          │
  │  ■ ■ ■ ■ ■  (wrapping swatch grid)      │
  │  [ Add ]  [ Edit ]  [ Remove ]          │
  │  ─────────────────────────────────────  │
  │                      [ OK ]  [ Cancel ] │
  └─────────────────────────────────────────┘
  ```
- Edit/Remove buttons are disabled (greyed) until a swatch is clicked to select it
- "Custom Color..." in the picker appends a new swatch to the custom group then auto-selects it

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-color-picker-redesign-and-preferences-panel*
*Context gathered: 2026-03-11*
