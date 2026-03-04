# Phase 1: Copy-Paste Semantics - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Redefine how `copy_hidden()` and `paste_hidden()` classify and process nodes: LINK_CLASSES file nodes route through the anchor system (or fall back to direct-file-node links); hidden-input Dots pointing to an anchor behave as Link nodes; hidden-input Dots pointing to non-anchor nodes use the legacy identity-reconnect path; link node class (PostageStamp vs NoOp) is detected at anchor creation time and stored on the anchor. Scope is same-script behavior only — cross-script paste for Link nodes is handled by FQNN lookup which already works; cross-script for legacy Dots disconnects silently.

</domain>

<decisions>
## Implementation Decisions

### Anchor routing trigger
- Only LINK_CLASSES members (Read, Camera, DeepRead, ReadGeo, etc.) enter the anchor routing path
- Non-LINK_CLASSES nodes are not affected even if an anchor happens to be connected to them

### LINK_CLASSES file node copy/paste (PASTE-01)
- At copy time: scan for an anchor whose `input(0)` is the file node being copied (identity check)
- If anchor found: store the anchor's FQNN — paste creates a Link to the anchor
- If no anchor found: store the file node's own FQNN — paste creates a Link directly to the file node (legacy behaviour, unchanged from current code)
- No anchor creation dialog; no auto-creation of anchors

### Hidden-input Dot classification (PASTE-01 / PASTE-03)
- A hidden-input Dot whose `input(0)` IS an anchor: treated as a Link node — gets `Link:` label, stores anchor FQNN, reconnects cross-script via anchor name
- A hidden-input Dot whose `input(0)` is NOT an anchor: legacy reconnect — stores source FQNN, reconnects same-script only by identity, no label change
- Cross-script legacy Dot: disconnect silently, no error (PASTE-04)

### Warning labels
- No warning labels on disconnected Dots — skip silently

### Stream type detection for link class (LINK-01/02/03)
- Detect the appropriate link class (PostageStamp vs NoOp) at anchor creation time, not at paste time
- Detection uses Nuke API introspection on the source node (e.g. channel inspection)
- Store the detected class as a hidden knob on the anchor node
- At paste time: read the stored class from the anchor knob — do not call `get_link_class_for_source()` with the anchor itself
- Rationale: anchors are created seldom, links pasted often — put overhead at creation time
- LINK_CLASSES dict remains valid for the direct-file-node paste path (no anchor case)

### Claude's Discretion
- Knob name and type for storing link class on anchor
- Which Nuke API to use for stream type detection (channel inspection recommended)
- Fallback link class if detection is inconclusive (NoOp is the safe default per LINK-04)
- Cut behaviour for LINK_CLASSES nodes (preserve existing cut=True path)

</decisions>

<specifics>
## Specific Ideas

- Anchors are created seldom, links pasted often — detection overhead belongs at anchor creation time
- The direct-file-node fallback (no anchor) must preserve existing behaviour exactly

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_link_class_for_source(source_node)` in `link.py`: currently does LINK_CLASSES lookup — needs updating to read from anchor knob when source is an anchor
- `setup_link_node(input_node, link_node)` in `link.py`: reusable as-is for wiring links
- `add_input_knob(node)` in `link.py`: reusable for adding hidden metadata knobs
- `is_anchor()`, `is_link()` predicates in `link.py`: reusable classification
- `create_anchor_named()` in `anchor.py`: anchor creation entry point — stream detection and knob storage belongs here
- `suggest_anchor_name()` in `anchor.py`: reusable name suggestion from file path

### Established Patterns
- Node metadata stored as hidden knobs (`setVisible(False)`) — follow this for the link-class knob on anchors
- All constants in `constants.py` — add new knob name there
- `KNOB_NAME` stores FQNN as a String_Knob — same pattern for link class storage

### Integration Points
- `copy_hidden()` in `paste_hidden.py`: needs new branch checking for anchor before falling through to direct-file-node path; hidden-input Dot branch needs anchor-vs-non-anchor split
- `paste_hidden()` in `paste_hidden.py`: link class lookup must read from anchor knob, not call `get_link_class_for_source(anchor_node)` directly
- `create_anchor_named()` in `anchor.py`: stream detection and link-class knob storage added here

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-copy-paste-semantics*
*Context gathered: 2026-03-04*
