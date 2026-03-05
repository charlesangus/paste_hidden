# Roadmap: paste_hidden

## Overview

This milestone clarifies the boundary between hidden-input Dot nodes and named Link nodes, fixes the link-type selection bug for Camera and other non-2D streams, extends paste behavior to auto-create anchors for file nodes, and ships the missing anchor UX features: color pickers in dialogs and on the anchor node itself, color propagation to links, cross-script link reconnection, DAG navigation history, and Backdrop inclusion in the navigation picker.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Copy-Paste Semantics** - Define clear behavior for file node anchoring and hidden-input Dot reconnection; fix link node type selection (completed 2026-03-04)
- [x] **Phase 2: Cross-Script Paste** - Link nodes reconnect by name across scripts; Dot nodes leave disconnected cleanly (completed 2026-03-05)
- [ ] **Phase 3: Anchor Color System** - Color picker in creation/rename dialogs and on anchor node; propagation to linked nodes
- [ ] **Phase 4: Anchor Navigation** - DAG position history with back shortcut; Backdrops included in navigation picker

## Phase Details

### Phase 1: Copy-Paste Semantics
**Goal**: Copy and paste behave predictably for file nodes and hidden-input Dots, with the correct link node class used for each stream type
**Depends on**: Nothing (first phase)
**Requirements**: PASTE-01, PASTE-03, LINK-01, LINK-02, LINK-03, LINK-04
**Success Criteria** (what must be TRUE):
  1. Copying a LINK_CLASSES file node with an existing anchor, or a hidden-input Dot whose input is an anchor, produces a Link node wired to that anchor on paste (cross-script capable)
  2. Copying a LINK_CLASSES file node with no anchor produces a Link node pointing directly to that file node on paste (legacy behaviour; no anchor involved)
  3. Copying a hidden-input Dot whose input is a non-anchor node reconnects it to that source on paste (same-script only); no anchor created, no Link node
  4. Pasting a Camera node produces a NoOp link, not a PostageStamp; pasting a 2D Read produces a PostageStamp link
  5. If stream-type detection cannot be implemented simply, all non-Dot links fall back to NoOp and no regressions occur
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Foundation: stream detection, link class stored on anchor, lookup helpers
- [ ] 01-02-PLAN.md — Routing: copy_hidden() and paste_hidden() new three-path classification

### Phase 2: Cross-Script Paste
**Goal**: Pasting into a different script reconnects Links by anchor name and leaves hidden-input Dots cleanly disconnected
**Depends on**: Phase 1
**Requirements**: XSCRIPT-01, XSCRIPT-02
**Success Criteria** (what must be TRUE):
  1. A Link node copied from script A and pasted into script B automatically reconnects to an anchor of the same name in script B if one exists
  2. A Link node copied from script A and pasted into script B leaves the Link disconnected (not errored) if no matching anchor exists in script B
  3. A hidden-input Dot copied from script A and pasted into script B is left disconnected without any reconnection attempt or error
**Plans**: 1 plan

Plans:
- [x] 02-01-PLAN.md — Cross-script reconnect (XSCRIPT-01/02), LINK_CLASSES dead code removal, PASTE-04 confirmed

### Phase 3: Anchor Color System
**Goal**: Anchor color is set via an explicit color picker at creation and rename time, surfaced on the anchor node itself, and propagates to all linked nodes when changed through our picker
**Depends on**: Phase 1
**Requirements**: COLOR-01, COLOR-02, COLOR-03, COLOR-04, COLOR-05
**Success Criteria** (what must be TRUE):
  1. The tabtabtab anchor picker displays each anchor's color by reading its actual tile_color knob value at open time, not by re-running backdrop/input logic
  2. The anchor creation dialog includes a color picker; the chosen color is applied to the new anchor
  3. The anchor rename dialog includes a color picker; the chosen color is applied to the anchor on save
  4. The anchor node's properties panel contains a color picker button that changes the anchor's color
  5. After changing anchor color via any of our color pickers, all Link nodes for that anchor immediately update their tile_color to match
**Plans**: TBD

### Phase 4: Anchor Navigation
**Goal**: The artist can jump back to where they were after navigating to an anchor, and Backdrops appear alongside anchor nodes in the navigation picker
**Depends on**: Phase 1
**Requirements**: NAV-01, NAV-02, NAV-03, FIND-01
**Success Criteria** (what must be TRUE):
  1. Invoking navigate-to-anchor (Alt+A) saves the current DAG position before jumping
  2. A keyboard shortcut returns the DAG view to the position saved before the last navigate-to-anchor
  3. Labelled BackdropNodes appear in the Alt+A navigation picker alongside anchor nodes and are navigable (DAG zooms to the Backdrop)
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Copy-Paste Semantics | 3/3 | Complete   | 2026-03-04 |
| 2. Cross-Script Paste | 1/1 | Complete    | 2026-03-05 |
| 3. Anchor Color System | 0/? | Not started | - |
| 4. Anchor Navigation | 0/? | Not started | - |

### Phase 5: Refactor cross-script paste logic for hidden-input Dot vs Anchor Dot distinction

**Goal:** Fix two UAT-confirmed bugs from Phase 2 — Link Dots not reconnecting cross-script and Local Dots erroneously reconnecting cross-script — by introducing a formal DOT_TYPE knob distinction between the two Dot subtypes
**Requirements**: XSCRIPT-01, XSCRIPT-02
**Depends on:** Phase 2
**Plans:** 3 plans (1 complete, 2 gap-closure)

Plans:
- [x] 05-01-PLAN.md — TDD: DOT_TYPE knob distinction (constants, add_input_knob extension, copy_hidden/paste_hidden Path B refactor)
- [ ] 05-02-PLAN.md — Gap closure: Dot anchor node name sync (mark_dot_as_anchor + rename_anchor_to set Anchor_ prefix on node name)
- [ ] 05-03-PLAN.md — Gap closure: LOCAL_DOT_COLOR darkened; DOT_TYPE preserved across setup_link_node(); Path A/C Dot link class fix
