# Phase 2: Cross-Script Paste - Research

**Researched:** 2026-03-04
**Domain:** Nuke Python plugin — cross-script paste reconnection and dead-code removal
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Name matching**
- Exact match, case-sensitive — anchor names in Nuke are unique and user-assigned; predictable behavior is preferred
- Extract anchor name from the stored FQNN knob (last segment after splitting on `.`) — no new storage needed
- Name-based cross-script reconnect applies to NoOp anchors only; Dot anchors are positional and do not participate (consistent with XSCRIPT-02)
- Multiple-match collision is a non-issue: Nuke enforces unique node names within a script

**No-match behavior**
- When no anchor with the matching name exists in the destination script, leave the pasted node as a disconnected placeholder
- The placeholder retains its Link node identity (NoOp with the reconnect knob and stored FQNN) — user can reconnect manually or it serves as a visible reminder

**Link class / PostageStamp removal**
- All links are NoOp — the PostageStamp distinction was abandoned
- The stored link_class knob on anchors and any related LINK_CLASSES logic should be removed as part of this phase
- The planner should trace all reads of the stored link_class knob and the LINK_CLASSES dict to identify what can be deleted; paste_hidden.py already hardcodes `nuke.createNode('NoOp')` so the creation path may already be correct

**Dot cross-script behavior (XSCRIPT-02 / PASTE-04)**
- Hidden-input Dots pasted cross-script are already silently disconnected by the existing `continue` in Path B of paste_hidden.py
- Confirm this satisfies XSCRIPT-02 and PASTE-04; no new code expected unless the test reveals a gap

### Claude's Discretion

None specified.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| XSCRIPT-01 | Link nodes pasted into another script reconnect to an anchor of the same name in the destination script | Requires replacing the `continue` in Path A/C of `paste_hidden()` with a name-based lookup via `find_anchor_by_name()`; name is extracted from the stored FQNN's last segment with `ANCHOR_PREFIX` stripped |
| XSCRIPT-02 | Hidden-input Dot nodes pasted into another script do not reconnect (distinct from Link behavior) | Path B already silently disconnects via `continue` when `find_anchor_node()` returns `None` — verify this covers the cross-script case and PASTE-04 |
</phase_requirements>

---

## Summary

Phase 2 is a targeted modification of `paste_hidden.py` with accompanying dead-code removal in `constants.py`, `link.py`, and `anchor.py`. The cross-script reconnect logic for Link nodes (NoOp anchors) inserts into the existing Path A/C branch of `paste_hidden()`, replacing a bare `continue` with a name-based lookup: extract the display name from the stored FQNN, call `find_anchor_by_name()` in the destination script, and either wire the link via `setup_link_node()` or leave it as a disconnected placeholder. Hidden-input Dot cross-script behavior (XSCRIPT-02/PASTE-04) appears to already be handled by the existing `continue` in Path B.

The CONTEXT.md also calls for removing the `LINK_CLASSES` dict and `ANCHOR_LINK_CLASS_KNOB_NAME` constant and any associated read-paths. An audit of the current codebase (2026-03-04) shows these are largely dead: `ANCHOR_LINK_CLASS_KNOB_NAME` is defined in `constants.py` but **not imported by any other file**; `LINK_CLASSES` is imported and used in `paste_hidden.py` as a node-class filter (`LINK_CLASSES.keys()`). The dead code removal task must be scoped carefully — `LINK_CLASSES` still drives the Path A routing in `copy_hidden()` and `paste_hidden()`, and may need to be replaced with an equivalent predicate rather than simply deleted.

**Primary recommendation:** Implement cross-script reconnect in `paste_hidden()` Path A/C; confirm Path B already satisfies XSCRIPT-02; then remove `ANCHOR_LINK_CLASS_KNOB_NAME` and `LINK_CLASSES` dead code after auditing all reads.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `nuke` (Nuke Python API) | project-determined | Node graph access, `allNodes()`, `toNode()`, `createNode()` | The only API available in a Nuke plugin |
| `anchor.py` (internal) | project | `find_anchor_by_name()`, `anchor_display_name()` | Already implements the name lookup the cross-script path needs |
| `link.py` (internal) | project | `find_anchor_node()`, `setup_link_node()`, `get_fully_qualified_node_name()` | Established FQNN and link-wiring patterns |
| `paste_hidden.py` (internal) | project | Sole entry point for paste behavior | Single integration point for all changes |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `constants.py` (internal) | project | `KNOB_NAME`, `LINK_CLASSES`, `ANCHOR_PREFIX`, `ANCHOR_LINK_CLASS_KNOB_NAME` | Read for cleanup target identification |

### Alternatives Considered

None applicable — this is a single-plugin Nuke project with no external library choices.

**Installation:** No new packages required.

---

## Architecture Patterns

### Existing Project Structure (relevant files)

```
paste_hidden/
├── paste_hidden.py     # Entry point — copy_hidden(), paste_hidden()
├── link.py             # FQNN helpers, find_anchor_node(), setup_link_node()
├── anchor.py           # find_anchor_by_name(), anchor_display_name(), all_anchors()
├── constants.py        # KNOB_NAME, LINK_CLASSES, ANCHOR_LINK_CLASS_KNOB_NAME, ANCHOR_PREFIX
└── tests/
    ├── __init__.py
    ├── test_link_probe.py
    └── test_anchor_store_link_class.py
```

### Pattern 1: FQNN Cross-Script Detection (existing)

**What:** `find_anchor_node()` in `link.py` already detects the cross-script case. It splits the stored FQNN on `.`, compares the script-name prefix from the stored FQNN against the prefix from the current script, and returns `None` if they differ.

**FQNN format:** `<script_stem>.<node_full_name>` where `<script_stem>` is `nuke.root().name().split('.')[0]`. For a node `Anchor_MyFootage` in a script named `shotA.nk`, the FQNN is `shotA.Anchor_MyFootage`.

**Name extraction:** The last segment of the FQNN (after splitting on `.`) is `Anchor_MyFootage`. Stripping `ANCHOR_PREFIX` (`'Anchor_'`) gives the display name `'MyFootage'`, which matches what `anchor_display_name(node)` returns for NoOp anchors.

```python
# Source: link.py (existing) — find_anchor_node() cross-script detection
if prefix_from_knob != prefix_from_current:
    # we are in a different script and/or Group, do nothing
    return None
```

**Cross-script name extraction for Phase 2:**
```python
# Extract display name from stored FQNN for cross-script lookup
stored_fqnn = node[KNOB_NAME].getText()
fqnn_segments = stored_fqnn.split('.')
node_full_name = fqnn_segments[-1]          # e.g. 'Anchor_MyFootage'
# Strip ANCHOR_PREFIX to get display name used by find_anchor_by_name()
from constants import ANCHOR_PREFIX
if node_full_name.startswith(ANCHOR_PREFIX):
    display_name = node_full_name[len(ANCHOR_PREFIX):]  # e.g. 'MyFootage'
    destination_anchor = find_anchor_by_name(display_name)
    # destination_anchor is None if no match, or the anchor to wire to
```

### Pattern 2: Path A/C Modification in paste_hidden() (new)

**What:** The existing Path A/C in `paste_hidden()` handles `LINK_CLASSES` file nodes and anchor nodes. When `find_anchor_node()` returns `None`, it currently does `continue` (leaves placeholder in place, no wiring). Phase 2 inserts a cross-script reconnect attempt before that `continue`.

**Current code (paste_hidden.py:103–116):**
```python
if node.Class() in LINK_CLASSES.keys() or is_anchor(node):
    if not input_node:
        continue   # <-- THIS bare continue is replaced in Phase 2
    ...
    link_node = nuke.createNode('NoOp')
    setup_link_node(input_node, link_node)
```

**Phase 2 logic:** When `input_node` is `None` AND the node `is_anchor(node)` (meaning a Link node, i.e., a NoOp that was an anchor copy), attempt the name-based lookup. If found, create the link; if not, leave the placeholder (still `continue`, just with the lookup attempt first).

**Critical gate: only NoOp anchors participate.** Dot anchors are positional and must NOT be included in the cross-script reconnect. The `is_anchor(node)` check in the paste branch already covers both, so the cross-script path must additionally confirm `node.Class() != 'Dot'` or use `is_anchor(node) and node.Class() != 'Dot'` to exclude Dot anchors.

### Pattern 3: Path B Already Handles XSCRIPT-02

**What:** `paste_hidden()` Path B (hidden-input Dot, `HIDDEN_INPUT_CLASSES`):
```python
elif node.Class() in HIDDEN_INPUT_CLASSES:
    if not input_node:
        continue   # cross-script: silently disconnected
    setup_link_node(input_node, node)
```

When a hidden-input Dot is pasted cross-script, `find_anchor_node()` returns `None`, and `continue` leaves the Dot disconnected. This already satisfies XSCRIPT-02 and PASTE-04. **No code change expected** — only a confirmation test or comment.

### Pattern 4: Dead Code Removal Scope

The CONTEXT.md identifies these as removal targets:

| Symbol | Location | Current Status | Safe to Remove? |
|--------|----------|----------------|-----------------|
| `ANCHOR_LINK_CLASS_KNOB_NAME` | `constants.py:30` | Defined but NOT imported anywhere | Yes — dead constant |
| `LINK_CLASSES` dict | `constants.py:7–16` | Imported by `paste_hidden.py`; drives Path A routing | No — must replace routing first |
| `LINK_CLASSES` usage in `paste_hidden.py` | `paste_hidden.py:11,37,103` | Used as node-class predicate (`LINK_CLASSES.keys()`) | Remove after routing replacement |
| `get_link_class_for_source()` | `link.py:56–63` | Called by `anchor.py` `create_from_anchor()` | Keep — still used; returns `'Dot'` or `'NoOp'` |
| `probe_stream_type_via_can_set_input()` | `link.py` (added in 01-03) | May not be called now that detection is simplified | Audit before removing |
| `detect_link_class_for_node()` | `link.py` (added in 01-01) | Superseded by probe; check if still called | Audit before removing |
| `_store_link_class_on_anchor()` | `anchor.py` | Stores class on anchor knob; check if still called | Audit before removing |

**Key insight:** `LINK_CLASSES` currently acts as a set of node classes that trigger the "replace with link" path. Removing it requires replacing `node.Class() in LINK_CLASSES.keys()` with an equivalent predicate. Based on the current codebase direction, the set of trigger classes can be encoded as a constant tuple (e.g., `LINK_SOURCE_CLASSES = ('Read', 'DeepRead', 'ReadGeo', 'Camera', 'Camera2', 'Camera3', 'Camera4', 'GeoImport')`) or derived from a simpler rule.

### Anti-Patterns to Avoid

- **Dot anchor cross-script reconnect:** Do NOT attempt name-based lookup for Dot anchors in Path B. Dot anchors are positional references, not named links. The CONTEXT explicitly states they must be silently disconnected.
- **FQNN segment assumptions for nested Groups:** `node.fullName()` returns `Group1.NodeName` for nodes inside Groups. The FQNN then becomes `script.Group1.NodeName`, and the last segment is still just the node's own name — this is safe for top-level anchors (which is the common case). However, the name extraction `fqnn_segments[-1]` is correct regardless of nesting depth.
- **Re-detecting link class at paste time:** The codebase established "detect once at creation, read from stored knob" as the pattern. Phase 2 abandons the stored knob for cross-script (since it can't be read from the source script), but uses `nuke.createNode('NoOp')` directly — consistent with `paste_hidden.py:111` which already hardcodes `NoOp`.
- **Removing `LINK_CLASSES` before replacing its routing use:** `LINK_CLASSES.keys()` is used as the node-class gate for Path A. Removing the dict without replacing the gate breaks copy/paste for file nodes entirely.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-script anchor lookup by display name | Custom node search loop | `find_anchor_by_name(display_name)` (anchor.py:103) | Already implemented; handles all anchor types, sorted, case-sensitive match |
| Anchor display name extraction | Custom name parsing | `anchor_display_name(node)` (anchor.py:91) | Returns node name minus `ANCHOR_PREFIX` for NoOp anchors; returns label for Dot anchors |
| FQNN anchor name extraction | String slicing variants | `fqnn.split('.')[-1]` then strip `ANCHOR_PREFIX` | FQNN format is `script.Anchor_Name`; last segment is always the node full name |
| Link node wiring | Custom knob-setting | `setup_link_node(input_node, link_node)` (link.py:131) | Sets `hide_input`, color, label, `KNOB_NAME`, and `setInput(0)` atomically |
| Same-script anchor resolution | Re-implementing FQNN compare | `find_anchor_node(link_node)` (link.py:148) | Already handles Group nesting and script-name comparison |

**Key insight:** All primitives needed for Phase 2 already exist. The implementation is wiring them together inside `paste_hidden()` Path A/C, plus one audit-and-delete pass for dead code.

---

## Common Pitfalls

### Pitfall 1: Dot Anchor Inclusion in Cross-Script Reconnect

**What goes wrong:** If the cross-script name lookup runs on all `is_anchor(node)` nodes including Dot anchors, pasted Dot anchors attempt to reconnect by label-name to a same-named Dot anchor in the destination — this violates XSCRIPT-02 and the CONTEXT decision that "Dot anchors are positional and do not participate."

**Why it happens:** `is_anchor()` returns `True` for both NoOp anchors (`Anchor_` prefix) and Dot anchors (`DOT_ANCHOR_KNOB_NAME` present or labeled Dot). The Path A/C guard `is_anchor(node)` would include both.

**How to avoid:** Gate the cross-script name lookup with an additional `node.Class() != 'Dot'` check, or use `node.name().startswith(ANCHOR_PREFIX)` directly for the cross-script path.

**Warning signs:** A pasted Dot anchor reconnects to a labeled Dot in the destination script when it should remain disconnected.

### Pitfall 2: FQNN Last Segment Contains Group Nesting

**What goes wrong:** A node inside a Group has `fullName()` = `'Group1.Anchor_MyFootage'`. The FQNN becomes `'scriptA.Group1.Anchor_MyFootage'`. Splitting on `.` and taking `[-1]` gives `'Anchor_MyFootage'` — this is correct. But if someone splits expecting exactly two segments (script + node), they will misparse Group-nested nodes.

**Why it happens:** `get_fully_qualified_node_name()` uses `node.fullName()` which includes the full Group path.

**How to avoid:** Always use `fqnn.split('.')[-1]` (last segment only) for the node name, never `fqnn.split('.')[1]`.

**Warning signs:** Name lookup fails for anchor nodes that live inside a Group node.

### Pitfall 3: LINK_CLASSES Removal Breaks Path A Gate

**What goes wrong:** If `LINK_CLASSES` is removed from `constants.py` and the `import` in `paste_hidden.py` is updated without replacing `LINK_CLASSES.keys()` in the `if node.Class() in LINK_CLASSES.keys()` check, a `NameError` is raised at paste time for any LINK_CLASSES node.

**Why it happens:** `LINK_CLASSES` is used in two places in `paste_hidden.py` (lines 37 and 103) as a node-class filter, not as a value source.

**How to avoid:** Replace `LINK_CLASSES.keys()` with a new constant (e.g., `LINK_SOURCE_CLASSES`) that is a frozenset or tuple of the same class names, before deleting the dict. The mapping values (PostageStamp, NoOp) are no longer needed.

**Warning signs:** `NameError: name 'LINK_CLASSES' is not defined` at paste time.

### Pitfall 4: Empty FQNN in the Knob

**What goes wrong:** The stored FQNN is `""` for cut operations and for nodes with no stored info. Splitting `""` on `.` yields `['']`, and `[''][-1]` is `''`. Calling `find_anchor_by_name('')` returns `None` (safe), but stripping `ANCHOR_PREFIX` from `''` gives `''`, which may trigger an empty-name lookup.

**Why it happens:** `copy_hidden()` stores `""` when `cut=True`.

**How to avoid:** Guard the cross-script name extraction with `if stored_fqnn:` before splitting. The existing `if not input_node: continue` already handles `None` from `find_anchor_node()` but does not guard against the empty FQNN case explicitly.

**Warning signs:** Spurious `find_anchor_by_name('')` calls; or unexpected reconnect to an anchor whose display name is empty.

---

## Code Examples

### Extract Display Name from Stored FQNN

```python
# Source: analysis of link.py:get_fully_qualified_node_name() and anchor.py:anchor_display_name()
# FQNN format: '<script_stem>.<node.fullName()>'  e.g. 'shotA.Anchor_MyFootage'
# For Group-nested nodes: 'shotA.Group1.Anchor_MyFootage'
from constants import ANCHOR_PREFIX, KNOB_NAME

stored_fqnn = node[KNOB_NAME].getText()
if stored_fqnn:
    node_full_name = stored_fqnn.split('.')[-1]  # last segment = node name
    if node_full_name.startswith(ANCHOR_PREFIX):
        display_name = node_full_name[len(ANCHOR_PREFIX):]  # 'MyFootage'
    else:
        display_name = node_full_name  # fallback (legacy file node FQNN)
```

### Cross-Script Reconnect Logic (Phase 2 insertion point)

```python
# Insert into paste_hidden() Path A/C, replacing the bare `continue`
# when input_node is None (cross-script case).
# This block runs when: (node.Class() in LINK_SOURCE_CLASSES or is_anchor(node))
#                       AND input_node is None
#                       AND node.Class() != 'Dot'  (exclude Dot anchors)
from anchor import find_anchor_by_name

stored_fqnn = node[KNOB_NAME].getText()
destination_anchor = None
if stored_fqnn and is_anchor(node) and node.Class() != 'Dot':
    node_full_name = stored_fqnn.split('.')[-1]
    if node_full_name.startswith(ANCHOR_PREFIX):
        display_name = node_full_name[len(ANCHOR_PREFIX):]
        destination_anchor = find_anchor_by_name(display_name)

if not destination_anchor:
    continue  # No match: leave disconnected placeholder

# Match found: wire to destination anchor
nukescripts.clear_selection_recursive()
node["selected"].setValue(True)
link_node = nuke.createNode('NoOp')
setup_link_node(destination_anchor, link_node)
link_node.setXYpos(node.xpos(), node.ypos())
selected_nodes.remove(node)
selected_nodes.append(link_node)
nuke.delete(node)
```

### Confirming Path B Already Handles XSCRIPT-02

```python
# Source: paste_hidden.py:118–124 (existing, no change needed)
elif node.Class() in HIDDEN_INPUT_CLASSES:
    if not input_node:
        continue  # cross-script Dot: silently disconnected — satisfies XSCRIPT-02
    setup_link_node(input_node, node)
```

`find_anchor_node()` in `link.py` returns `None` when `prefix_from_knob != prefix_from_current`, which is the cross-script case. The `if not input_node: continue` at line 123 already handles it. PASTE-04 (non-anchor Dot pasted cross-script) is satisfied through the same path since `find_anchor_node()` also returns `None` when the source node no longer exists in the current script.

### Dead Code Removal: ANCHOR_LINK_CLASS_KNOB_NAME

```python
# constants.py — safe to delete (not imported anywhere in current codebase):
# ANCHOR_LINK_CLASS_KNOB_NAME = 'paste_hidden_anchor_link_class'

# Verify before removing:
# grep -r 'ANCHOR_LINK_CLASS_KNOB_NAME' .   # should show only constants.py
```

### Dead Code Removal: LINK_CLASSES → LINK_SOURCE_CLASSES

```python
# Replace in constants.py:
# OLD:
LINK_CLASSES = {
    "Read": "PostageStamp",
    "DeepRead": "NoOp",
    ...
}
# NEW (values no longer needed since all links are NoOp):
LINK_SOURCE_CLASSES = frozenset({
    "Read", "DeepRead", "ReadGeo",
    "Camera", "Camera2", "Camera3", "Camera4",
    "GeoImport",
})

# Update paste_hidden.py imports and usages:
# from constants import KNOB_NAME, LINK_SOURCE_CLASSES, HIDDEN_INPUT_CLASSES
# if node.Class() in LINK_SOURCE_CLASSES:          (copy_hidden Path A)
# if node.Class() in LINK_SOURCE_CLASSES or is_anchor(node):   (paste_hidden Path A/C)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `LINK_CLASSES` dict with class → link class mapping | All links are NoOp; `LINK_CLASSES` serves only as a set of trigger classes | Phase 1 (01-01/01-03) | `LINK_CLASSES` values no longer used; safe to collapse to a set |
| Channel-prefix heuristic for stream detection | `canSetInput` probe (01-03) — but now moot since all links are NoOp | Phase 1 (01-03) | `probe_stream_type_via_can_set_input()`, `detect_link_class_for_node()` may be dead |
| Cross-script paste: `continue` (leave placeholder) | Cross-script paste: name-based reconnect attempt for NoOp Links | Phase 2 (this phase) | Link nodes in destination script auto-wire if anchor name matches |

**Deprecated/outdated:**
- `ANCHOR_LINK_CLASS_KNOB_NAME`: defined in `constants.py`, not imported anywhere — dead constant from the "store class on anchor knob" design that was partially superseded.
- `probe_stream_type_via_can_set_input()`, `detect_link_class_for_node()`, `get_link_class_for_anchor()`, `_store_link_class_on_anchor()`: added in Phase 1 (01-01, 01-03) for the PostageStamp/NoOp distinction. Since all links are now NoOp, these functions may be unused dead code. **The planner must audit these before scheduling removal** — `get_link_class_for_source()` is still called by `anchor.py:create_from_anchor()` and must be kept (it returns `'Dot'` or `'NoOp'` based on whether the source is a Dot node).

---

## Open Questions

1. **Are `probe_stream_type_via_can_set_input()`, `detect_link_class_for_node()`, `get_link_class_for_anchor()`, and `_store_link_class_on_anchor()` truly dead?**
   - What we know: These functions were added in 01-01 and 01-03. The current `get_link_class_for_source()` in `link.py` (lines 56–63) returns `'Dot'` or `'NoOp'` without calling any of them. The grep for `ANCHOR_LINK_CLASS_KNOB_NAME` shows it is not imported outside `constants.py`.
   - What's unclear: Whether these functions still exist in `link.py` and `anchor.py` (the summaries list them as created, but the current `link.py` content does not include them — they may have already been removed or never committed).
   - Recommendation: The planner should include a code-audit task at the start of Phase 2 to `grep` for these function names and confirm their presence/absence before scheduling any removal.

2. **Does the `PASTE-04` requirement traceability need updating?**
   - What we know: PASTE-04 is listed as "Pending" in REQUIREMENTS.md and assigned to Phase 1, but the existing Path B `continue` in `paste_hidden.py` already satisfies it. Phase 2 CONTEXT says to confirm this satisfies PASTE-04.
   - What's unclear: Whether the planner should update REQUIREMENTS.md to mark PASTE-04 complete in Phase 2.
   - Recommendation: Include a task to confirm and mark PASTE-04 complete if the existing behavior passes review.

3. **What happens when a file node (not an anchor) is pasted cross-script?**
   - What we know: Path A handles LINK_SOURCE_CLASSES nodes (e.g., Read). If the stored FQNN points to a file node (legacy fallback path: no anchor found at copy time), `find_anchor_node()` returns `None` cross-script. The new cross-script logic only applies when `is_anchor(node)` — file nodes are not anchors, so the name-based lookup would not be attempted.
   - What's unclear: Whether this is intentional (file node cross-script paste leaves a disconnected placeholder) or a gap.
   - Recommendation: Based on CONTEXT decisions — name-based reconnect is for NoOp anchors only. File node cross-script paste leaving a placeholder is consistent and intentional. No action needed.

---

## Sources

### Primary (HIGH confidence)

- `paste_hidden/paste_hidden.py` (read 2026-03-04) — current Path A/B/C logic, cross-script `continue` locations
- `paste_hidden/link.py` (read 2026-03-04) — `find_anchor_node()` FQNN logic, `setup_link_node()`, `get_fully_qualified_node_name()`
- `paste_hidden/anchor.py` (read 2026-03-04) — `find_anchor_by_name()`, `anchor_display_name()`, `all_anchors()`
- `paste_hidden/constants.py` (read 2026-03-04) — `LINK_CLASSES`, `ANCHOR_LINK_CLASS_KNOB_NAME`, `ANCHOR_PREFIX`, `KNOB_NAME`
- `.planning/phases/02-cross-script-paste/02-CONTEXT.md` (read 2026-03-04) — locked decisions for Phase 2
- `.planning/REQUIREMENTS.md` (read 2026-03-04) — XSCRIPT-01, XSCRIPT-02, PASTE-04 definitions
- `.planning/phases/01-copy-paste-semantics/01-01-SUMMARY.md` (read 2026-03-04) — ANCHOR_LINK_CLASS_KNOB_NAME origin
- `.planning/phases/01-copy-paste-semantics/01-03-SUMMARY.md` (read 2026-03-04) — probe function origin, PostageStamp → NoOp shift

### Secondary (MEDIUM confidence)

None — all findings verified directly from source code.

### Tertiary (LOW confidence)

None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no external dependencies; all code read directly
- Architecture: HIGH — all patterns verified from source code, FQNN format confirmed from `get_fully_qualified_node_name()` implementation
- Pitfalls: HIGH — derived from reading the actual code paths that would be modified; no guesswork

**Research date:** 2026-03-04
**Valid until:** 2026-04-04 (codebase is stable; changes are confined to this project)
