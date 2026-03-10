---
phase: 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction
verified: 2026-03-05T00:00:00Z
status: passed
score: 8/8 must-haves verified
re_verification: false
---

# Phase 05: DOT_TYPE Link/Local Dot Distinction Verification Report

**Phase Goal:** Fix two UAT-confirmed bugs from Phase 2 by introducing a formal DOT_TYPE distinction between Link Dots (anchor-backed, cross-script capable) and Local Dots (plain-node-backed, script-local only).
**Verified:** 2026-03-05
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A Link Dot (input(0) is an anchor) pasted cross-script reconnects to a same-named anchor in the destination script | VERIFIED | `paste_hidden.py` lines 187-196: `if is_cross_script or not input_node` + `if dot_type == 'link'` gate calls `find_anchor_by_name(display_name)` and `setup_link_node(destination_anchor, node)`. Test `test_link_dot_pasted_cross_script_with_matching_anchor_calls_setup_link_node` passes. |
| 2 | A Local Dot (input(0) is a non-anchor node) pasted cross-script is left disconnected — no reconnect attempt under any circumstances, including same-stem scripts | VERIFIED | `paste_hidden.py` lines 187-198: the `is_cross_script` gate uses FQNN stem comparison (not `find_anchor_node()` return value), so same-stem false positives are blocked. Local Dot falls through to `continue` with no reconnect. Tests `test_local_dot_pasted_cross_script_does_not_call_find_anchor_by_name_or_setup_link_node` and `test_local_dot_pasted_same_stem_false_positive_does_not_reconnect` both pass. |
| 3 | A Local Dot pasted within the same script reconnects to the original source node by identity (PASTE-03 preserved) | VERIFIED | `paste_hidden.py` line 201: `setup_link_node(input_node, node)` is called in the same-script branch (when `not is_cross_script and input_node`). Test `test_local_dot_pasted_same_script_restores_local_label_and_color_after_setup_link_node` verifies `setup_link_node` is called with the source node. |
| 4 | After same-script paste, a Local Dot retains 'Local: \<name\>' label and LOCAL_DOT_COLOR orange tile color | VERIFIED | `paste_hidden.py` lines 203-207: after `setup_link_node()`, checks `DOT_TYPE_KNOB_NAME in node.knobs() and node[DOT_TYPE_KNOB_NAME].getValue() == 'local'`, then restores label and `LOCAL_DOT_COLOR`. Test `test_local_dot_pasted_same_script_restores_local_label_and_color_after_setup_link_node` asserts label is `'Local: My Blur'` and tile_color is `LOCAL_DOT_COLOR`. |
| 5 | DOT_TYPE_KNOB_NAME and LOCAL_DOT_COLOR constants exist in constants.py | VERIFIED | `constants.py` lines 25-26: `DOT_TYPE_KNOB_NAME = 'paste_hidden_dot_type'` and `LOCAL_DOT_COLOR = 0xB35A00FF`. |
| 6 | add_input_knob() in link.py accepts an optional dot_type parameter; when provided, adds a hidden DOT_TYPE string knob alongside KNOB_NAME | VERIFIED | `link.py` line 108: `def add_input_knob(node, dot_type=None):`. Lines 137-141: conditional `nuke.String_Knob(DOT_TYPE_KNOB_NAME)` with `setVisible(False)` and `setValue(dot_type)` when `dot_type is not None`. Three tests in `TestAddInputKnobDotTypeExtension` all pass. |
| 7 | copy_hidden() Path B sets DOT_TYPE='link' for anchor-backed Dots and DOT_TYPE='local' for plain-node-backed Dots | VERIFIED | `paste_hidden.py` line 72: `add_input_knob(node, dot_type='link')` in the `elif is_anchor(input_node):` branch. Line 81: `add_input_knob(node, dot_type='local')` in the `else:` branch. Tests `test_copy_hidden_anchor_backed_dot_calls_add_input_knob_with_dot_type_link` and `test_copy_hidden_plain_node_backed_dot_calls_add_input_knob_with_dot_type_local` pass. |
| 8 | Link Dots always receive ANCHOR_DEFAULT_COLOR (canonical purple) at copy time, not the anchor's custom color | VERIFIED | `paste_hidden.py` line 71: `node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)` immediately after `setup_link_node(input_node, node)` in the anchor branch of `copy_hidden()` Path B. Test `test_copy_hidden_anchor_backed_dot_sets_tile_color_to_anchor_default_color` passes. |

**Score:** 8/8 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `constants.py` | DOT_TYPE_KNOB_NAME and LOCAL_DOT_COLOR constants | VERIFIED | Lines 25-26: both constants present with exact specified values (`'paste_hidden_dot_type'` and `0xB35A00FF`). |
| `link.py` | Extended add_input_knob() with dot_type parameter | VERIFIED | Line 108: `def add_input_knob(node, dot_type=None):`. Lines 113-141: DOT_TYPE_KNOB_NAME removal in re-add cycle (line 115-118) plus conditional knob addition (lines 137-141). Substantive implementation — not a stub. |
| `paste_hidden.py` | copy_hidden() and paste_hidden() Path B with DOT_TYPE branching | VERIFIED | `DOT_TYPE_KNOB_NAME` referenced at lines 13, 171, 172, 203, 204. Both functions have substantive DOT_TYPE branching logic. 165 lines of active code, no stubs or placeholders. |
| `tests/test_dot_type_distinction.py` | Offline unit tests for all DOT_TYPE behaviors | VERIFIED | 16 tests across 4 test classes: `TestAddInputKnobDotTypeExtension` (3), `TestCopyHiddenDotTypeBehavior` (5), `TestPasteHiddenCrossScriptDotTypeBehavior` (4), `TestPasteHiddenBackwardCompatibility` (2), `TestPasteHiddenSameScriptDotTypeBehavior` (2). Class `TestDotTypeDistinction` is not the top-level name — tests are organized across named classes per behavior domain. Confirmed substantive: 839 lines. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| copy_hidden() Path B (paste_hidden.py) | add_input_knob() (link.py) | dot_type='link' or dot_type='local' argument | VERIFIED | Lines 72 and 81 of paste_hidden.py: `add_input_knob(node, dot_type='link')` and `add_input_knob(node, dot_type='local')`. Callers pass the argument; add_input_knob() acts on it at lines 137-141 of link.py. |
| paste_hidden() Path B cross-script gate (paste_hidden.py) | find_anchor_by_name() (anchor.py) | DOT_TYPE_KNOB_NAME == 'link' guard before reconnect attempt | VERIFIED | paste_hidden.py lines 187-195: `if is_cross_script or not input_node:` enclosing `if dot_type == 'link':` then `find_anchor_by_name(display_name)`. The 'link' guard is correctly placed before the call. |
| paste_hidden() Path B same-script path (paste_hidden.py) | LOCAL_DOT_COLOR restoration block | DOT_TYPE_KNOB_NAME == 'local' check after setup_link_node() | VERIFIED | paste_hidden.py lines 201-207: `setup_link_node(input_node, node)` followed by `if (DOT_TYPE_KNOB_NAME in node.knobs() and node[DOT_TYPE_KNOB_NAME].getValue() == 'local'):` which sets label and `LOCAL_DOT_COLOR`. Pattern `DOT_TYPE_KNOB_NAME in node.knobs` present at line 203. |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| XSCRIPT-01 | 05-01-PLAN.md | Link nodes pasted into another script reconnect to an anchor of the same name in the destination script | SATISFIED | paste_hidden() Path B: when `dot_type == 'link'` and `is_cross_script`, `find_anchor_by_name(display_name)` is called and `setup_link_node(destination_anchor, node)` reconnects the Link Dot. Bug 1 (Link Dots never reconnecting cross-script) is fixed. 2 tests verify this directly. |
| XSCRIPT-02 | 05-01-PLAN.md | Hidden-input Dot nodes pasted into another script do not reconnect (distinct from Link behavior) | SATISFIED | paste_hidden() Path B: Local Dots (`dot_type == 'local'`) hit `continue` without calling `find_anchor_by_name` or `setup_link_node` in the cross-script branch. FQNN stem comparison prevents same-stem false positives (Bug 2 fix). 4 tests verify this across variants including same-stem false positive and backward compat. |

**Traceability note:** REQUIREMENTS.md traceability table attributes XSCRIPT-01/02 to "Phase 2 Complete (02-01)". Phase 5's plan also claims these requirement IDs. This is consistent — Phase 2 established the infrastructure; Phase 5 corrects two UAT-confirmed bugs in that infrastructure. The requirements' behavioral definitions are now fully satisfied by the Phase 2 + Phase 5 combination. Both requirements are checked [x] in REQUIREMENTS.md. No orphaned requirements.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| paste_hidden.py | 139 | Comment uses word "placeholders" — refers to placeholder Link nodes left disconnected when no anchor found, which is correct intentional behavior | INFO | Not a code anti-pattern; the comment accurately describes the cross-script no-anchor case. No impact. |

No TODO, FIXME, HACK, empty return, or stub implementations found in any of the four modified files.

---

### Human Verification Required

The following behaviors cannot be verified programmatically because they require a running Nuke session with a real DAG:

#### 1. Link Dot Cross-Script Reconnect (Bug 1)

**Test:** In Nuke, create an anchor (e.g. `Anchor_MyFootage`) pointing to a Read node. Create a Dot node with `hide_input` on, wired to the anchor. Copy the Dot (Ctrl+C via the custom shortcut). Open a second Nuke script that also has an `Anchor_MyFootage`. Paste.
**Expected:** The pasted Dot reconnects to `Anchor_MyFootage` in the destination script, displaying the canonical purple tile color.
**Why human:** Requires live Nuke DAG, actual node graph, and menu.py shortcut registration to be in place.

#### 2. Local Dot Same-Stem False Positive Prevention (Bug 2)

**Test:** In Nuke, create a Dot with `hide_input` on, wired to a `Blur1` node (not an anchor). Copy. Open a second Nuke script that also has a `Blur1` node and has the same filename stem (e.g. both scripts are `untitled.nk` opened separately). Paste.
**Expected:** The pasted Dot is left disconnected — it does NOT wire to the destination `Blur1`.
**Why human:** Requires two Nuke instances, specific filename conditions, and live graph state.

#### 3. Local Dot Appearance After Same-Script Paste

**Test:** In Nuke, copy a Local Dot (input is a plain node). Paste in the same script.
**Expected:** The pasted Dot shows burnt orange (`0xB35A00FF`) tile color and a `Local: <source name>` label in the node graph.
**Why human:** Visual color appearance and label rendering must be confirmed in the DAG.

---

### Gaps Summary

No gaps. All 8 must-have truths are VERIFIED by code inspection. All 4 required artifacts exist, are substantive, and are wired. Both key links (copy-time DOT_TYPE stamping, paste-time DOT_TYPE gating) are confirmed connected end-to-end. The full test suite (27 tests: 16 new + 11 pre-existing) passes with zero failures.

The three human verification items above are confidence checks for the live Nuke environment — they are not blockers to marking this phase complete, as the offline test suite fully exercises all code paths.

---

_Verified: 2026-03-05_
_Verifier: Claude (gsd-verifier)_
