---
status: complete
phase: 04-anchor-navigation
source: [04-W0-SUMMARY.md, 04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md]
started: 2026-03-10T00:00:00Z
updated: 2026-03-10T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Alt+A saves DAG position before navigating
expected: Press Alt+A and select an anchor (or backdrop). Navigate jumps to the node. Then press Alt+Z — it returns you to exactly where you were before the Alt+A jump (same zoom level and center). The return is instantaneous and precise.
result: pass

### 2. Alt+Z is no-op when no prior navigation
expected: Press Alt+Z without having pressed Alt+A first (fresh Nuke session or script just opened). Nothing happens — no error, no movement, no crash.
result: pass

### 3. Alt+Z only goes back one step
expected: Press Alt+A twice to navigate to two different anchors. Press Alt+Z once — you return to the position before the SECOND Alt+A jump (not the first). A second Alt+Z press does nothing (slot consumed).
result: pass

### 4. Alt+A picker includes labelled BackdropNodes
expected: Create a BackdropNode and give it a label (e.g. "BG Comp"). Press Alt+A — the picker shows a "Backdrops/BG Comp" entry alongside any Anchors. Selecting it navigates to and zooms the backdrop to fit.
result: pass
note: Backdrop entries appear as "BG Comp [Backdrop]" (not "Backdrops/BG Comp"). User suggested prefixing with "Backdrops/" to enable filtering by typing "ba" — deferred as future improvement, current format acceptable.

### 5. Alt+A picker opens with only Backdrops (no anchors)
expected: In a script with labelled Backdrops but no anchor nodes, press Alt+A. The picker opens (not silently fails). Backdrops are listed and selectable.
result: pass

### 6. Navigating to backdrop via Alt+A saves position for Alt+Z
expected: Note your current position. Press Alt+A, navigate to a Backdrop. You jump to it. Press Alt+Z — you return to where you were before the jump.
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
