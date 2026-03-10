# Feature Research

**Domain:** Qt/PySide preferences panel and color picker dialog for a Nuke plugin
**Researched:** 2026-03-10
**Confidence:** HIGH (behavior derived from existing codebase + Qt documentation; no market competition)

---

## Context

This is a single-artist internal tool. "Table stakes" and "differentiators" are reframed relative
to user expectations for a tool panel in a professional DCC (Nuke), not a consumer product.
Features are scoped strictly to the v1.1 milestone: preferences panel and color picker redesign.
All v1.0 features (swatch grid, color propagation, anchor dialogs) are existing and not re-evaluated here.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features the artist expects. Missing any of these = the panel or dialog feels unfinished or
broken for professional use.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Preferences dialog accessible from menu | Standard DCC plugin UX; Nuke itself has a Preferences menu entry | LOW | Add menu item to existing Anchors menu in `menu.py` |
| Enable/disable plugin toggle (checkbox) | Without this, disabling requires editing `menu.py` manually — unacceptable workflow | LOW | Boolean flag; when disabled, Ctrl+C/X/V must fall back to native Nuke commands |
| Paste-mode toggle: link-creation vs plain copy | LINK_CLASSES currently hardcoded in `constants.py`; user expects runtime control | LOW | Two-state radio or checkbox; affects `copy_hidden()` Path A logic only |
| Preferences persist across Nuke sessions | A preferences panel that resets on restart is unusable | MEDIUM | Must write to a file; `~/.nuke/` is the conventional location; JSON is already used for USER_PALETTE_PATH |
| Custom color list with Add / Remove | The color palette is already persisted; UI to manage it is the missing piece | MEDIUM | Backed by existing `load_user_palette()` / `save_user_palette()` helpers |
| Color picker: click selects without closing | Current behavior closes on click; users expect to browse before committing | LOW | `_on_swatch_clicked` must set `_selected_color` without calling `self.accept()` |
| Color picker: Enter/Return key accepts | Standard modal dialog keyboard contract; any dialog that ignores Enter feels broken | LOW | `keyPressEvent` already exists; currently Enter only works inside hint mode — must work globally |
| Color picker: pre-selected swatch visually highlighted on open | Without a visible highlight, the current color is invisible after re-opening | LOW | Already partially implemented via border style; must survive the new deferred-accept flow |
| Color picker: OK/Accept button | With click no longer closing the dialog, an explicit accept path is mandatory | LOW | Standard `QDialogButtonBox` or simple OK button wired to `self.accept()` |

### Differentiators (What Makes This Better Than the Status Quo)

These are improvements beyond basic function. This is a single-user tool, so "differentiator"
means "noticeably better than the current workaround."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Custom color list with Edit (in-place rename/reorder) | Add/Remove alone leaves the list hard to curate; Edit gives control over ordering | MEDIUM | QListWidget with double-click edit or separate Edit button; color value re-entry via `nuke.getColor()` |
| Swatch order: custom colors first, then backdrop colors, then Nuke defaults | Custom colors are the most intentional; surfacing them first reduces scanning time | LOW | Reorder the `all_color_groups` list in `_build_ui`; custom slot already exists, just currently last |
| Default anchor color highlighted in picker on open | Without this, the artist cannot see what color is currently set when re-opening the picker | LOW | Already partially done; confirm it persists correctly after click-to-select re-renders swatches |
| Preferences panel: custom color management embedded | Placing color list management inside preferences (rather than a separate dialog) keeps the feature surface small | LOW | Reuse color list widget inside the preferences dialog |
| Preferences state readable by plugin at runtime without dialog being open | Plugin code must check enabled/paste-mode flags on every copy/paste invocation | MEDIUM | A module-level `load_prefs()` helper called at import or lazily per-operation; must not require the dialog to be open |

### Anti-Features (Commonly Considered, Better Avoided)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Using Nuke's built-in `preferences` node to store plugin settings | Seems "native" and avoids a separate file | Nuke's preferences node is version-specific (`preferences17.0.nk`), adds unversioned knobs to a shared namespace, and is fragile across Nuke version upgrades | JSON file in `~/.nuke/` — already used for USER_PALETTE_PATH; extend the same pattern |
| QSettings / uistate.ini for plugin prefs | Nuke itself uses `uistate.ini` for some panel state; could piggyback on it | `QSettings` with `uistate.ini` path is undocumented for plugin use and could collide with Foundry internals; format is INI not JSON, inconsistent with existing codebase | Dedicated `paste_hidden_prefs.json` alongside existing `paste_hidden_user_palette.json` |
| Combining preferences and color palette into a single JSON file | Fewer files | Makes the schema load/save harder to evolve independently; palette is already shipped as its own file | Keep separate files; palette path is already a constant (`USER_PALETTE_PATH`) |
| Full color editor (HSV sliders, hex input) inside the swatch picker | Some users like in-picker editing | The existing "Custom Color..." button already delegates to `nuke.getColor()` (Nuke's native full-color dialog); duplicating that adds complexity with no gain | Keep the "Custom Color..." button; it already handles the edge case |
| Preferences window as a docked Nuke panel (nukescripts.PythonPanel) | Looks "more native" | Docked panels have a persistent lifecycle that complicates state sync; preferences are infrequently accessed; a modal QDialog is simpler and correct | Modal `QDialog`; open from menu, close on OK/Cancel |
| Live preview of enable/disable toggle while panel is open | Instant feedback seems good | If the plugin disables itself while the preferences dialog is open, menu shortcuts are live-rewired mid-session; edge cases are hard to reason about | Apply all changes on OK/Accept only; Cancel discards |

---

## Feature Dependencies

```
[Preferences persist across sessions]
    └──requires──> [Prefs JSON load/save helpers]
                       └──requires──> [Defined prefs schema (enabled, paste_mode, custom_colors)]

[Enable/disable toggle]
    └──requires──> [Prefs JSON load/save helpers]
    └──requires──> [Plugin reads prefs flag at copy/paste invocation]

[Paste-mode toggle]
    └──requires──> [Prefs JSON load/save helpers]
    └──requires──> [copy_hidden() reads paste_mode flag before Path A logic]

[Custom color list UI (Add/Remove/Edit)]
    └──requires──> [Existing load_user_palette() / save_user_palette() in colors.py]
    └──enhances──> [Color picker swatch order: custom colors first]

[Color picker: click selects without closing]
    └──conflicts──> [Current _on_swatch_clicked calls self.accept()]

[Color picker: Enter accepts]
    └──requires──> [A currently-selected swatch state (not just _selected_color set at open)]

[Color picker: OK button]
    └──requires──> [Click-to-select without closing (otherwise OK is redundant)]

[Swatch order: custom first]
    └──requires──> [No structural change to _build_ui, only list reorder]
    └──enhances──> [Pre-selected color highlighting (custom colors are the most likely pre-selected)]
```

### Dependency Notes

- **Enable/disable toggle requires runtime flag reads:** `paste_hidden.py` functions `copy_hidden()`, `cut_hidden()`, `paste_hidden()` must each check a loaded prefs flag. This is a change to the hot path; it must be a fast dictionary lookup, not a file read per operation.
- **Click-to-select conflicts with current close-on-click:** The entire `_on_swatch_clicked` method must be refactored. This is the central behavioral change of the color picker redesign.
- **Custom color list in preferences depends on existing palette helpers:** `load_user_palette()` and `save_user_palette()` in `colors.py` are stable; the preferences panel simply needs to call them. No change to persistence logic required.
- **Paste-mode toggle depends on `copy_hidden()` reading a flag:** The flag controls whether Path A (link creation for LINK_SOURCE_CLASSES nodes) fires. The plain-copy fallback is already the behavior when `copy_hidden()` encounters a node without a matching anchor; the paste-mode toggle just needs to suppress the Path A branch entirely.

---

## MVP Definition

This is a subsequent milestone on a shipped plugin. "MVP" here means: minimum to make the
preferences panel and color picker redesign complete and releasable as v1.1.

### Launch With (v1.1)

- [ ] Preferences dialog accessible from the Anchors menu
- [ ] Enable/disable toggle — persisted, read at copy/paste invocation
- [ ] Paste-mode toggle (link-creation vs plain copy for LINK_SOURCE_CLASSES) — persisted
- [ ] Custom color list: Add and Remove — backed by existing palette helpers
- [ ] Preferences JSON load/save module (separate from palette file)
- [ ] Color picker: click selects swatch without closing dialog
- [ ] Color picker: Enter/Return accepts with currently selected color
- [ ] Color picker: OK button for explicit accept
- [ ] Color picker: swatch order reordered (custom first, then backdrop, then Nuke defaults)
- [ ] Color picker: pre-selected color highlight visible after click-to-select flow

### Add After Validation (v1.1+)

- [ ] Custom color list: Edit (replace color value via `nuke.getColor()`) — useful but not blocking
- [ ] Custom color list: drag-to-reorder — ergonomic improvement; requires more complex QListWidget setup

### Future Consideration (v2+)

- [ ] Full forward/back navigation history stack (NAV-03) — already tracked in PROJECT.md as v2 candidate
- [ ] Manual `tile_color` change propagation to links (Color-V2-01) — explicitly deferred by design

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Color picker: click-to-select without closing | HIGH | LOW | P1 |
| Color picker: Enter accepts | HIGH | LOW | P1 |
| Color picker: OK button | HIGH | LOW | P1 |
| Enable/disable toggle + persistence | HIGH | MEDIUM | P1 |
| Paste-mode toggle + persistence | HIGH | LOW | P1 |
| Prefs JSON load/save helpers | HIGH | LOW | P1 (unblocks all prefs features) |
| Custom color list Add/Remove in prefs | MEDIUM | MEDIUM | P1 |
| Swatch order: custom first | MEDIUM | LOW | P1 |
| Pre-selected highlight after click-to-select | MEDIUM | LOW | P1 |
| Custom color list Edit | LOW | LOW | P2 |
| Custom color list drag-to-reorder | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for v1.1 launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

There are no direct competitors — this is an internal single-artist plugin. The relevant
reference points are DCC industry norms and Qt standard dialog patterns.

| Feature | Qt Standard Pattern | Nuke Native Pattern | Our Approach |
|---------|---------------------|---------------------|--------------|
| Preferences dialog | Modal QDialog with OK/Cancel, apply-on-OK | Foundry uses a tabbed non-modal preferences window; plugins rarely use it | Modal QDialog; simpler, sufficient for small feature set |
| Color swatch picker | QColorDialog has a custom color section; click-and-close is not standard for palette pickers | Nuke's `nuke.getColor()` is a single call that returns one color and closes | Custom palette picker; click-selects, Enter/OK closes |
| Persisting plugin settings | QSettings (platform-aware) | ~/.nuke/*.nk knob files for Nuke-native prefs | JSON in ~/.nuke/; consistent with existing USER_PALETTE_PATH pattern |
| Custom color management | QColorDialog has a "Add to Custom Colors" button | None in Nuke natively | QListWidget with Add/Remove in prefs panel |

---

## Sources

- Existing codebase: `/workspace/colors.py` — current `ColorPaletteDialog` implementation (HIGH confidence)
- Existing codebase: `/workspace/constants.py` — `USER_PALETTE_PATH`, `LINK_SOURCE_CLASSES` (HIGH confidence)
- Existing codebase: `/workspace/paste_hidden.py` — `copy_hidden()` Path A/B logic (HIGH confidence)
- Existing codebase: `/workspace/PROJECT.md` — v1.1 target features and constraints (HIGH confidence)
- [QDialog documentation — Qt for Python](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QDialog.html) — modal dialog contract, accept/reject signals (HIGH confidence)
- [QListWidget — Qt for Python](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QListWidget.html) — add/remove/edit item patterns (HIGH confidence)
- [Foundry: Custom Panels in Nuke](https://learn.foundry.com/nuke/developers/111/pythondevguide/custom_panels.html) — plugin panel patterns (MEDIUM confidence)
- [Foundry: Preferences knob defaults (uistate.ini)](https://support.foundry.com/hc/en-us/articles/360006950439) — QSettings/uistate.ini risk (MEDIUM confidence)
- [Houdini Qt ColorPalette](https://www.sidefx.com/docs/houdini/hom/hou/qt/ColorPalette.html) — DCC color palette UX precedent: `colorAccepted` signal on deferred accept (MEDIUM confidence)

---

*Feature research for: paste_hidden v1.1 — preferences panel and color picker redesign*
*Researched: 2026-03-10*
