# Requirements: paste_hidden

**Defined:** 2026-03-03
**Core Value:** Copy and paste must reconnect predictably — anchors provide stable, navigable references; hidden inputs reconnect to their source without ceremony.

## v1 Requirements

### Copy-Paste Behavior

- [x] **PASTE-01**: When a LINK_CLASSES file node is copied, paste creates a Link node: pointing to the existing anchor if one exists, or pointing directly to the file node if no anchor exists (legacy fallback). When a hidden-input Dot whose input(0) is an anchor is copied, paste creates a Link node pointing to that anchor (cross-script capable).
- [x] **PASTE-03**: A hidden-input Dot whose input(0) is a non-anchor node reconnects to that source by identity on paste (same-script only); no anchor is created and no Link behavior applies
- [x] **PASTE-04**: A hidden-input Dot whose input(0) is a non-anchor node, pasted into a different script, is left disconnected silently (no reconnection attempt)

### Link Node Types

- [x] **LINK-01**: 2D stream nodes use PostageStamp as the link node class
- [x] **LINK-02**: Deep and 3D stream nodes (e.g. Camera) use NoOp as the link node class
- [x] **LINK-03**: Camera links no longer incorrectly produce PostageStamp nodes when pasted
- [x] **LINK-04**: Fallback: if stream-type detection is not simple and performant, all non-Dot links use NoOp

### Cross-Script Paste

- [x] **XSCRIPT-01**: Link nodes pasted into another script reconnect to an anchor of the same name in the destination script
- [x] **XSCRIPT-02**: Hidden-input Dot nodes pasted into another script do not reconnect (distinct from Link behavior)

### Anchor Navigation History

- [x] **NAV-01**: DAG position is saved when navigate-to-anchor (Alt+A) is invoked
- [x] **NAV-02**: A keyboard shortcut jumps the DAG view back to the saved position
- [ ] **NAV-03**: Full browser-style forward/back navigation history stack (stretch goal — deferred to v2)

### Anchor Color System

- [x] **COLOR-01**: Tabtabtab picker reads the anchor's actual `tile_color` knob value at invocation time (not re-derived from backdrop/input logic)
- [x] **COLOR-02**: Anchor creation dialog includes a color picker
- [x] **COLOR-03**: Anchor rename dialog includes a color picker
- [x] **COLOR-04**: Anchor node has a color picker button/knob in its properties panel
- [x] **COLOR-05**: When anchor color is changed via our color picker, all linked nodes update their color to match

### Anchor Find

- [x] **FIND-01**: Anchor navigation picker (Alt+A) includes labelled BackdropNodes as navigable targets alongside anchor nodes

## v1.1 Requirements

### Preferences Infrastructure

- [x] **PREFS-01**: Preferences are persisted to `~/.nuke/paste_hidden_prefs.json` with keys: `plugin_enabled`, `link_classes_paste_mode`, `custom_colors`
- [x] **PREFS-02**: On first run with no prefs file, existing `paste_hidden_user_palette.json` custom colors migrate into the new prefs file; old file is never written again
- [x] **PREFS-03**: When plugin is disabled, `copy_hidden()`, `cut_hidden()`, and `paste_hidden()` fall through to Nuke's default clipboard behavior silently
- [x] **PREFS-04**: When `link_classes_paste_mode` is set to `passthrough`, copying a LINK_CLASSES node (Read, Camera, etc.) produces a plain Nuke copy with no anchor creation and no FQNN stamp — identical to default Nuke copy behavior

### Preferences Panel

- [ ] **PANEL-01**: User can open a preferences dialog from the Anchors menu
- [ ] **PANEL-02**: User can toggle the plugin enabled/disabled in the preferences dialog; change persists across sessions
- [ ] **PANEL-03**: User can toggle LINK_CLASSES paste mode between "Create link" and "Paste copy" in the preferences dialog; change persists across sessions
- [ ] **PANEL-04**: User can view the list of saved custom colors in the preferences dialog
- [ ] **PANEL-05**: User can add a new custom color to the saved list via the color picker in the preferences dialog
- [ ] **PANEL-06**: User can remove a custom color from the saved list in the preferences dialog
- [ ] **PANEL-07**: User can edit (replace) an existing custom color in the saved list via the color picker in the preferences dialog

### Color Picker Redesign

- [x] **PICKER-01**: Clicking a color swatch selects/highlights it without closing the dialog
- [x] **PICKER-02**: User confirms selection with Enter key or OK button; dialog closes and returns chosen color
- [x] **PICKER-03**: The pre-selected color (`initial_color`) is visually highlighted when the dialog opens
- [x] **PICKER-04**: Swatch groups are ordered: custom colors → backdrop colors → Nuke defaults, with visual separation between groups
- [x] **PICKER-05**: Custom colors chosen via "Custom Color..." are staged in memory and only persisted to disk when the dialog is accepted (not on Cancel)

## v2 Requirements

### Navigation

- **NAV-V2-01**: Full browser-style forward/back navigation history (promoted to v1 if NAV-03 stretch goal ships)

### Color

- **COLOR-V2-01**: Anchor color propagation when user changes tile_color directly (currently by-design out of scope for v1)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Undo/redo stack integration | Nuke API complexity; not requested |
| Backdrops as link targets | Backdrops have no connectable outputs |
| Cross-script reconnection for Dot hidden inputs | Ad-hoc Dots are positional; cross-script reconnection is for named Links only |
| External persistence (database, remote API) | Local-only plugin |
| Multi-user / shared anchor libraries | Out of scope for single-artist tool |
| NAV-03 full history stack | Deferred to v2 — single-slot back covers primary use case |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PASTE-01 | Phase 1 | Complete |
| PASTE-03 | Phase 1 | Complete |
| PASTE-04 | Phase 1 | Complete (02-01) |
| LINK-01 | Phase 1 | Complete (01-01) |
| LINK-02 | Phase 1 | Complete (01-01) |
| LINK-03 | Phase 1 | Complete (01-01) |
| LINK-04 | Phase 1 | Complete (01-01) |
| XSCRIPT-01 | Phase 2 | Complete (02-01) |
| XSCRIPT-02 | Phase 2 | Complete (02-01) |
| NAV-01 | Phase 4 | Complete |
| NAV-02 | Phase 4 | Complete |
| NAV-03 | Phase 4 | Deferred (v2) — single-slot back implemented (NAV-01/02); full stack not shipped |
| COLOR-01 | Phase 3 | Complete |
| COLOR-02 | Phase 3 | Complete |
| COLOR-03 | Phase 3 | Complete |
| COLOR-04 | Phase 3 | Complete |
| COLOR-05 | Phase 3 | Complete |
| FIND-01 | Phase 4 | Complete |
| PREFS-01 | Phase 6 | Complete |
| PREFS-02 | Phase 6 | Complete |
| PREFS-03 | Phase 6 | Complete |
| PREFS-04 | Phase 6 | Complete |
| PANEL-01 | Phase 7 | Pending |
| PANEL-02 | Phase 7 | Pending |
| PANEL-03 | Phase 7 | Pending |
| PANEL-04 | Phase 7 | Pending |
| PANEL-05 | Phase 7 | Pending |
| PANEL-06 | Phase 7 | Pending |
| PANEL-07 | Phase 7 | Pending |
| PICKER-01 | Phase 7 | Complete |
| PICKER-02 | Phase 7 | Complete |
| PICKER-03 | Phase 7 | Complete |
| PICKER-04 | Phase 7 | Complete |
| PICKER-05 | Phase 7 | Complete |

**Coverage:**
- v1 requirements: 17 complete, 1 deferred (NAV-03 → v2)
- v1.1 requirements: 13 pending
- Mapped to phases: 31
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-03*
*Last updated: 2026-03-10 after v1.1 milestone start*
