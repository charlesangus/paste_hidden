---
status: complete
phase: 06-preferences-infrastructure
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md, 06-04-SUMMARY.md]
started: 2026-03-11T12:40:00Z
updated: 2026-03-11T13:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Prefs file created on first run
expected: Delete (or rename) ~/.nuke/paste_hidden_prefs.json if it exists. Launch Nuke and load the plugin. After startup, ~/.nuke/paste_hidden_prefs.json should exist and contain the three keys: plugin_enabled (true), link_classes_paste_mode ("stamp"), and custom_colors (a list).
result: issue
reported: "No sign of it."
severity: major

### 2. Legacy palette migration
expected: With ~/.nuke/paste_hidden_prefs.json absent but ~/.nuke/paste_hidden_user_palette.json present (from an old install), load the plugin. The new prefs file should be created and its custom_colors list should contain the colors from the old palette file. The old palette file should be left untouched.
result: skipped
reason: No old palette file present; prefs file creation already failing (Test 1)

### 3. Plugin disabled — clipboard passthrough
expected: Set plugin_enabled to false in ~/.nuke/paste_hidden_prefs.json (or via any prefs UI if available). Restart Nuke / reload plugin. Select any node and press Ctrl+C, then Ctrl+V. Nuke's standard copy/paste should work normally — no anchor gets created, no FQNN knob is stamped on the pasted node.
result: pass

### 4. Plugin disabled — anchor and label shortcuts do nothing
expected: With plugin_enabled set to false, press the anchor creation shortcut and the label shortcuts. Nothing should happen — no dialog opens, no node is created, no error appears.
result: pass

### 5. Plugin disabled — menu items greyed out
expected: With plugin_enabled set to false at startup, open the Nuke menu where the anchor/label commands live. All plugin-specific anchor and label commands should appear greyed out / disabled. The "old" copy/cut/paste fallback commands should remain active.
result: pass

### 6. Passthrough copy mode — no FQNN stamp on LINK_SOURCE_CLASSES nodes
expected: Set link_classes_paste_mode to "passthrough" in the prefs file (plugin_enabled must be true). Select a Read node (or Camera node) and press the plugin copy shortcut. Paste into the same or another script. The pasted node should be a plain copy with no FQNN input knob stamped on it — as if you had used Nuke's built-in copy.
result: pass

### 7. Normal stamp mode still works
expected: With link_classes_paste_mode set to "stamp" (default) and plugin_enabled true, copy a Read node and paste it. The pasted node should have the FQNN input knob stamped as normal (existing Phase 1–5 behavior unchanged).
result: pass

## Summary

total: 7
passed: 5
issues: 1
pending: 0
skipped: 1

## Gaps

- truth: "~/.nuke/paste_hidden_prefs.json is created on first run containing plugin_enabled, link_classes_paste_mode, and custom_colors keys"
  status: failed
  reason: "User reported: No sign of it."
  severity: major
  test: 1
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
