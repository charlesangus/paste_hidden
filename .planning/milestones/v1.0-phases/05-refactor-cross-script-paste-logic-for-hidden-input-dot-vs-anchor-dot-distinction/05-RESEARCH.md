# Phase 5: Refactor Cross-Script Paste Logic for Hidden-Input Dot vs Anchor Dot Distinction - Research

**Researched:** 2026-03-05
**Domain:** Python / Nuke plugin — copy-paste semantics, knob metadata, node visual identity
**Confidence:** HIGH — all findings derived from direct codebase analysis; no external library research required

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Dot subtype terminology and distinction
Two Dot subtypes must be formally distinguished:
- **Link Dot** — a Dot whose `input(0)` is an anchor node. Cross-script capable. Should reconnect to same-named anchor on cross-script paste.
- **Local Dot** — a Dot whose `input(0)` is a non-anchor node (e.g. Blur1). Script-local only. Must NOT reconnect cross-script.

Add an explicit DOT_TYPE knob (string) to distinguish them at paste time. Set to `'link'` for Link Dots and `'local'` for Local Dots in `copy_hidden()` Path B. Do NOT rely solely on FQNN suffix inspection — use the explicit knob.

#### Cross-script Link node reconnect (Bug 1 fix)
When a Link node (NoOp or PostageStamp with KNOB_NAME set) is pasted cross-script and a same-named anchor exists in the destination script:
- **Rewire the existing pasted node** to the destination anchor (do not create a fresh node). Since we use NoOps for all links now, the type mismatch concern is moot.
- Use `_extract_display_name_from_fqnn()` to get the display name, then `find_anchor_by_name()` to locate the destination anchor.
- If no matching anchor exists → leave the pasted node disconnected silently. No error, no dialog.

This logic lives in `paste_hidden()` Path B. Currently Path B does `continue` for cross-script; it needs a check: if FQNN points to an anchor (or DOT_TYPE == 'link'), attempt name-based reconnect.

#### Local Dot cross-script behaviour (Bug 2 fix)
When a Local Dot is pasted cross-script:
- Do NOT attempt reconnection under any circumstances.
- Retain the "Local: ..." label and Local Dot orange color on the pasted node — it remains visually identifiable as a disconnected Local Dot from another script.
- Same-stem false positives (two scripts named "untitled") are an acceptable edge case and do not require engineering effort.

#### Local Dot same-script behaviour (preserve PASTE-03)
When a Local Dot is pasted within the same script:
- Reconnect to the original source node by identity (via FQNN/KNOB_NAME). This is PASTE-03 and currently works — do not break it.

#### Visual differentiation: Local Dot vs Link Dot
| Dot type | Label prefix | Tile color |
|----------|-------------|------------|
| Local Dot | `"Local: <source node name>"` | Subdued/muted orange — not bright warning orange, not close to Nuke's default Blur grey |
| Link Dot | `"Link: <anchor display name>"` | Always anchor default purple (`ANCHOR_DEFAULT_COLOR = 0x6f3399ff`) — not the specific anchor's custom color |

Exact orange hex is Claude's discretion; constraint: muted/burnt orange, not bright, not close to Blur's default Nuke grey.

### Claude's Discretion
- Exact orange hex value for Local Dots (constrained above)
- Knob name constant for DOT_TYPE (consistent with naming convention in constants.py, e.g. `DOT_TYPE_KNOB_NAME`)
- How to handle pre-existing nodes that lack the DOT_TYPE knob (backward compat fallback: treat as Local Dot if FQNN doesn't point to an anchor; treat as Link Dot otherwise)
- Whether to update existing hidden-input Dots' visual appearance when the new code runs, or only on next copy

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 5 fixes two UAT-confirmed bugs from Phase 2 by introducing a formal distinction between two hidden-input Dot subtypes: **Link Dots** (whose `input(0)` is an anchor node, cross-script capable) and **Local Dots** (whose `input(0)` is any other node, script-local only). The fix is a pure correctness refactor — no new capabilities are added.

**Bug 1** (XSCRIPT-01 gap): Link nodes pasted cross-script silently fail to reconnect because `paste_hidden()` Path B does `continue` for all cross-script cases. The fix adds a DOT_TYPE-gated cross-script reconnect attempt that rewires the pasted node in-place using `find_anchor_by_name()`.

**Bug 2** (XSCRIPT-02 gap): Local Dots erroneously reconnect cross-script when the source and destination scripts share the same filename stem (e.g. both named `untitled.nk`). This happens because `find_anchor_node()` compares script-stem prefixes — same-stem scripts produce a false positive match, causing `setup_link_node()` to wire to an unrelated same-named node in the destination. The fix bypasses `find_anchor_node()` entirely for cross-script Local Dots by using the DOT_TYPE knob as a gate, making same-stem collisions structurally impossible.

**Primary recommendation:** Add `DOT_TYPE_KNOB_NAME` to `constants.py`, set it in `copy_hidden()` Path B's `if/else is_anchor(input_node)` branches alongside the existing `KNOB_NAME`, override label/color to match the Dot type, and add a cross-script reconnect block inside `paste_hidden()` Path B's `if not input_node:` guard.

---

## Standard Stack

No external libraries or packages. This phase is pure Python within the Nuke plugin environment.

### Core (Project-Internal)
| Module | File | Purpose | Role in Phase 5 |
|--------|------|---------|----------------|
| `constants.py` | `constants.py` | Shared string constants and color values | Add `DOT_TYPE_KNOB_NAME` and `LOCAL_DOT_COLOR` constants |
| `link.py` | `link.py` | Node predicates, knob setup helpers | `add_input_knob()`, `setup_link_node()`, `find_anchor_node()` |
| `paste_hidden.py` | `paste_hidden.py` | Copy/paste orchestration | Both `copy_hidden()` and `paste_hidden()` Path B |
| `anchor.py` | `anchor.py` | Anchor lookup | `find_anchor_by_name()` already imported by `paste_hidden` |

---

## Architecture Patterns

### Established Pattern: Hidden Knob as Node Metadata
`constants.py` defines knob name constants; `add_input_knob()` in `link.py` creates hidden knobs at copy time. Paste-time code reads these knobs to determine behavior. The DOT_TYPE knob follows this exact pattern.

Existing example: `DOT_ANCHOR_KNOB_NAME = 'paste_hidden_dot_anchor'` — a hidden Boolean knob set at copy time, read at paste time.

**Pattern for DOT_TYPE:**
```python
# constants.py — follows DOT_ANCHOR_KNOB_NAME naming convention
DOT_TYPE_KNOB_NAME = 'paste_hidden_dot_type'
LOCAL_DOT_COLOR = 0xB35A00FF  # burnt orange: muted, not alarming, not close to grey
```

### Established Pattern: Three-Path copy_hidden() / paste_hidden()
`copy_hidden()` and `paste_hidden()` each have three labeled code paths (Path A, B, C). Path B handles `HIDDEN_INPUT_CLASSES` nodes (Dot, PostageStamp, NoOp with `hide_input` set). This phase modifies only Path B in both functions.

### Established Pattern: Cross-Script Reconnect in Path A/C
`paste_hidden()` Path A/C already has a cross-script reconnect block:
```python
if is_anchor(node) and node.Class() != 'Dot':
    display_name = _extract_display_name_from_fqnn(node[KNOB_NAME].getText())
    if display_name:
        destination_anchor = find_anchor_by_name(display_name)
        if destination_anchor:
            link_node = nuke.createNode('NoOp')
            setup_link_node(destination_anchor, link_node)
            link_node.setXYpos(node.xpos(), node.ypos())
            selected_nodes.remove(node)
            selected_nodes.append(link_node)
            nuke.delete(node)
            continue
    continue
```

**Path B is different**: it rewires the existing pasted node in-place, it does NOT create a new node and delete the old one. This is because the pasted Dot/NoOp is already the correct class — no type mismatch concern, and no need to manage the `selected_nodes` list.

### Anti-Pattern to Avoid: Creating a New Node in Path B
Path A/C creates a new NoOp and deletes the pasted anchor placeholder. Path B must NOT do this — it rewires the existing pasted node. Using the Path A/C pattern in Path B would break the selection management and leave a dangling node.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Finding anchor by display name | Custom scan loop | `find_anchor_by_name()` in `anchor.py` (already imported) |
| Extracting anchor name from FQNN | Custom string parsing | `_extract_display_name_from_fqnn()` in `paste_hidden.py` (module-level function) |
| Detecting cross-script vs same-script | Script stem comparison | `find_anchor_node()` returning `None` (already handles this) |
| Adding hidden knobs | Inline knob creation | `add_input_knob()` extended with optional `dot_type` parameter |
| Determining if a Dot is an anchor | Class check or name check | `is_anchor()` in `link.py` |

---

## Common Pitfalls

### Pitfall 1: Breaking PASTE-03 (same-script Local Dot reconnect)
**What goes wrong:** The DOT_TYPE check accidentally gates or skips the same-script reconnect path, causing Local Dots to not reconnect when pasted in the same script.
**Why it happens:** Placing the DOT_TYPE check at the wrong nesting level — outside the `if not input_node:` guard instead of inside it.
**How to avoid:** The DOT_TYPE cross-script logic MUST be nested inside `if not input_node:`. The same-script path (`setup_link_node(input_node, node)` when `input_node` is truthy) is untouched.
**Warning signs:** Test for PASTE-03 fails; Local Dot pasted in same-script appears disconnected.

### Pitfall 2: setup_link_node() Overwrites Label/Color on Same-Script Paste
**What goes wrong:** `paste_hidden()` Path B same-script case calls `setup_link_node(source_node, dot)`, which resets the label to `"Link: <name>"` and color to `find_node_color(source_node)`. This erases the `"Local: "` prefix and orange color established at copy time.
**Why it happens:** `setup_link_node()` always writes its own label and color — it does not check DOT_TYPE.
**How to avoid:** After `setup_link_node(input_node, node)` in the same-script path, check `DOT_TYPE_KNOB_NAME` and restore Local appearance if `'local'`:
```python
setup_link_node(input_node, node)
if (DOT_TYPE_KNOB_NAME in node.knobs()
        and node[DOT_TYPE_KNOB_NAME].getValue() == 'local'):
    source_label = input_node['label'].getText() or input_node.name()
    node['label'].setValue(f"Local: {source_label}")
    node['tile_color'].setValue(LOCAL_DOT_COLOR)
```
**Warning signs:** After same-script paste, Local Dot shows `"Link: "` prefix or wrong color.

### Pitfall 3: DOT_TYPE Knob Destroyed by add_input_knob()
**What goes wrong:** `add_input_knob()` removes and re-adds `TAB_NAME` and `KNOB_NAME` knobs to keep them at the end of the knob list. If DOT_TYPE is added *before* `add_input_knob()` is called, it will be positioned before the tab/knob pair and survive the removal (since `add_input_knob()` only removes `TAB_NAME` and `KNOB_NAME`). However, if the intention is for DOT_TYPE to be added *inside* `add_input_knob()`, the logic must remove/re-add it there too.
**Why it happens:** `add_input_knob()` manages only two knobs; DOT_TYPE must either be handled inside it or added reliably after.
**How to avoid:** Extend `add_input_knob()` with an optional `dot_type=None` parameter. When `dot_type` is provided, `add_input_knob()` adds `DOT_TYPE_KNOB_NAME` as a hidden String_Knob after `KNOB_NAME`. All existing callers pass no `dot_type` and are unaffected. Only `copy_hidden()` Path B passes `dot_type='link'` or `dot_type='local'`.
**Warning signs:** DOT_TYPE knob missing on pasted nodes; backward compat fallback fires when it shouldn't.

### Pitfall 4: Link Dot Color Set to Anchor's Custom Color Instead of Default Purple
**What goes wrong:** `setup_link_node(anchor, dot)` calls `find_node_color(anchor)`, which reads the anchor's actual `tile_color` knob. If the anchor has a custom color (e.g. from a backdrop), the Link Dot gets that color, not `ANCHOR_DEFAULT_COLOR`.
**Why it happens:** `setup_link_node()` was designed to propagate the source node's color. For Link Dots, the intent is always the canonical anchor purple.
**How to avoid:** After `setup_link_node(input_node, node)` in the Link Dot branch of `copy_hidden()` Path B, override color explicitly:
```python
node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)
```
**Warning signs:** Link Dots appear in custom anchor colors or backdrop colors instead of purple.

### Pitfall 5: Backward Compat Fallback Fires for New Nodes
**What goes wrong:** Pre-Phase-5 nodes lack `DOT_TYPE_KNOB_NAME`. The fallback must correctly identify them as Link or Local by FQNN inspection. A malformed FQNN (e.g. empty string or `Anchor_` with empty suffix) must not trigger a spurious reconnect.
**Why it happens:** `_extract_display_name_from_fqnn()` returns `''` (empty string) for `'shotA.Anchor_'` — and `if display_name:` evaluates empty string as falsy, correctly treating it as no-match.
**How to avoid:** Use the existing `_extract_display_name_from_fqnn()` guard without modification: `if display_name:` already handles the empty-suffix edge case.
**Warning signs:** Reconnect attempt fires for malformed FQNNs; backward compat fallback triggers on new nodes that have `DOT_TYPE_KNOB_NAME`.

### Pitfall 6: Same-Stem Script False Positive (Bug 2 Root Cause — Must Not Recur)
**What goes wrong:** `find_anchor_node()` compares the script-stem prefix of the stored FQNN against the current script. If both scripts have the same stem (e.g. `untitled`), the prefix matches and `find_anchor_node()` returns a node from the destination script — a completely unrelated node with the same name.
**Why it happens:** `find_anchor_node()` was designed for same-script identity lookup; it is not safe to use for cross-script Local Dots.
**How to avoid:** For Local Dots, NEVER call `find_anchor_node()` cross-script. The DOT_TYPE gate ensures that when `input_node is None` and `DOT_TYPE == 'local'`, we immediately `continue` without any reconnect attempt. This makes same-stem false positives structurally impossible.
**Warning signs:** Local Dot pasted cross-script reconnects to a same-named node in the destination.

---

## Code Examples

### Pattern 1: add_input_knob() Extended with dot_type Parameter (link.py)

```python
# link.py — extend add_input_knob() with optional dot_type parameter
def add_input_knob(node, dot_type=None):
    if not is_anchor(node):
        add_link_reconnect_knob(node)

    # remove our custom knobs to make sure they're at the end
    try:
        node.removeKnob(node[KNOB_NAME])
    except Exception:
        pass
    try:
        node.removeKnob(node[TAB_NAME])
    except Exception:
        pass
    try:
        node.removeKnob(node[DOT_TYPE_KNOB_NAME])
    except Exception:
        pass

    tab = nuke.Tab_Knob(TAB_NAME)
    tab.setFlag(nuke.INVISIBLE)
    tab.setVisible(False)
    node.addKnob(tab)

    knob = nuke.String_Knob(KNOB_NAME)
    knob.setVisible(False)
    node.addKnob(knob)

    if dot_type is not None:
        dot_type_knob = nuke.String_Knob(DOT_TYPE_KNOB_NAME)
        dot_type_knob.setVisible(False)
        dot_type_knob.setValue(dot_type)
        node.addKnob(dot_type_knob)
```

Note: `DOT_TYPE_KNOB_NAME` must be imported from `constants` at the top of `link.py`.

### Pattern 2: copy_hidden() Path B with DOT_TYPE branching (paste_hidden.py)

```python
# copy_hidden() Path B — set DOT_TYPE and correct label/color per subtype
elif node.Class() in HIDDEN_INPUT_CLASSES and node['hide_input'].getValue():
    input_node = node.input(0)
    if input_node is None or input_node in selected_nodes:
        stored_fqnn = ""
        add_input_knob(node)
    elif is_anchor(input_node):
        # Link Dot: anchor-backed, cross-script capable
        stored_fqnn = get_fully_qualified_node_name(input_node)
        setup_link_node(input_node, node)
        node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)  # always canonical purple
        add_input_knob(node, dot_type='link')
    else:
        # Local Dot: plain-node-backed, same-script only
        stored_fqnn = get_fully_qualified_node_name(input_node)
        setup_link_node(input_node, node)
        source_label = input_node['label'].getText() or input_node.name()
        node['label'].setValue(f"Local: {source_label}")
        node['tile_color'].setValue(LOCAL_DOT_COLOR)
        add_input_knob(node, dot_type='local')
    node[KNOB_NAME].setText(stored_fqnn)
```

### Pattern 3: paste_hidden() Path B with cross-script DOT_TYPE gate (paste_hidden.py)

```python
# paste_hidden() Path B — DOT_TYPE-gated cross-script reconnect
elif node.Class() in HIDDEN_INPUT_CLASSES:
    if not input_node:
        # Cross-script: check DOT_TYPE knob (or fall back to FQNN inspection)
        stored_fqnn = node[KNOB_NAME].getText()
        dot_type = None
        if DOT_TYPE_KNOB_NAME in node.knobs():
            dot_type = node[DOT_TYPE_KNOB_NAME].getValue()
        else:
            # Backward compat: infer type from FQNN
            display_name_from_fqnn = _extract_display_name_from_fqnn(stored_fqnn)
            dot_type = 'link' if display_name_from_fqnn else 'local'

        if dot_type == 'link':
            display_name = _extract_display_name_from_fqnn(stored_fqnn)
            if display_name:
                destination_anchor = find_anchor_by_name(display_name)
                if destination_anchor:
                    setup_link_node(destination_anchor, node)
                    # Ensure Link Dot color is canonical purple after reconnect
                    node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)
        # Local Dot: silent no-op — do not reconnect
        continue

    # Same-script: reconnect by identity
    setup_link_node(input_node, node)
    # Restore Local Dot appearance if applicable
    if (DOT_TYPE_KNOB_NAME in node.knobs()
            and node[DOT_TYPE_KNOB_NAME].getValue() == 'local'):
        source_label = input_node['label'].getText() or input_node.name()
        node['label'].setValue(f"Local: {source_label}")
        node['tile_color'].setValue(LOCAL_DOT_COLOR)
```

### Pattern 4: Constants additions (constants.py)

```python
# constants.py — new constants for Phase 5
DOT_TYPE_KNOB_NAME = 'paste_hidden_dot_type'
LOCAL_DOT_COLOR = 0xB35A00FF  # burnt orange: muted, not alarming, not close to Blur grey
```

---

## Root Cause Analysis (Both Bugs)

### Bug 1: Link Dots Do Not Reconnect Cross-Script
**Root cause:** `paste_hidden()` Path B does `continue` for ALL cross-script cases (`if not input_node: continue`). There is no subtype distinction — Link Dots are treated identically to Local Dots.
**Code location:** `paste_hidden.py`, `paste_hidden()` Path B, lines 158–163.
**Fix:** Insert DOT_TYPE-gated reconnect logic inside the `if not input_node:` block before `continue`.

### Bug 2: Local Dots Erroneously Reconnect Cross-Script (Same-Stem Scripts)
**Root cause:** When pasted cross-script, `find_anchor_node()` is NOT called for HIDDEN_INPUT_CLASSES nodes in the current code. Instead, the bug is triggered if both source and destination scripts have the same stem (e.g. `untitled.nk`). In that case `find_anchor_node()` returns a non-None node (same-name node in destination), and `setup_link_node()` erroneously reconnects to it.

Wait — re-examining the current code: `paste_hidden()` Path B calls `find_anchor_node(node)` at line 118 for ALL nodes including HIDDEN_INPUT_CLASSES. So for same-stem scripts, `find_anchor_node()` returns the destination's `Blur1`, causing `setup_link_node(blur1_in_dest, dot)` to fire.

**Code location:** `paste_hidden.py`, `paste_hidden()` Path B, lines 155–163.
**Fix:** DOT_TYPE gate prevents reaching `setup_link_node()` for Local Dots when cross-script, regardless of stem matching.

---

## Decisions for Planner (Claude's Discretion Items)

### 1. DOT_TYPE knob name constant
**Recommended:** `DOT_TYPE_KNOB_NAME = 'paste_hidden_dot_type'`
**Rationale:** Follows the project's established `paste_hidden_` prefix pattern (see `DOT_ANCHOR_KNOB_NAME = 'paste_hidden_dot_anchor'`).

### 2. Local Dot orange hex value
**Recommended:** `LOCAL_DOT_COLOR = 0xB35A00FF`
**Rationale:** Burnt orange (RGB 179, 90, 0) — muted, clearly recognizable as orange without being alarming or close to Nuke's default dark grey tile color. Distinct from the anchor purple (`0x6F3399FF`). Not vivid enough to suggest error state.

### 3. add_input_knob() extension vs separate helper
**Recommended:** Extend `add_input_knob()` with `dot_type=None` parameter.
**Rationale:** Follows the existing single-responsibility pattern of this helper. All existing callers pass no `dot_type` and are unaffected. The DOT_TYPE knob must be managed in the same remove/re-add cycle as `KNOB_NAME` to avoid positional drift — this is cleanest inside `add_input_knob()`.

### 4. Same-script Local Dot label/color restoration
**Recommended:** Restore `"Local: "` prefix and `LOCAL_DOT_COLOR` after `setup_link_node()` call in the same-script path.
**Rationale:** `setup_link_node()` overwrites label and color. If the DOT_TYPE knob says `'local'`, the visual identity established at copy time should be preserved on paste. Failing to do this creates an inconsistency: the Dot's appearance changes from Local to Link on paste within the same script.

### 5. Existing nodes without DOT_TYPE knob (backward compat)
**Recommended:** Infer type from FQNN: `display_name_from_fqnn is not None` → treat as Link Dot; `None` → treat as Local Dot.
**Rationale:** This exactly mirrors the distinction that would have been made had the Phase 5 code been present at copy time. Pre-Phase-5 Link Dots stored anchor FQNNs (matching `Anchor_` prefix); Local Dots stored plain node FQNNs (no prefix match).

### 6. Whether to update existing nodes' visual appearance
**Recommended:** Only on next copy (do not retroactively update existing nodes).
**Rationale:** There is no reliable way to trigger a visual update on all existing hidden-input Dots without iterating `nuke.allNodes()` on plugin load — which would be surprising and potentially slow. On next copy/paste cycle, nodes will receive the correct label, color, and DOT_TYPE knob.

---

## File Change Summary for Planner

| File | Change Type | What Changes |
|------|-------------|--------------|
| `constants.py` | Add 2 constants | `DOT_TYPE_KNOB_NAME`, `LOCAL_DOT_COLOR` |
| `link.py` | Extend function | `add_input_knob()` gets `dot_type=None` parameter; adds `DOT_TYPE_KNOB_NAME` knob when provided; must also import `DOT_TYPE_KNOB_NAME` from constants |
| `paste_hidden.py` | Modify 2 functions | `copy_hidden()` Path B: set DOT_TYPE, override label/color; `paste_hidden()` Path B: add cross-script DOT_TYPE gate + same-script label restoration; imports `DOT_TYPE_KNOB_NAME` and `LOCAL_DOT_COLOR` |
| Tests | New test file | Tests for both copy_hidden DOT_TYPE branching and paste_hidden cross-script DOT_TYPE gate (following offline stub pattern from `test_cross_script_paste.py`) |

No changes needed to `anchor.py`, `labels.py`, `util.py`, or `menu.py`.

---

## Open Questions

1. **Does `copy_hidden()` Path B `stored_fqnn = ""` branch (when `input_node is None or input_node in selected_nodes`) need a DOT_TYPE?**
   - What we know: When `stored_fqnn = ""`, paste does nothing useful with the FQNN. `_extract_display_name_from_fqnn("")` returns `None`. Backward compat fallback would treat this as Local Dot.
   - What's unclear: Should `add_input_knob(node)` be called with `dot_type='local'` in this branch, or left as `add_input_knob(node)` with no dot_type?
   - Recommendation: Call `add_input_knob(node)` with no `dot_type` in the empty-FQNN branch. These nodes will never meaningfully reconnect (their FQNN is `""`), so the knob is moot.

2. **Does `setup_link_node()` need to be called at all in the same-script path for the label/color fix?**
   - What we know: `setup_link_node()` sets `hide_input=True`, color, label, calls `add_input_knob()`, sets `KNOB_NAME`, and calls `setInput(0, input_node)`. The `setInput(0, input_node)` is the critical reconnect operation.
   - Recommendation: Keep calling `setup_link_node()` for the reconnect and `KNOB_NAME` update. Then fix up label/color afterward for Local Dots. Do not refactor `setup_link_node()` to accept a `dot_type` parameter — caller-side fixup is simpler and less risky.

---

## Sources

### Primary (HIGH confidence)
All findings derived from direct source code analysis of the project codebase. No external library research was required.

- `paste_hidden.py` — full analysis of `copy_hidden()` and `paste_hidden()` Path B
- `link.py` — `add_input_knob()`, `setup_link_node()`, `find_anchor_node()`, `is_anchor()`
- `constants.py` — naming conventions, existing constants
- `anchor.py` — `find_anchor_by_name()`, `all_anchors()`
- `tests/test_cross_script_paste.py` — offline stub pattern (established in Phase 2)
- `.planning/phases/02-cross-script-paste/02-UAT.md` — bug reports with exact reproduction steps
- `.planning/phases/05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction/05-CONTEXT.md` — locked decisions and integration points

---

## Metadata

**Confidence breakdown:**
- Root cause analysis: HIGH — traced exact code paths for both bugs with logic verification
- Architecture/change plan: HIGH — derived from existing patterns, no speculation
- Code examples: HIGH — derived from codebase conventions, verified against actual function signatures
- Orange hex choice: MEDIUM — reasoning is sound but color perception is subjective; user constraint says muted/burnt orange

**Research date:** 2026-03-05
**Valid until:** Stable — no external dependencies; only invalidated by changes to `paste_hidden.py`, `link.py`, `constants.py`
