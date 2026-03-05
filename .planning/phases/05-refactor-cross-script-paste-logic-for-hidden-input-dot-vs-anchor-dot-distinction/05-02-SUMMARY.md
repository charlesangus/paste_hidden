---
phase: 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction
plan: 02
subsystem: anchor-dot-name-sync
tags: [tdd, anchor, dot, name-sync, fqnn, cross-script]
dependency_graph:
  requires: []
  provides:
    - mark_dot_as_anchor sets Dot node name to Anchor_<sanitized_label>
    - rename_anchor_to Dot branch updates node name AND link FQNNs
    - TDD suite for Dot anchor name sync
  affects:
    - anchor.py rename_anchor_to
    - link.py mark_dot_as_anchor
    - tests/test_dot_anchor_name_sync.py
tech_stack:
  added: []
  patterns:
    - TDD red-green with offline nuke stub
    - FQNN old/new capture around setName for atomic FQNN update
key_files:
  created:
    - tests/test_dot_anchor_name_sync.py
  modified:
    - anchor.py
    - link.py
    - tests/test_dot_type_distinction.py
decisions:
  - rename_anchor_to Dot branch raises ValueError for empty sanitized name — consistent with NoOp path
  - anchor_display_name() for Dot anchors is unchanged — remains label-based for UI picker readability
  - mark_dot_as_anchor name sync occurs only on the first call (knob guard path returns early on subsequent calls)
  - setName() added to StubNode in test_dot_type_distinction.py to unblock shared nuke stub when both test files run together
metrics:
  duration: 3 min
  completed_date: "2026-03-05"
  tasks_completed: 2
  files_modified: 4
---

# Phase 05 Plan 02: Dot Anchor Node Name Sync Summary

**One-liner:** Dot anchors now carry `Anchor_` prefix in their node name — `mark_dot_as_anchor()` sets it on creation, `rename_anchor_to()` keeps it in sync and updates link FQNNs.

## Objective

Fix the root cause of UAT test 3 failure: Dot anchor node names stayed as Nuke auto-assigned names like `Dot1`, making cross-script reconnect impossible because `_extract_display_name_from_fqnn()` could not strip `ANCHOR_PREFIX` from a name that never had it.

## What Was Built

**`link.py` — `mark_dot_as_anchor()` updated:**
- After the boolean knob is added, reads the Dot's `label` knob
- Sanitizes the label using `re.sub(r'[^A-Za-z0-9_]', '_', label)`
- If the sanitized result is non-empty, calls `dot_node.setName(ANCHOR_PREFIX + sanitized)`
- Empty labels leave the node name unchanged (caller responsibility)
- `import re` added at module level

**`anchor.py` — `rename_anchor_to()` Dot branch rewritten:**
- Sanitizes the new name immediately; raises `ValueError` if result is empty (matches NoOp path guard)
- Captures `old_fqnn = get_fully_qualified_node_name(anchor_node)` BEFORE `setName()`
- Calls `anchor_node.setName(ANCHOR_PREFIX + sanitized)` to sync node name
- Sets `anchor_node['label'].setValue(name.strip())`
- Captures `new_fqnn = get_fully_qualified_node_name(anchor_node)` AFTER `setName()`
- Iterates `nuke.allNodes()` updating `KNOB_NAME` from `old_fqnn` to `new_fqnn` and label to `'Link: {name.strip()}'` on matching link nodes

**`anchor_display_name()` — unchanged:** Still returns `node['label'].getValue().strip()` for Dot anchors.

**`tests/test_dot_anchor_name_sync.py` — TDD suite (10 tests):**
- 3 tests for `mark_dot_as_anchor()`: labelled Dot gets name, empty label leaves name, idempotent on second call
- 5 tests for `rename_anchor_to()` Dot path: label updated, node name updated, link KNOB_NAME updated, link label updated, ValueError on empty sanitized name
- 2 tests for `anchor_display_name()` Dot path: label text returned (not node name), spaces preserved

**`tests/test_dot_type_distinction.py` — StubNode extended:**
- Added `setName(new_name)` method to StubNode (auto-fix Rule 2: missing method caused AttributeError when both test files ran together, sharing the same `sys.modules['nuke']`)

## Verification

```
python3 -m pytest tests/ -v
41 passed in 0.13s
```

All 10 new tests pass. All 31 pre-existing tests pass (including 20 from `test_dot_type_distinction.py` and 11 from `test_cross_script_paste.py`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical stub method] Added `setName()` to StubNode in test_dot_type_distinction.py**
- **Found during:** GREEN phase — all 5 new `rename_anchor_to` and `mark_dot_as_anchor` tests failed with `AttributeError: 'StubNode' object has no attribute 'setName'`
- **Issue:** Both test files share `sys.modules['nuke']`. Since `test_dot_type_distinction.py` is loaded after `test_dot_anchor_name_sync.py` (alphabetical order), its `make_stub_nuke_module()` replaces the nuke module stub. The replacement StubNode lacked `setName()`, which `anchor.py` now calls in the Dot branch of `rename_anchor_to()` and in `mark_dot_as_anchor()`.
- **Fix:** Added `def setName(self, new_name): self._name = new_name` to the StubNode class in `test_dot_type_distinction.py`
- **Files modified:** `tests/test_dot_type_distinction.py`
- **Commit:** 77cc9ef

**2. [Rule 1 - Bug] Test used `'!!!'` as empty-sanitized name — incorrect**
- **Found during:** RED phase verification — `'!!!'` sanitizes to `'___'` (underscores), not empty
- **Fix:** Changed test input to `'   '` (whitespace only); `name.strip()` → `''`, sanitize → `''` → correctly triggers ValueError
- **Files modified:** `tests/test_dot_anchor_name_sync.py`
- **Commit:** 77cc9ef (included in same GREEN commit)

## Self-Check: PASSED

- tests/test_dot_anchor_name_sync.py: FOUND
- anchor.py: FOUND
- link.py: FOUND
- Commit 49a0ba4 (RED): FOUND
- Commit 77cc9ef (GREEN): FOUND
