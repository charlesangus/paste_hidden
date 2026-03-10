---
phase: 01-copy-paste-semantics
verified: 2026-03-04T00:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
---

# Phase 1: Copy-Paste Semantics Verification Report

**Phase Goal:** Copy and paste behave predictably for file nodes and hidden-input Dots, with the correct link node class used for each stream type
**Verified:** 2026-03-04
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1 | Copying a LINK_CLASSES file node with an existing anchor, or a hidden-input Dot whose input is an anchor, produces a Link node wired to that anchor on paste | VERIFIED | paste_hidden.py Path A scans allNodes() for anchor by identity; Path B detects is_anchor(input_node) and calls setup_link_node; paste_hidden() resolves via find_anchor_node() and creates link node |
| 2 | Copying a LINK_CLASSES file node with no anchor produces a Link node pointing directly to that file node on paste (legacy fallback) | VERIFIED | paste_hidden.py Path A falls back to get_fully_qualified_node_name(node) when anchor_for_node is None; paste creates link via get_link_class_for_source(file_node) |
| 3 | Copying a hidden-input Dot whose input is a non-anchor node reconnects it to that source on paste (same-script only); no anchor created | VERIFIED | paste_hidden.py Path B: is_anchor(input_node) is False path stores FQNN via setup_link_node; paste Path B calls setup_link_node(input_node, node) for reconnect |
| 4 | Pasting a Camera node produces a NoOp link; pasting a 2D Read produces a PostageStamp link | VERIFIED | detect_link_class_for_node() returns LINK_CLASSES['Camera'] = 'NoOp'; stored on anchor knob; get_link_class_for_source(anchor) dispatches to get_link_class_for_anchor() which reads stored 'NoOp' |
| 5 | If stream-type detection cannot be implemented simply, all non-Dot links fall back to NoOp and no regressions occur | VERIFIED | detect_link_class_for_node(): None input returns 'NoOp'; API errors return 'NoOp' via try/except; unknown channel types return 'NoOp'; get_link_class_for_anchor() returns 'NoOp' when knob absent |

**Score:** 5/5 success criteria verified

### Plan 01-01 Must-Have Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A LINK_CLASSES file node (e.g. Read) connected to an anchor results in PostageStamp stored on that anchor's link-class knob | VERIFIED | detect_link_class_for_node() returns LINK_CLASSES['Read'] = 'PostageStamp'; _store_link_class_on_anchor() writes this to the hidden knob |
| 2 | A Camera node connected to an anchor results in NoOp stored on that anchor's link-class knob | VERIFIED | detect_link_class_for_node() returns LINK_CLASSES['Camera'] = 'NoOp'; stored via _store_link_class_on_anchor() at create_anchor_named() time |
| 3 | get_link_class_for_source() returns the stored class when called with an anchor node (reads knob, not LINK_CLASSES dict) | VERIFIED | link.py line 109-110: `if source_node is not None and is_anchor(source_node): return get_link_class_for_anchor(source_node)` — dispatches to knob read before any dict lookup |
| 4 | Stream-type detection falls back to NoOp when detection is inconclusive (LINK-04) | VERIFIED | detect_link_class_for_node(): None returns 'NoOp'; channels() exception returns 'NoOp'; no 2D channels returns 'NoOp'; try/except wraps all channel inspection |

### Plan 01-02 Must-Have Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Copying a LINK_CLASSES file node that has an anchor stores the anchor's FQNN (not the file node's own FQNN) | VERIFIED | paste_hidden.py lines 42-47: scans allNodes() for candidate where is_anchor(candidate) and candidate.input(0) is node; stores get_fully_qualified_node_name(anchor_for_node) |
| 2 | Copying a LINK_CLASSES file node with no anchor stores the file node's own FQNN (legacy path unchanged) | VERIFIED | paste_hidden.py line 50: else branch stores get_fully_qualified_node_name(node) |
| 3 | Copying a hidden-input Dot whose input(0) is an anchor stores the anchor FQNN and marks it for Link behavior | VERIFIED | paste_hidden.py lines 60-64: is_anchor(input_node) branch stores get_fully_qualified_node_name(input_node) and calls setup_link_node(input_node, node) |
| 4 | Copying a hidden-input Dot whose input(0) is a non-anchor node stores that node's FQNN for legacy identity reconnect | VERIFIED | paste_hidden.py lines 66-70: else branch stores FQNN and calls setup_link_node |
| 5 | Pasting a stored anchor FQNN creates a link node using the class from the anchor's stored knob | VERIFIED | paste_hidden.py line 115: link_class = get_link_class_for_source(input_node) — input_node is the resolved anchor; get_link_class_for_source dispatches to get_link_class_for_anchor() |
| 6 | Pasting a stored file-node FQNN creates a link node using get_link_class_for_source(file_node) — legacy path unchanged | VERIFIED | Same paste Path A/C code path; when input_node is a file node (not anchor), get_link_class_for_source falls through to LINK_CLASSES.get() |
| 7 | A legacy Dot (non-anchor input) pastes by reconnecting to the stored node by identity (same-script); cross-script disconnects silently | VERIFIED | paste_hidden.py lines 123-129: Path B calls find_anchor_node() which returns None for cross-script; `if not input_node: continue` handles silent disconnect; same-script resolves and calls setup_link_node |

**Score:** 11/11 must-have truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `constants.py` | ANCHOR_LINK_CLASS_KNOB_NAME constant | VERIFIED | Line 30: `ANCHOR_LINK_CLASS_KNOB_NAME = 'paste_hidden_anchor_link_class'` — exact value matches plan spec |
| `link.py` | detect_link_class_for_node(), get_link_class_for_anchor(), updated get_link_class_for_source() | VERIFIED | All three functions present; detect_link_class_for_node has NoOp fallback with try/except; get_link_class_for_source dispatches to anchor knob first |
| `anchor.py` | create_anchor_named() stores link class on anchor knob at creation time | VERIFIED | _store_link_class_on_anchor() helper at line 234; called from create_anchor_named() at line 276, after tile_color set |
| `paste_hidden.py` | Three-path copy_hidden() classification and updated paste_hidden() | VERIFIED | Path A (LINK_CLASSES), Path B (HIDDEN_INPUT_CLASSES with anchor split), Path C (is_anchor); paste reads via get_link_class_for_source |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `anchor.py:create_anchor_named()` | `link.py:detect_link_class_for_node()` | call at anchor creation time | WIRED | anchor.py line 39 imports detect_link_class_for_node; called in _store_link_class_on_anchor at line 241; _store_link_class_on_anchor called from create_anchor_named at line 276 |
| `link.py:get_link_class_for_source()` | anchor knob ANCHOR_LINK_CLASS_KNOB_NAME | is_anchor() dispatch | WIRED | link.py line 109-110: is_anchor check then get_link_class_for_anchor(source_node); get_link_class_for_anchor reads ANCHOR_LINK_CLASS_KNOB_NAME at line 95 |
| `paste_hidden.py:copy_hidden()` | `link.py:is_anchor()` | anchor detection branch for Dot nodes | WIRED | paste_hidden.py line 13 imports is_anchor; line 43 uses is_anchor(candidate); line 60 uses is_anchor(input_node) for Dot branch split |
| `paste_hidden.py:paste_hidden()` | `link.py:get_link_class_for_source()` | reads link class for paste via updated dispatch | WIRED | paste_hidden.py line 16 imports get_link_class_for_source; line 115: `link_class = get_link_class_for_source(input_node)` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| LINK-01 | 01-01 | 2D stream nodes use PostageStamp as the link node class | SATISFIED | detect_link_class_for_node() returns 'PostageStamp' for Read (LINK_CLASSES lookup) and for nodes with rgba/depth/forward channels |
| LINK-02 | 01-01 | Deep and 3D stream nodes (e.g. Camera) use NoOp as the link node class | SATISFIED | LINK_CLASSES maps Camera, DeepRead, ReadGeo, Camera2-4, GeoImport to 'NoOp'; detect_link_class_for_node returns these values |
| LINK-03 | 01-01 | Camera links no longer incorrectly produce PostageStamp nodes when pasted | SATISFIED | detect_link_class_for_node returns 'NoOp' for Camera; stored on anchor at creation; get_link_class_for_source reads knob not LINK_CLASSES at paste time |
| LINK-04 | 01-01 | Fallback: if stream-type detection is not simple and performant, all non-Dot links use NoOp | SATISFIED | detect_link_class_for_node returns 'NoOp' for None input, API errors (try/except), and unrecognised channel types |
| PASTE-01 | 01-02 | Copying a LINK_CLASSES file node or anchor-pointed Dot creates a Link node pointing to the anchor on paste | SATISFIED | paste_hidden.py Path A anchor scan + Path B anchor Dot branch + paste_hidden Path A/C link creation |
| PASTE-03 | 01-02 | Hidden-input Dot with non-anchor input reconnects to that source by identity on paste (same-script only) | SATISFIED | paste_hidden.py Path B: non-anchor else branch stores FQNN; paste Path B: setup_link_node reconnects if same-script; silent skip if cross-script |

**Orphaned requirements (mapped to Phase 1 in REQUIREMENTS.md but not in any plan's frontmatter):**

| Requirement | Status in REQUIREMENTS.md | In ROADMAP Phase 1 | In Plan Frontmatter | Code Implementation |
|-------------|--------------------------|-------------------|--------------------|--------------------|
| PASTE-04 | Phase 1 / Pending | Not listed | Not claimed | Incidentally present: find_anchor_node() returns None for cross-script prefix mismatch; paste_hidden Path B `if not input_node: continue` silently disconnects |

PASTE-04 behavior is implemented as a structural side effect of the cross-script guard in `find_anchor_node()`. The behavior satisfies the requirement. It is not blocked. However, REQUIREMENTS.md still shows `[ ]` (unchecked) and the traceability table shows "Pending" — these should be updated to reflect the implementation.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| paste_hidden.py | 106 | Comment uses word "placeholder" to describe Nuke node left in DAG | Info | No impact — "placeholder node" refers to the temporarily-pasted Nuke node that stays when cross-script; this is a description of expected behavior, not a code placeholder |

No functional anti-patterns found. All `return None` occurrences in link.py and anchor.py are legitimate conditional returns (cross-script guard, empty-backdrop check, absent-anchor guard), not stubs. No TODO/FIXME comments present.

### Human Verification Required

#### 1. Camera anchor paste produces NoOp link (not PostageStamp)

**Test:** In a live Nuke session, create a Camera node. Create an anchor attached to that Camera. Copy the Camera node. Paste. Observe the created link node class.
**Expected:** A NoOp link node is created wired to the anchor. No PostageStamp node appears.
**Why human:** Cannot run Nuke API in the verifier environment; requires live Nuke session with the plugin loaded.

#### 2. Read anchor paste produces PostageStamp link

**Test:** In a live Nuke session, create a Read node. Create an anchor attached to that Read. Copy the Read node. Paste. Observe the created link node class.
**Expected:** A PostageStamp link node is created wired to the anchor.
**Why human:** Same reason — requires live Nuke session.

#### 3. Hidden-input Dot cross-script silent disconnect (PASTE-04)

**Test:** In script A, create any non-anchor node and a hidden-input Dot wired to it. Copy the Dot. Open script B. Paste. Verify the pasted Dot has no input connected and no error is raised.
**Expected:** Dot pastes with no input connection and no error or dialog.
**Why human:** Cross-script test requires two Nuke scripts and paste between them.

#### 4. Channel inspection fallback for unknown node types

**Test:** In a live Nuke session, create a node type not in LINK_CLASSES (e.g. a Merge2 with only rgb output), attach it to an anchor, copy and paste. Observe the link class created.
**Expected:** PostageStamp link (2D channel detection via rgba prefix) or NoOp if channels() raises or returns no 2D channels.
**Why human:** Requires live Nuke API call to channels() on an actual node.

### Gaps Summary

No gaps. All 11 must-have truths are VERIFIED against the actual codebase. All 4 key links are WIRED. All 6 explicitly-claimed requirements (PASTE-01, PASTE-03, LINK-01, LINK-02, LINK-03, LINK-04) are SATISFIED by code evidence.

One administrative gap: PASTE-04 behavior is implemented but REQUIREMENTS.md still shows it as `[ ] Pending`. This is a documentation inconsistency, not a code gap. The implementation at paste_hidden.py lines 123-128 plus find_anchor_node()'s cross-script guard in link.py lines 210-212 satisfies PASTE-04.

All four modified files (`constants.py`, `link.py`, `anchor.py`, `paste_hidden.py`) pass `ast.parse()` with no syntax errors. Commits d13aebf, 2fcdba5, f156b30, f046c79 exist in git history.

---

_Verified: 2026-03-04_
_Verifier: Claude (gsd-verifier)_
