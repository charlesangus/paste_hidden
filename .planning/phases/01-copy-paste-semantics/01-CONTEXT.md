# Phase 1: Copy-Paste Semantics - Context

**Gathered:** 2026-03-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Redefine how `copy_hidden()` and `paste_hidden()` classify and process nodes: file nodes (Read, Camera, etc.) use the anchor system on paste; hidden-input Dot nodes reconnect to their source by identity without creating anchors or links; link node class (PostageStamp vs NoOp) is derived programmatically and stored on the anchor rather than looked up from a static dict at paste time. Scope is same-script behavior only — cross-script paste is Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Anchor lookup at copy time (PASTE-01)
- Scan all anchors in the script; find one whose `input(0)` is the file node being copied
- Only direct `input(0)` counts — do not traverse multi-hop paths
- If multiple anchors have the same file node as input(0): use first found (good enough for common case)
- If no anchor found: proceed to auto-anchor creation (PASTE-02 path)

### Auto-anchor creation (PASTE-02)
- When pasting a file node with no existing anchor: prompt the user for an anchor name (same dialog as manual anchor creation, same name suggestion logic from file path)
- Anchor is placed right below the original file node in the graph
- The pasted copy of the file node is deleted — only the link node remains after paste
- Each paste does a fresh anchor lookup: if anchor was created during a previous paste of the same node, it will be found and reused on subsequent pastes

### Hidden-input Dot classification and reconnection (PASTE-03)
- A hidden-input Dot is: `hide_input == True`, NOT an anchor, NOT a link to an anchor
- Reconnection behavior is unchanged — continue using FQNN-based lookup
- Change required: ensure hidden-input Dots never enter the anchor/link creation path (guard in copy/paste routing)
- When source node is not found on paste: leave the Dot disconnected and apply a warning label to it
- When copying: if a node has a warning label AND has a connected input(0), clear the warning label before copying

### Stream type detection for link class (LINK-01, LINK-02, LINK-03)
- Do NOT use `LINK_CLASSES` dict to determine link class for anchored nodes — anchors can be attached to anything, not just known file node classes
- Detect the appropriate link class programmatically at anchor creation time (e.g. by inspecting the source node's output type/format)
- Store the determined link class as a knob on the anchor node itself at creation time
- At paste time, read the stored class from the anchor knob — do not rely on `anchor.input(0).Class()` as the anchor's input may not be a file node
- `LINK_CLASSES` dict remains valid for the legacy direct-file-node paste path (non-anchor copy of a LINK_CLASSES member)

### Claude's Discretion
- Exact warning label text for disconnected Dots
- Knob name and type for storing link class on anchor
- Which Nuke API to use for programmatic stream type detection (output format introspection)
- Fallback link class if stream detection is inconclusive (NoOp is the safe default)

</decisions>

<specifics>
## Specific Ideas

- Warning label on disconnected Dot should be visually obvious — cleared automatically on next copy when the input is restored
- Stream type detection at anchor creation: the anchor's source node is available at creation time, so detection can be thorough; no need to re-detect at paste time

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_link_class_for_source(source_node)` in `link.py`: currently does LINK_CLASSES lookup — will need to be extended or replaced with anchor-stored class lookup for the anchor path
- `setup_link_node(input_node, link_node)` in `link.py`: reusable as-is for wiring links
- `add_input_knob(node)` in `link.py`: reusable for adding hidden metadata knobs to anchors
- `is_anchor()`, `is_link()` predicates in `link.py`: reusable classification

### Established Patterns
- Node metadata stored as hidden knobs (INVISIBLE, setVisible(False)) — follow this pattern for the new link-class knob on anchors
- `KNOB_NAME` (`copy_hidden_input_node`) stores FQNN as a String_Knob — same pattern for link class storage
- All constants in `constants.py` — add new knob name there

### Integration Points
- `copy_hidden()` in `paste_hidden.py`: routing logic needs new branch for "file node with anchor" and "file node without anchor"
- `paste_hidden()` in `paste_hidden.py`: needs to read link class from anchor knob instead of calling `get_link_class_for_source(anchor_node)`
- `create_anchor_named()` in `anchor.py`: anchor creation already handles name dialog and positioning — the new stream-detection and link-class storage belongs here
- `HIDDEN_INPUT_CLASSES` in `constants.py`: currently includes PostageStamp, Dot, NoOp — the Dot guard for PASTE-03 interacts with this list

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-copy-paste-semantics*
*Context gathered: 2026-03-03*
