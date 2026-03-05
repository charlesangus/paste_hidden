# Phase 5: Refactor cross-script paste logic for hidden-input Dot vs Anchor Dot distinction - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix two UAT-confirmed bugs from Phase 2:
1. Link nodes (PostageStamp/NoOp links) pasted cross-script do not reconnect to a same-named anchor in the destination script (XSCRIPT-01 gap)
2. Non-anchor hidden-input Dots can erroneously reconnect cross-script when source and destination scripts share the same filename stem (XSCRIPT-02 gap)

The fix requires a formal distinction between two Dot subtypes and visual differentiation between them. No new capabilities are added — this is a correctness refactor of existing paste semantics.

</domain>

<decisions>
## Implementation Decisions

### Dot subtype terminology and distinction
Two Dot subtypes must be formally distinguished:
- **Link Dot** — a Dot whose `input(0)` is an anchor node. Cross-script capable. Should reconnect to same-named anchor on cross-script paste.
- **Local Dot** — a Dot whose `input(0)` is a non-anchor node (e.g. Blur1). Script-local only. Must NOT reconnect cross-script.

Add an explicit DOT_TYPE knob (string) to distinguish them at paste time. Set to `'link'` for Link Dots and `'local'` for Local Dots in `copy_hidden()` Path B. Do NOT rely solely on FQNN suffix inspection — use the explicit knob.

### Cross-script Link node reconnect (Bug 1 fix)
When a Link node (NoOp or PostageStamp with KNOB_NAME set) is pasted cross-script and a same-named anchor exists in the destination script:
- **Rewire the existing pasted node** to the destination anchor (do not create a fresh node). Since we use NoOps for all links now, the type mismatch concern is moot.
- Use `_extract_display_name_from_fqnn()` to get the display name, then `find_anchor_by_name()` to locate the destination anchor.
- If no matching anchor exists → leave the pasted node disconnected silently. No error, no dialog.

This logic lives in `paste_hidden()` Path B. Currently Path B does `continue` for cross-script; it needs a check: if FQNN points to an anchor (or DOT_TYPE == 'link'), attempt name-based reconnect.

### Local Dot cross-script behaviour (Bug 2 fix)
When a Local Dot is pasted cross-script:
- Do NOT attempt reconnection under any circumstances.
- Retain the "Local: ..." label and Local Dot orange color on the pasted node — it remains visually identifiable as a disconnected Local Dot from another script.
- Same-stem false positives (two scripts named "untitled") are an acceptable edge case and do not require engineering effort.

### Local Dot same-script behaviour (preserve PASTE-03)
When a Local Dot is pasted within the same script:
- Reconnect to the original source node by identity (via FQNN/KNOB_NAME). This is PASTE-03 and currently works — do not break it.

### Visual differentiation: Local Dot vs Link Dot
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

</decisions>

<specifics>
## Specific Ideas

- The user noted: "You have attempted this work twice before, and botched it both times. Be careful, work methodically, think things out step by step, and make extra sure you're not breaking existing functionality." — The researcher and planner must trace every code path carefully, test every existing path before changing it, and verify PASTE-03 (same-script Local Dot reconnect) is not broken.
- Orange for Local Dots must not evoke "warning" or alarm — it's a neutral visual marker, not an error state.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_extract_display_name_from_fqnn()` in `paste_hidden.py` — already implements FQNN suffix check (strips ANCHOR_PREFIX from last segment). Can be used as part of the backward-compat fallback for nodes lacking the new DOT_TYPE knob.
- `find_anchor_by_name()` in `anchor.py` — already used in Path A/C for cross-script name-based reconnect. Reuse in Path B for Link Dot reconnect.
- `ANCHOR_DEFAULT_COLOR = 0x6f3399ff` in `constants.py` — confirmed as the Link Dot tile color.
- `setup_link_node()` in `link.py` — currently called for both Link Dots and Local Dots in `copy_hidden()` Path B. The logic that sets label and color needs to branch based on Dot type.
- `DOT_ANCHOR_KNOB_NAME = 'paste_hidden_dot_anchor'` in `constants.py` — precedent for knob naming convention. New DOT_TYPE knob should follow this pattern.

### Established Patterns
- `copy_hidden()` Path B in `paste_hidden.py`: branches on `is_anchor(input_node)` to distinguish anchor-backed Dots from non-anchor Dots. The DOT_TYPE knob must be set in both branches of this `if/else`.
- `paste_hidden()` Path B: currently handles HIDDEN_INPUT_CLASSES nodes. The cross-script reconnect must be inserted before the existing `if not input_node: continue`.
- `add_input_knob()` in `link.py`: always called before setting KNOB_NAME. The DOT_TYPE knob should be added in the same flow (or set alongside KNOB_NAME).

### Integration Points
- `paste_hidden.py` → `copy_hidden()` Path B: add DOT_TYPE knob + branch label/color logic
- `paste_hidden.py` → `paste_hidden()` Path B: add cross-script reconnect check for Link Dots; preserve same-script reconnect for Local Dots
- `constants.py`: add DOT_TYPE_KNOB_NAME constant and the Local Dot orange color constant
- `link.py` → `setup_link_node()`: may need a `dot_type` parameter or caller-side override so label prefix and color can vary

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-refactor-cross-script-paste-logic-for-hidden-input-dot-vs-anchor-dot-distinction*
*Context gathered: 2026-03-05*
