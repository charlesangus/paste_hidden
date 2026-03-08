# Phase 4: Anchor Navigation - Research

**Researched:** 2026-03-08
**Domain:** Nuke Python API — DAG viewport control, tabtabtab picker extension
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Navigation history depth:** Single-step back only — one saved position slot, no history stack. Each Alt+A jump (to anchor or Backdrop) overwrites the saved slot before navigating. The slot is cleared/consumed when Alt+Z is used (no "forward" re-visit). Every Alt+A saves regardless of whether the user just came back (no ping-pong detection needed). NAV-03 (full browser-style history) deferred to a future phase.
- **Back shortcut:** Keyboard shortcut is Alt+Z. Registered in the Anchors menu (same place as Alt+A Anchor Find). Silent no-op if no position has been saved yet (no error, no message).
- **What "DAG position" means:** Save `nuke.zoom()` (zoom level) + `nuke.center()` (x, y center point). Session-only — in-memory module-level variable in `anchor.py`; not persisted to disk. On Alt+Z restore: set zoom + center back to saved values, then call `nukescripts.clear_selection_recursive()` (matches existing behavior in `navigate_to_anchor()`). Selection state at the time of the original jump is NOT saved (viewport only).
- **Backdrop inclusion in picker:** Only BackdropNodes with a non-empty `label` knob appear in the picker. Anchors appear bare (no prefix): `MyAnchor`, `PlateA`. Backdrops appear prefixed: `Backdrops/GradeStack`, `Backdrops/Comp`. Navigating to a Backdrop = `nuke.zoomToFitSelected()` on the BackdropNode (zoom to fit entire backdrop). Backdrop navigation also saves the previous DAG position (identical to anchor navigation — any Alt+A jump saves position).

### Claude's Discretion

- How `nuke.center()` / `nuke.zoom()` are called to restore position (API details).
- Whether to introduce a `navigate_to_backdrop()` helper or extend `navigate_to_anchor()`.
- Test strategy for the in-memory back-position slot.

### Deferred Ideas (OUT OF SCOPE)

- NAV-03: Full browser-style forward/back history stack — future phase (NAV-V2-01 in REQUIREMENTS.md).

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NAV-01 | DAG position is saved when navigate-to-anchor (Alt+A) is invoked | `nuke.zoom()` (no args) returns current zoom float; `nuke.center()` returns [x, y] list. Save both before navigation call. Module-level slot variable in `anchor.py`. |
| NAV-02 | A keyboard shortcut (Alt+Z) jumps the DAG view back to the saved position | `nuke.zoom(saved_zoom, saved_center)` restores viewport. Register in `menu.py` same as Alt+A. Silent no-op guard: check slot is not None before restoring. |
| NAV-03 | Full browser-style forward/back history stack | DEFERRED — not in scope for this phase. |
| FIND-01 | Anchor navigation picker (Alt+A) includes labelled BackdropNodes as navigable targets alongside anchor nodes | `nuke.allNodes('BackdropNode')` lists all backdrops. Filter to non-empty `label` knob. Add to `AnchorNavigatePlugin.get_items()` with `menupath: 'Backdrops/' + label`. Navigate via `zoomToFitSelected()` on the BackdropNode. |

</phase_requirements>

## Summary

Phase 4 is well-scoped and low-risk. All implementation builds on patterns already established in `anchor.py` and `menu.py`. The Nuke API for DAG viewport save/restore is well-documented and simple: `nuke.zoom()` returns the current zoom level as a float; `nuke.center()` returns [x, y] as a list; `nuke.zoom(level, [x, y])` restores both in one call. The round-trip pattern `center = nuke.center(); zoom = nuke.zoom()` → `nuke.zoom(zoom, center)` is the canonical approach confirmed by Foundry's official documentation.

The two capabilities (navigation history and Backdrop inclusion) are independent of each other but both touch `AnchorNavigatePlugin` and `navigate_to_anchor()`. The natural plan split is: (1) the position-save/restore system with Alt+Z, then (2) the Backdrop entries in the picker. Both can be validated offline with the existing stub-based unittest infrastructure — no live Nuke session needed for logic tests.

The only area requiring discretion is whether to introduce a `navigate_to_backdrop()` helper function or handle Backdrop navigation inline inside the plugin's `invoke()` method. Given the existing pattern of `navigate_to_anchor()` as a named helper, introducing `navigate_to_backdrop()` is the cleaner approach (testable in isolation, consistent with codebase style).

**Primary recommendation:** Implement in two sequential tasks — (1) position slot + Alt+Z restore, (2) Backdrop picker entries + `navigate_to_backdrop()`.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `nuke` (built-in) | 13.x–16.x | DAG viewport control (`zoom`, `center`, `zoomToFitSelected`), node enumeration (`allNodes`) | Foundry's own Python API — only option |
| `nukescripts` (built-in) | same | `clear_selection_recursive()` — already used in `navigate_to_anchor()` | Established pattern in this codebase |
| `tabtabtab` (bundled) | project | Plugin mechanism for Alt+A picker items (`get_items()`, `invoke()`) | Already used by `AnchorNavigatePlugin` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unittest` + stubs | stdlib | Offline tests without live Nuke | All logic tests — stubs already established |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Module-level slot variable | Persistent file / Nuke preferences | File I/O is unnecessary overhead; session-only is the decided constraint |
| `navigate_to_backdrop()` helper | Inline logic in `invoke()` | Helper is more testable and consistent with existing `navigate_to_anchor()` pattern |

## Architecture Patterns

### Existing Pattern: Module-Level Widget Globals

Already used in `anchor.py`:
```python
_anchor_picker_widget = None   # line 492
_anchor_navigate_widget = None # line 563
```

The back-position slot follows this exact pattern:
```python
_back_position = None  # None = no position saved; tuple = (zoom_level, center_xy)
```

### Pattern 1: Save-Before-Navigate

**What:** Before any navigation call in `navigate_to_anchor()` (and the new `navigate_to_backdrop()`), capture current viewport state into the module-level slot.

**When to use:** Every time `invoke()` calls a navigate function — guarantees the slot always reflects the position before the most recent jump.

**Example:**
```python
# In anchor.py
_back_position = None  # module-level

def _save_dag_position():
    """Capture current DAG viewport state into the back-position slot."""
    global _back_position
    zoom_level = nuke.zoom()
    center_xy = nuke.center()
    _back_position = (zoom_level, center_xy)

def navigate_back():
    """Restore the saved DAG position. Silent no-op if none saved."""
    global _back_position
    if _back_position is None:
        return
    zoom_level, center_xy = _back_position
    _back_position = None  # consume the slot
    nuke.zoom(zoom_level, center_xy)
    nukescripts.clear_selection_recursive()
```

### Pattern 2: Backdrop Items in AnchorNavigatePlugin.get_items()

**What:** Extend `get_items()` to yield both anchor items and labelled Backdrop items.

**When to use:** Any picker that should list both anchors and Backdrops.

**Example:**
```python
def get_items(self):
    items = []
    for anchor_node in all_anchors():
        items.append({
            'menuobj': anchor_node,
            'menupath': 'Anchors/' + anchor_display_name(anchor_node),
        })
    for backdrop_node in nuke.allNodes('BackdropNode'):
        label = backdrop_node['label'].value().strip()
        if label:
            items.append({
                'menuobj': backdrop_node,
                'menupath': 'Backdrops/' + label,
            })
    return items
```

### Pattern 3: navigate_to_backdrop()

**What:** Named helper that selects the BackdropNode and calls `nuke.zoomToFitSelected()`, mirroring `navigate_to_anchor()`.

**Example:**
```python
def navigate_to_backdrop(backdrop_node):
    """Zoom the DAG to fit the entire BackdropNode."""
    nukescripts.clear_selection_recursive()
    backdrop_node["selected"].setValue(True)
    nuke.zoomToFitSelected()
    nukescripts.clear_selection_recursive()
```

### Pattern 4: Unified invoke() Dispatch

**What:** `AnchorNavigatePlugin.invoke()` saves position first, then dispatches to the correct navigate function based on node class.

**Example:**
```python
def invoke(self, thing):
    node = thing['menuobj']
    if not nuke.exists(node.name()):
        return
    _save_dag_position()  # always save before navigating
    if node.Class() == 'BackdropNode':
        navigate_to_backdrop(node)
    else:
        navigate_to_anchor(node)
```

### Anti-Patterns to Avoid

- **Saving position inside navigate_to_anchor() itself:** This would break the separation of concerns — navigation functions should navigate, not manage history. The save belongs in `invoke()` (or `select_anchor_and_navigate()` entry point if invoked without the picker).
- **Storing position as separate zoom and center variables:** Use a single slot `_back_position = (zoom, center)` or `None`. This makes the "no position saved" guard trivial.
- **Filtering backdrops by something other than non-empty label:** The user explicitly decided "only labelled BackdropNodes". Don't add additional filters (e.g., size, color).
- **Using a prefix-only display name for backdrops in get_color():** BackdropNodes in the picker will be passed to `get_color()` — ensure the method handles both anchor nodes and Backdrop nodes. Backdrops have `tile_color` so the same approach works.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DAG viewport state capture | Custom coordinate tracking | `nuke.zoom()` + `nuke.center()` | Foundry API handles viewport coordinate system precisely |
| DAG viewport restore | Manual pan calculation | `nuke.zoom(level, [x, y])` | Single call restores both zoom and center atomically |
| Backdrop enumeration | Custom regex on node names | `nuke.allNodes('BackdropNode')` | Already used in `find_smallest_containing_backdrop()` in `link.py` |
| Zoom-to-fit Backdrop | Manual coordinate calculation | `nuke.zoomToFitSelected()` | Already used in `navigate_to_anchor()` — exact same mechanism |

**Key insight:** The Nuke API already provides exactly what's needed. The entire navigation history feature reduces to ~10 lines of new Python.

## Common Pitfalls

### Pitfall 1: nuke.zoom() Returns None in Headless Context

**What goes wrong:** In a non-GUI environment (e.g., running tests without Nuke), `nuke.zoom()` returns `None`. Storing `(None, None)` and then calling `nuke.zoom(None, None)` later would fail.

**Why it happens:** The Nuke API is GUI-dependent; viewport functions are no-ops or return None in batch/headless mode.

**How to avoid:** The stub for offline tests must explicitly provide `nuke.zoom` and `nuke.center` as mockable callables. Tests verify logic (save/restore slot behavior) using return value mocking, not actual viewport state.

**Warning signs:** `_back_position = (None, None)` — the guard `if _back_position is None` would pass but the restore would fail. Use `if _back_position is None` (tuple vs None check) not a truthiness check — an empty or zero-valued tuple could be falsy.

### Pitfall 2: Backdrop label knob returns raw markup

**What goes wrong:** `backdrop_node['label'].value()` may include Nuke's TCL-style formatting or HTML tags if the user set a styled label.

**Why it happens:** Nuke's label knob supports markup. `value()` vs `getValue()` may behave differently.

**How to avoid:** Use `.strip()` on the returned string; for the filter condition, just check that the stripped string is non-empty. The display name in the picker can use the raw `.strip()` result — no need to strip markup for the picker label (Nuke renders it anyway).

**Warning signs:** Empty strings or strings with only whitespace passing through as valid backdrop labels.

### Pitfall 3: get_color() Called with BackdropNode menuobj

**What goes wrong:** `AnchorNavigatePlugin.get_color()` currently assumes `menuobj` is an anchor node (accesses `tile_color`). BackdropNodes also have `tile_color`, so the existing code works — but the method should be verified to handle both.

**Why it happens:** The original implementation was anchor-only. After FIND-01, it handles two node types.

**How to avoid:** BackdropNodes have `tile_color` accessible via `node['tile_color'].value()` — the same knob access pattern. No change needed if the method uses this generic knob access. Verify in tests.

### Pitfall 4: Missing items when no Backdrops exist

**What goes wrong:** If the script has no BackdropNodes, `nuke.allNodes('BackdropNode')` returns `[]`. The guard in `select_anchor_and_navigate()` currently checks `if not all_anchors(): return`. After FIND-01, the picker should also launch if only labelled Backdrops exist (no anchors).

**Why it happens:** The current guard `if not all_anchors(): return` would prevent the picker from showing when there are Backdrops but no anchors.

**How to avoid:** Change the launch guard from `if not all_anchors(): return` to check `if not get_items_for_navigate_picker(): return` (or equivalent) — or simply check whether there are any anchors OR labelled Backdrops before suppressing the picker.

## Code Examples

Verified patterns from official Foundry documentation:

### Save/Restore DAG Viewport Position

```python
# Source: Foundry official docs - https://learn.foundry.com/nuke/developers/140/pythonreference/dag.html
# Get current state
zoom_level = nuke.zoom()          # returns float (current zoom factor)
center_xy = nuke.center()         # returns [x, y] list

# Restore state
nuke.zoom(zoom_level, center_xy)  # sets zoom and centers on the saved point
```

### Zoom to Fit a Node

```python
# Source: existing navigate_to_anchor() in anchor.py
nukescripts.clear_selection_recursive()
node["selected"].setValue(True)
nuke.zoomToFitSelected()
nukescripts.clear_selection_recursive()
```

### List All Labelled BackdropNodes

```python
# Source: adapted from find_smallest_containing_backdrop() in link.py
labelled_backdrops = [
    bd for bd in nuke.allNodes('BackdropNode')
    if bd['label'].value().strip()
]
```

### Nuke API — nuke.zoom() Signatures

```python
nuke.zoom()                        # → float: returns current zoom level
nuke.zoom(scale)                   # sets zoom, cursor position maintained
nuke.zoom(scale, [center_x, center_y])  # sets zoom + pans to center
```

### Nuke API — nuke.center() Signature

```python
nuke.center()  # → [x, y]: returns current DAG center as a 2-element list
               # result is suitable to pass directly to nuke.zoom() as center arg
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No navigation history | Single-slot back position (session-only) | Phase 4 (this phase) | Artists can jump back after Alt+A navigation |
| Anchors-only in picker | Anchors + labelled Backdrops in picker | Phase 4 (this phase) | Broader DAG navigation from a single shortcut |

**Deprecated/outdated:** None — Phase 4 extends the existing system without replacing anything.

## Open Questions

1. **nuke.zoom() return value in tests**
   - What we know: In GUI context it returns a float. In headless tests it likely returns None (from stub or real API).
   - What's unclear: Whether the existing nuke stubs already include `zoom` and `center` or need to be extended.
   - Recommendation: Wave 0 for the new test file must add `stub.zoom = MagicMock(return_value=1.0)` and `stub.center = MagicMock(return_value=[0.0, 0.0])` to the nuke stub. Inspect `test_anchor_color_system.py`'s `make_stub_nuke_module()` — those additions go there (or in the new test file's own stub).

2. **Backdrop label markup stripping**
   - What we know: `bd['label'].value().strip()` gives usable strings for the filter.
   - What's unclear: Whether Nuke sometimes stores markup that `.strip()` doesn't remove, making the filter unreliable.
   - Recommendation: For this phase, `.strip()` is sufficient. If edge cases arise in QA, add a simple tag-stripping regex.

3. **`all_items_for_navigate_picker()` vs inline guard change**
   - What we know: Current guard `if not all_anchors(): return` in `select_anchor_and_navigate()` will suppress the picker when only Backdrops exist.
   - What's unclear: Whether the artist workflow ever has Backdrops without anchors (probably yes during early script setup).
   - Recommendation: Fix the guard to: `if not (all_anchors() or any(bd['label'].value().strip() for bd in nuke.allNodes('BackdropNode'))): return`.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `unittest` (stdlib — no install required) |
| Config file | None — discovered via `python3 -m unittest discover -s tests -p "*.py"` |
| Quick run command | `python3 -m unittest discover -s tests -p "*.py"` |
| Full suite command | `python3 -m unittest discover -s tests -p "*.py"` |

Note: `pytest` is not installed in this environment. The project uses `python3 -m unittest` throughout (58 tests currently passing).

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NAV-01 | Calling `_save_dag_position()` (or equivalent) captures `nuke.zoom()` + `nuke.center()` into module slot | unit | `python3 -m unittest tests.test_anchor_navigation` | No — Wave 0 |
| NAV-01 | `AnchorNavigatePlugin.invoke()` calls save before navigating | unit | `python3 -m unittest tests.test_anchor_navigation` | No — Wave 0 |
| NAV-02 | `navigate_back()` calls `nuke.zoom(saved_zoom, saved_center)` when slot is populated | unit | `python3 -m unittest tests.test_anchor_navigation` | No — Wave 0 |
| NAV-02 | `navigate_back()` is a silent no-op when `_back_position is None` | unit | `python3 -m unittest tests.test_anchor_navigation` | No — Wave 0 |
| NAV-02 | `navigate_back()` clears the slot after restoring | unit | `python3 -m unittest tests.test_anchor_navigation` | No — Wave 0 |
| NAV-02 | Alt+Z menu command calls `anchor.navigate_back()` | manual/smoke | N/A (requires live Nuke) | N/A |
| FIND-01 | `AnchorNavigatePlugin.get_items()` includes labelled BackdropNodes with `Backdrops/` prefix | unit | `python3 -m unittest tests.test_anchor_navigation` | No — Wave 0 |
| FIND-01 | `AnchorNavigatePlugin.get_items()` excludes unlabelled (empty label) BackdropNodes | unit | `python3 -m unittest tests.test_anchor_navigation` | No — Wave 0 |
| FIND-01 | Navigating to Backdrop calls `zoomToFitSelected()` on the BackdropNode | unit | `python3 -m unittest tests.test_anchor_navigation` | No — Wave 0 |
| FIND-01 | Picker launches when only labelled Backdrops exist (no anchors) | unit | `python3 -m unittest tests.test_anchor_navigation` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m unittest discover -s tests -p "*.py"`
- **Per wave merge:** `python3 -m unittest discover -s tests -p "*.py"`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_anchor_navigation.py` — covers NAV-01, NAV-02, FIND-01 (all logic tests for this phase)
  - Must extend nuke stub with: `stub.zoom = MagicMock(return_value=1.0)`, `stub.center = MagicMock(return_value=[0.0, 0.0])`
  - Reuse `make_stub_nuke_module()` pattern from `test_anchor_color_system.py`
  - Stub pattern for Qt + tabtabtab already established — copy from existing test files

## Sources

### Primary (HIGH confidence)
- Foundry official docs — `nuke.zoom()` signature, parameters, return value: https://learn.foundry.com/nuke/developers/130/pythondevguide/_autosummary/nuke.zoom.html
- Foundry official docs — `nuke.center()` signature and return format: https://learn.foundry.com/nuke/developers/16.0/pythondevguide/_autosummary/nuke.center.html
- Foundry official docs — DAG manipulation overview: https://learn.foundry.com/nuke/developers/140/pythonreference/dag.html
- `/workspace/anchor.py` — existing `navigate_to_anchor()`, `AnchorNavigatePlugin`, module-level globals pattern
- `/workspace/link.py` — existing `find_smallest_containing_backdrop()` and `nuke.allNodes('BackdropNode')` pattern
- `/workspace/menu.py` — existing menu registration pattern (`anchors_menu.addCommand(name, cmd, shortcut)`)
- `/workspace/tests/test_anchor_color_system.py` — existing offline stub infrastructure, `make_stub_nuke_module()`

### Secondary (MEDIUM confidence)
- Web search results confirming save/restore round-trip pattern: `center = nuke.center(); zoom = nuke.zoom()` → `nuke.zoom(zoom, center)` — confirmed by multiple Foundry doc pages

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Nuke built-in API confirmed via official Foundry documentation
- Architecture: HIGH — All patterns derived from existing codebase code or confirmed API signatures
- Pitfalls: MEDIUM — Headless/None return value pitfall is speculative but grounded in Nuke API behavior; markup pitfall is LOW risk given `.strip()` sufficiency

**Research date:** 2026-03-08
**Valid until:** 2026-06-08 (stable API, 90-day window reasonable)
