# paste_hidden

## What This Is

`paste_hidden` is a Foundry Nuke plugin that replaces Nuke's native clipboard system with one that intelligently handles hidden inputs, and adds a named anchor/link reference system for navigating and reusing node graph connections. It is used by a single VFX artist to manage complex compositing node graphs.

## Core Value

Copy and paste must reconnect predictably — anchors provide stable, navigable references; hidden inputs reconnect to their source without ceremony.

## Requirements

### Validated

- ✓ Ctrl+C/X/V replaced with hidden-input-aware clipboard system — existing
- ✓ Anchor nodes (NoOp with `Anchor_` prefix, or marked Dot) created and named — existing
- ✓ Link nodes (PostageStamp/NoOp/Dot) wire to anchors via FQNN — existing
- ✓ Tabtabtab fuzzy-search picker for anchor creation and navigation — existing
- ✓ Anchor navigation (Alt+A) zooms DAG to anchor location — existing
- ✓ Anchor renaming propagates label to all linked nodes — existing
- ✓ Label utilities (large/medium/append) with font sizing — existing
- ✓ Anchor color inherits from backdrop → input node → default purple on creation — existing

### Active

**Copy-paste behavior:**
- [ ] File nodes (Read, Camera, etc.) with an existing anchor → copy creates a link to that anchor
- [ ] File nodes without an anchor → copy auto-creates an anchor for them
- [ ] Hidden-input Dots reconnect to their original source by node identity; do not create anchors or become links unless manually connected to one

**Link node type system:**
- [ ] 2D stream nodes use PostageStamp links (preferred); Deep/3D stream nodes use NoOp links
- [ ] Camera links no longer come out as PostageStamp when pasted (current bug)
- [ ] Fallback: all non-Dot links use NoOp if stream-type detection is not simple and performant

**Cross-script paste:**
- [ ] Link nodes reconnect to an anchor of the same name when pasted into another script
- [ ] Hidden-input Dot nodes do not reconnect cross-script (leave disconnected cleanly)

**Anchor navigation history:**
- [ ] DAG position is saved when navigate-to-anchor is invoked
- [ ] Keyboard shortcut jumps back to the saved position
- [ ] Full browser-style forward/back history stack (stretch goal)

**Anchor color system:**
- [ ] Tabtabtab reads actual `tile_color` knob value at invocation — not re-derived from backdrop/input logic
- [ ] Anchor creation dialog includes a color picker
- [ ] Anchor rename dialog includes a color picker
- [ ] Color picker button/knob on anchor node itself
- [ ] When anchor color is changed via our color picker → all linked nodes update to match
- [ ] Manual tile_color changes by user do not propagate (links stay wrong until next copy-paste — by design)

**Anchor find:**
- [ ] Anchor navigation picker (Alt+A) includes labelled BackdropNodes as navigable targets

### Out of Scope

- Undo/redo stack integration — Nuke API complexity, not requested
- Cross-script reconnection for hidden-input Dot nodes — explicitly excluded
- Backdrops as link targets — navigate-only
- External persistence (database, remote API) — local-only plugin

## Context

Brownfield Nuke plugin. The codebase has two partly-overlapping systems: a legacy hidden-input copy-paste system (Dot nodes that reconnect to their source) and a newer anchor/link system (named NoOp/Dot anchors with FQNN-tracked link nodes). The interactions between these systems are inconsistent and causing bugs. The current milestone is about making both systems well-defined with clear, non-overlapping semantics, and shipping the missing anchor UX features (color picker, navigation history, backdrop inclusion).

Key architectural context:
- All state stored as node knobs (no external persistence); survives save/reload
- FQNN format: `<script_stem>.<node.fullName()>` — used for cross-script detection
- `link.py` contains shared predicates and setup; `constants.py` holds all class mappings
- PySide2 (Nuke <16) and PySide6 (Nuke 16+) both must work; Qt may be unavailable in headless Nuke

## Constraints

- **Runtime**: Nuke 14+ embedded Python (2.7+/3.x); no external package manager
- **UI**: PySide2/PySide6 conditional — all Qt code must degrade gracefully if Qt unavailable
- **Dependencies**: No dependencies beyond Nuke bundled runtime (`nuke`, `nukescripts`, Qt)
- **State**: All persistence via node knobs only — no files written at runtime (except tabtabtab weights)
- **Compatibility**: Changes must not break existing anchors/links in saved `.nk` scripts

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hidden-input Dots and Links are distinct systems with different semantics | Dots are ad-hoc; Links are named references. Conflating them causes inconsistent reconnection | — Pending |
| PostageStamp preferred for 2D links; NoOp as fallback for all | PostageStamp doesn't work for Deep/3D streams; NoOp always works | — Pending |
| Color propagation only from our color picker, not raw tile_color changes | Low-stakes; user who bypasses the picker accepts stale link colors | — Pending |
| Backdrop anchors are navigate-only, not link targets | Backdrops don't have connectable outputs | — Pending |
| Cross-script reconnection for Links (by name), not for Dots | Dots are positional/ad-hoc; Links are intentional named references | — Pending |

---
*Last updated: 2026-03-03 after initialization*
