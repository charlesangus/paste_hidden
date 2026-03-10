---
status: diagnosed
phase: 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction
source: [05-01-SUMMARY.md]
started: 2026-03-05T14:00:00Z
updated: 2026-03-05T14:30:00Z
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
  root_cause: "paste_hidden() Path A/C (lines 149, 159) unconditionally creates a NoOp via nuke.createNode('NoOp'), never calling get_link_class_for_source() which would return 'Dot' for a Dot anchor source"
  artifacts:
    - path: "paste_hidden.py"
      issue: "lines 149 and 159 — nuke.createNode('NoOp') hardcoded; should be nuke.createNode(get_link_class_for_source(input_node or node))"
  missing:
    - "Call get_link_class_for_source() in Path A/C to pick Dot vs NoOp based on source class"
  fix_verified: "Pass (2026-03-10) — get_link_class_for_source() added to Path A/C in 05-03. Gap closed."

- truth: "Local Dot tile_color should be a dark burnt orange, clearly distinct from Link Dot purple"
  status: failed
  reason: "User reported: let's go darker on the dot colour tho"
  severity: cosmetic
  test: 2
  root_cause: "LOCAL_DOT_COLOR = 0xB35A00FF is mid-brightness burnt orange (R=179,G=90,B=0); user wants it darker"
  artifacts:
    - path: "constants.py"
      issue: "line 26 — LOCAL_DOT_COLOR = 0xB35A00FF should be a darker value, e.g. 0x7A3A00FF"
  missing:
    - "Darken LOCAL_DOT_COLOR constant"
  fix_verified: "Pass (2026-03-10) — darkened to 0x7A3A00FF in 05-03. Gap closed."

- truth: "Pasting a Local Dot preserves its 'Local: {name}' label and burnt orange color — not overwritten to 'Link: ...' and input node color"
  status: failed
  reason: "User reported: when pasting the Local: dot, the label changes to link / new dot is named Link: bla bla and takes on the colour of the input node."
  severity: major
  test: 2
  root_cause: "setup_link_node() calls add_input_knob(link_node) without dot_type, which strips the DOT_TYPE_KNOB_NAME knob entirely (link.py line 116 removes it, line 137 only re-adds if dot_type is not None). The guard at paste_hidden.py line 203 then never fires because the knob is gone."
  artifacts:
    - path: "paste_hidden.py"
      issue: "lines 200-207 — must read dot_type_value before calling setup_link_node(), then restore Local appearance unconditionally without relying on the knob surviving the call"
    - path: "link.py"
      issue: "setup_link_node() calls add_input_knob() with no dot_type, silently stripping the knob"
  missing:
    - "Read dot_type from node before setup_link_node(); re-apply Local appearance and re-stamp knob afterward if dot_type == 'local'"
  fix_verified: "Pass (2026-03-10) — saved_dot_type re-stamp pattern implemented in 05-03. Gap closed."

- truth: "Link Dot reconnects cross-script to the matching Anchor Dot by name"
  status: failed
  reason: "User reported: Doesn't work. The Link: dot does not re-connect to the Anchor dot. Probably because Anchor dots work by label. That's a misfeature. Let's rework anchor dots so the label and node name stay in sync."
  severity: major
  test: 3
  root_cause: "Two compounding issues: (1) _extract_display_name_from_fqnn() returns None for Dot anchors because their node names lack the ANCHOR_PREFIX ('Anchor_') prefix, so cross-script reconnect is never attempted. (2) Even if bypassed, anchor_display_name() for Dots returns node['label'] while the FQNN stores the node name — they are never guaranteed to match since rename_anchor_to() updates only the label for Dot anchors."
  artifacts:
    - path: "paste_hidden.py"
      issue: "lines 114-116 — _extract_display_name_from_fqnn() ANCHOR_PREFIX guard silently excludes all Dot anchors"
    - path: "anchor.py"
      issue: "lines 147-153 — rename_anchor_to() updates only label for Dot anchors, leaving node name (used in FQNN) out of sync"
  missing:
    - "rename_anchor_to() must also rename the Dot node's Nuke name to a sanitized form matching the label (e.g. Anchor_<sanitized>) so FQNN and label-based lookup agree"
    - "mark_dot_as_anchor() / creation path must apply the same node name sync"
    - "Remove or relax ANCHOR_PREFIX guard in _extract_display_name_from_fqnn() for Dot anchors once node names carry the prefix"
  fix_verified: "Pass for Link Dot → Anchor Dot reconnect (2026-03-10). New issue discovered: Anchor Dot copied cross-script should paste as a Link Dot connected to the matching anchor in the destination script — currently does not."

- truth: "Copying an Anchor Dot cross-script pastes as another Anchor Dot (not a Link Dot to the matching anchor)"
  status: observation
  reason: "User noted: pasting an Anchor Dot into a script with a matching anchor could reasonably paste as a Link Dot connected to it. Deferred — current behavior is not inherently wrong. Watch for user feedback before deciding."
  severity: minor
  test: 3-retest

- truth: "Pasting a Local Dot same-script produces a Dot with 'Local: {name}' label and burnt orange color — not 'Link: ...' and input node color"
  status: failed
  reason: "User reported: fail. when copy-pasting a Local: dot, the new dot is named Link: bla bla and takes on the colour of the input node. incorrect behaviour, not to spec."
  severity: major
  test: 5
  root_cause: "Same root cause as test 2 gap — setup_link_node() strips the DOT_TYPE knob, so Local appearance restoration guard never fires. setup_link_node() also sets label to 'Link: ...' and tile_color to input node color, which is never corrected."
  artifacts:
    - path: "paste_hidden.py"
      issue: "Same fix location as test 2 gap — lines 200-207"
  missing:
    - "Same fix as test 2 gap — read and restore dot_type before/after setup_link_node()"
  fix_verified: "Pass (2026-03-10) — covered by re-test 2 above. Gap closed."
