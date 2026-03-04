# Phase 2: Cross-Script Paste - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

When a node is pasted into a different Nuke script: Link nodes (NoOp) reconnect to an anchor of the same name in the destination script if one exists, and leave a disconnected placeholder if not. Hidden-input Dot nodes are left disconnected silently — no reconnection attempt.

</domain>

<decisions>
## Implementation Decisions

### Name matching
- Exact match, case-sensitive — anchor names in Nuke are unique and user-assigned; predictable behavior is preferred
- Extract anchor name from the stored FQNN knob (last segment after splitting on `.`) — no new storage needed
- Name-based cross-script reconnect applies to NoOp anchors only; Dot anchors are positional and do not participate (consistent with XSCRIPT-02)
- Multiple-match collision is a non-issue: Nuke enforces unique node names within a script

### No-match behavior
- When no anchor with the matching name exists in the destination script, leave the pasted node as a disconnected placeholder
- The placeholder retains its Link node identity (NoOp with the reconnect knob and stored FQNN) — user can reconnect manually or it serves as a visible reminder

### Link class / PostageStamp removal
- All links are NoOp — the PostageStamp distinction was abandoned
- The stored link_class knob on anchors and any related LINK_CLASSES logic should be removed as part of this phase
- The planner should trace all reads of the stored link_class knob and the LINK_CLASSES dict to identify what can be deleted; paste_hidden.py already hardcodes `nuke.createNode('NoOp')` so the creation path may already be correct

### Dot cross-script behavior (XSCRIPT-02 / PASTE-04)
- Hidden-input Dots pasted cross-script are already silently disconnected by the existing `continue` in Path B of paste_hidden.py
- Confirm this satisfies XSCRIPT-02 and PASTE-04; no new code expected unless the test reveals a gap

</decisions>

<specifics>
## Specific Ideas

No specific references — standard implementation expected.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `find_anchor_by_name(display_name)` (anchor.py:103) — searches current script by display name; can be used directly for the cross-script reconnect lookup
- `anchor_display_name(node)` (anchor.py:91) — returns label for Dot anchors, node name for NoOp anchors
- `get_fully_qualified_node_name(node)` (link.py:17) — used to build FQNNs; useful for understanding the naming scheme
- `setup_link_node(input_node, link_node)` (link.py:131) — wires and configures a link node; reuse for cross-script reconnect

### Established Patterns
- FQNN format: `<script_stem>.<node_full_name>` (link.py:19) — cross-script detection is already done by comparing script prefix; name extraction is the last segment
- `paste_hidden()` Path A/C (paste_hidden.py:103–116) — the existing cross-script `continue` is what needs replacing with the name-lookup path for Links
- `paste_hidden()` Path B (paste_hidden.py:118–124) — Dot cross-script already silently disconnects via `continue`; likely no change needed

### Integration Points
- `paste_hidden()` in paste_hidden.py is the sole entry point for paste behavior; the cross-script reconnect logic inserts into the Path A/C branch when `find_anchor_node()` returns `None`

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-cross-script-paste*
*Context gathered: 2026-03-04*
