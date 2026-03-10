---
status: complete
phase: 03-anchor-color-system
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md]
started: 2026-03-10T00:00:00Z
updated: 2026-03-10T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Create anchor shows combined name+color dialog
expected: Select a node and create an anchor (e.g. via the menu or shortcut). A dialog appears that lets you enter a name AND choose a color in one step — not two separate dialogs. The dialog shows a color swatch grid.
result: pass
note: Dialog works but exact design needs rework — user has thoughts on this.

### 2. Dialog pre-selects color from input node
expected: With a node selected (e.g. a Read or Merge), open the create anchor dialog. The color swatch pre-selects a color derived from the input node (e.g. its tile color or backdrop color). If nothing useful is derivable, it pre-selects the default purple.
result: issue
reported: "There is no visible feedback as to what color will be used."
severity: major

### 3. Anchor is created with chosen color
expected: Create an anchor and pick a non-default color in the dialog. The resulting anchor node has that color as its tile_color. The tabtabtab picker (Alt+A) shows it in that color.
result: pass

### 4. Cancel on creation dialog aborts anchor creation
expected: Open the create anchor dialog and press Cancel. No anchor node is created — nothing changes in the DAG.
result: pass

### 5. Rename anchor dialog shows current color pre-selected
expected: Select an existing anchor and rename it (e.g. via menu). The ColorPaletteDialog opens with the anchor's CURRENT color already highlighted/selected in the grid, not the default. The name field is pre-filled with the current name.
result: pass

### 6. Changing color in rename dialog propagates to all linked nodes
expected: An anchor has 2+ link nodes pointing to it. Open rename dialog, choose a different color, confirm. All linked nodes (PostageStamp / NoOp) update to that new color. The anchor itself also updates.
result: pass

### 7. "Set Color" button on anchor node opens color picker
expected: Select an existing anchor node and look at its knobs panel. There should be a "Set Color" button/knob. Clicking it opens the ColorPaletteDialog. Choosing a color updates the anchor and all its linked nodes.
result: pass

### 8. tabtabtab (Alt+A) shows anchor colors correctly
expected: Create anchors with different colors. Open the Alt+A picker. Each anchor entry in the picker shows its correct color (the one you set), not a stale or default color.
result: pass

## Summary

total: 8
passed: 7
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Dialog pre-selects a color and makes it visually obvious which color will be used"
  status: failed
  reason: "User reported: There is no visible feedback as to what color will be used."
  severity: major
  test: 2
  root_cause: ""
  artifacts: []
  missing: []
