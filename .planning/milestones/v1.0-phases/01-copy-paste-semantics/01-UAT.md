---
status: diagnosed
phase: 01-copy-paste-semantics
source: 01-01-SUMMARY.md, 01-02-SUMMARY.md
started: 2026-03-04T12:45:00Z
updated: 2026-03-04T13:10:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Camera anchor paste creates NoOp link
expected: Create a Camera node. Run the paste_hidden anchor workflow to attach it (creating a hidden anchor for that Camera). Copy the Camera node. Paste it — a new link node should be created using the NoOp class (not PostageStamp), because Camera nodes produce 3D/geo streams, not 2D image streams.
result: issue
reported: "Works for camera nodes, but only camera nodes. We need a generic solution. I suggest that at anchor creation, we create some temp nodes - a 3d node, a Deep node, and a 2d node, and either actually try to wire them in to the anchor's input, or use canSetInput to determine whether the anchor is wired into a 2d, 3d, or Deep stream. Then we need to store that on the anchor, so we can make the correct link type."
severity: major

### 2. Read anchor paste creates PostageStamp link
expected: Create a Read node with media loaded. Run the paste_hidden anchor workflow to attach it. Copy the Read node. Paste it — a new link node should be created using the PostageStamp class (not NoOp), because Read nodes produce 2D image streams.
result: pass

### 3. Unknown node type anchor paste falls back to NoOp
expected: Create a node type that is not in LINK_CLASSES (e.g., a generic node with no standard channel output, or one with unusual channel names). Attach it via the anchor workflow. Copy and paste — a NoOp link should be created with no error or exception. The fallback should be silent and safe.
result: pass

### 4. Cross-script Dot paste is silent
expected: In script A, create a hidden-input Dot connected to some source node. Copy that Dot. Open (or switch to) script B where that source node does not exist. Paste — the paste should complete silently with no error dialog or Python traceback. The Dot may appear disconnected or be skipped, but no exception should be raised.
result: pass

## Summary

total: 4
passed: 3
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Link class detection at anchor creation works generically for all node types (2D, 3D/geo, Deep), not just Camera"
  status: failed
  reason: "User reported: Works for camera nodes, but only camera nodes. We need a generic solution. I suggest that at anchor creation, we create some temp nodes - a 3d node, a Deep node, and a 2d node, and either actually try to wire them in to the anchor's input, or use canSetInput to determine whether the anchor is wired into a 2d, 3d, or Deep stream. Then we need to store that on the anchor, so we can make the correct link type."
  severity: major
  test: 1
  root_cause: "detect_link_class_for_node() uses static LINK_CLASSES dict (only 8 known file-reader types) then channel-prefix heuristic ('rgba','depth','forward'). Neither strategy affirmatively identifies stream type for arbitrary node classes — 3D/Deep nodes fall through to NoOp by coincidence, not by design. No use of Nuke's canSetInput() API."
  artifacts:
    - path: "link.py"
      issue: "detect_link_class_for_node() relies on static dict + channel-name prefix inspection; no canSetInput probe; cannot classify unknown node types correctly"
    - path: "constants.py"
      issue: "LINK_CLASSES dict covers only 8 known file-reader classes; no generic stream-type coverage"
    - path: "anchor.py"
      issue: "_store_link_class_on_anchor() calls detect_link_class_for_node() without any canSetInput fallback; if input_node is None, silently stores 'NoOp' without probing"
  missing:
    - "New probe function in link.py: create temp NoOp (2D), Scene (3D/geo), DeepMerge (Deep) scratch nodes; call anchor_node.canSetInput(0, scratch) for each; first True match identifies stream type; delete scratch nodes immediately"
    - "Map probe result to link class: 2D accepted → 'PostageStamp'; 3D or Deep accepted → 'NoOp'; no match → 'NoOp'"
    - "Replace channel-inspection fallback in detect_link_class_for_node() with canSetInput probe; retain LINK_CLASSES fast-path for known types"
    - "Update _store_link_class_on_anchor() to use probe against anchor.input(0) when input_node is None"
  debug_session: ""
