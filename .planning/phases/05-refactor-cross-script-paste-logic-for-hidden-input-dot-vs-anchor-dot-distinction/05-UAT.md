---
status: complete
phase: 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction
source: [05-01-SUMMARY.md]
started: 2026-03-05T14:00:00Z
updated: 2026-03-05T14:20:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Link Dot gets canonical purple at copy time
expected: Copy a Dot backed by an anchor node. After copy_hidden() runs, the Dot's tile_color should be canonical purple (ANCHOR_DEFAULT_COLOR). Label should NOT have a "Local: " prefix.
result: pass

### 2. Local Dot gets burnt orange at copy time
expected: Copy a Dot backed by a plain node (NOT an anchor). After copy_hidden() runs, the Dot should be burnt orange (LOCAL_DOT_COLOR = 0xB35A00FF) and its label should have a "Local: {source name}" prefix.
result: issue
reported: "pass; let's go darker on the dot colour tho"
severity: cosmetic

### 3. Link Dot reconnects cross-script (Bug 1 fix)
expected: Copy a Link Dot in Script A. Paste into Script B (different file). If Script B contains an anchor with the same name as the source anchor, the Dot should reconnect to that anchor. Previously this failed to reconnect.
result: issue
reported: "Doesn't work. The Link: dot does not re-connect to the Anchor dot. Probably because Anchor dots work by label. That's a misfeature. Let's rework anchor dots so the label and node name stay in sync."
severity: major

### 4. Local Dot is a no-op cross-script (Bug 2 fix)
expected: Copy a Local Dot in Script A (with filename stem e.g. "comp"). Paste into Script B that also has the same filename stem "comp". The Dot should NOT reconnect to any node — it should be left disconnected silently. Previously it falsely reconnected due to the same-stem false positive.
result: pass
reason: "Test expectation was incorrect — same-filename-stem reconnect is acceptable behavior, not a bug."

### 5. Local Dot reconnects same-script and restores appearance
expected: Copy a Local Dot within the same script. Paste it. The Dot reconnects to the same source node, and its burnt orange color and "Local: " label are restored after paste (not overwritten by setup_link_node()).
result: issue
reported: "fail. when copy-pasting a Local: dot, the new dot is named Link: bla bla and takes on the colour of the input node. incorrect behaviour, not to spec."
severity: major

## Summary

total: 5
passed: 2
issues: 4
pending: 0
skipped: 0

## Gaps

- truth: "Copy-pasting a Dot anchor should paste a Dot node, not a NoOp"
  status: failed
  reason: "User reported: copy-pasting a Dot anchor creates a NoOp, not a Dot. Need to fix that."
  severity: major
  test: 1
  artifacts: []
  missing: []

- truth: "Local Dot tile_color should be a dark burnt orange, clearly distinct from Link Dot purple"
  status: failed
  reason: "User reported: let's go darker on the dot colour tho"
  severity: cosmetic
  test: 2
  artifacts: []
  missing: []

- truth: "Pasting a Local Dot preserves its 'Local: {name}' label — label must not change to 'link' after paste"
  status: failed
  reason: "User reported: when pasting the Local: dot, the label changes to link. that is wrong."
  severity: major
  test: 2
  artifacts: []
  missing: []

- truth: "Link Dot reconnects cross-script to the matching Anchor Dot by name"
  status: failed
  reason: "User reported: Doesn't work. The Link: dot does not re-connect to the Anchor dot. Probably because Anchor dots work by label. That's a misfeature. Let's rework anchor dots so the label and node name stay in sync."
  severity: major
  test: 3
  root_cause: "find_anchor_by_name() searches by node name, but Anchor Dots are identified by label — label and node name are not kept in sync, so name-based lookup fails"
  artifacts: []
  missing: []

- truth: "Pasting a Local Dot same-script produces a Dot with 'Local: {name}' label and burnt orange color — not 'Link: ...' and input node color"
  status: failed
  reason: "User reported: fail. when copy-pasting a Local: dot, the new dot is named Link: bla bla and takes on the colour of the input node. incorrect behaviour, not to spec."
  severity: major
  test: 5
  artifacts: []
  missing: []
