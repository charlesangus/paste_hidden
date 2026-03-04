# Requirements: paste_hidden

**Defined:** 2026-03-03
**Core Value:** Copy and paste must reconnect predictably — anchors provide stable, navigable references; hidden inputs reconnect to their source without ceremony.

## v1 Requirements

### Copy-Paste Behavior

- [ ] **PASTE-01**: When a file node (Read, Camera, etc.) with an existing anchor is copied, paste creates a Link node pointing to that anchor
- [ ] **PASTE-02**: When a file node without an existing anchor is copied, paste auto-creates an anchor for it and a Link node pointing to the new anchor
- [ ] **PASTE-03**: Hidden-input Dot nodes reconnect to their original source node by identity on paste; they do not create anchors or become Links
- [ ] **PASTE-04**: Hidden-input Dot nodes pasted into a different script do not attempt to reconnect (leave disconnected cleanly)

### Link Node Types

- [ ] **LINK-01**: 2D stream nodes use PostageStamp as the link node class
- [ ] **LINK-02**: Deep and 3D stream nodes (e.g. Camera) use NoOp as the link node class
- [ ] **LINK-03**: Camera links no longer incorrectly produce PostageStamp nodes when pasted
- [ ] **LINK-04**: Fallback: if stream-type detection is not simple and performant, all non-Dot links use NoOp

### Cross-Script Paste

- [ ] **XSCRIPT-01**: Link nodes pasted into another script reconnect to an anchor of the same name in the destination script
- [ ] **XSCRIPT-02**: Hidden-input Dot nodes pasted into another script do not reconnect (distinct from Link behavior)

### Anchor Navigation History

- [ ] **NAV-01**: DAG position is saved when navigate-to-anchor (Alt+A) is invoked
- [ ] **NAV-02**: A keyboard shortcut jumps the DAG view back to the saved position
- [ ] **NAV-03**: Full browser-style forward/back navigation history stack (stretch goal)

### Anchor Color System

- [ ] **COLOR-01**: Tabtabtab picker reads the anchor's actual `tile_color` knob value at invocation time (not re-derived from backdrop/input logic)
- [ ] **COLOR-02**: Anchor creation dialog includes a color picker
- [ ] **COLOR-03**: Anchor rename dialog includes a color picker
- [ ] **COLOR-04**: Anchor node has a color picker button/knob in its properties panel
- [ ] **COLOR-05**: When anchor color is changed via our color picker, all linked nodes update their color to match

### Anchor Find

- [ ] **FIND-01**: Anchor navigation picker (Alt+A) includes labelled BackdropNodes as navigable targets alongside anchor nodes

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

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PASTE-01 | Phase 1 | Pending |
| PASTE-02 | Phase 1 | Pending |
| PASTE-03 | Phase 1 | Pending |
| PASTE-04 | Phase 1 | Pending |
| LINK-01 | Phase 1 | Pending |
| LINK-02 | Phase 1 | Pending |
| LINK-03 | Phase 1 | Pending |
| LINK-04 | Phase 1 | Pending |
| XSCRIPT-01 | Phase 2 | Pending |
| XSCRIPT-02 | Phase 2 | Pending |
| NAV-01 | Phase 4 | Pending |
| NAV-02 | Phase 4 | Pending |
| NAV-03 | Phase 4 | Pending |
| COLOR-01 | Phase 3 | Pending |
| COLOR-02 | Phase 3 | Pending |
| COLOR-03 | Phase 3 | Pending |
| COLOR-04 | Phase 3 | Pending |
| COLOR-05 | Phase 3 | Pending |
| FIND-01 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-03*
*Last updated: 2026-03-03 after roadmap creation*
