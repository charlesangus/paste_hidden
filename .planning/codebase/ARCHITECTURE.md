# Architecture

**Analysis Date:** 2026-03-03

## Pattern Overview

**Overall:** Replacement clipboard system with an auxiliary anchor-and-link reference system for Nuke node graphs.

**Key Characteristics:**
- Overrides Nuke's built-in copy/cut/paste system to handle hidden inputs intelligently
- Stateless anchor-and-link system persisted as plain Nuke node properties (NoOp/Dot nodes with metadata knobs)
- Separation of concerns: clipboard operations (`paste_hidden.py`), anchors (`anchor.py`), links and shared utilities (`link.py`)
- UI driven by tabtabtab fuzzy-search plugin system for anchor/link creation and navigation
- Configuration isolated in `constants.py` with no dependencies on implementation modules

## Layers

**UI Layer:**
- Purpose: Menu integration and user-facing commands
- Location: `menu.py` (Nuke menu registration), `tabtabtab.py` (search widget framework)
- Contains: Command registration, keyboard shortcut bindings, fuzzy-search UI widget code
- Depends on: Core modules (anchor, labels, paste_hidden), Nuke API, PySide2/PySide6
- Used by: Nuke main menu system; invoked by user keyboard shortcuts and menu clicks

**Anchor System Layer:**
- Purpose: Creation, renaming, storage, and discovery of named input reference nodes
- Location: `anchor.py`
- Contains: Anchor creation/renaming logic, anchor color resolution (backdrop/input node color priority), FQNN lookup, link retrieval, AnchorPlugin/AnchorNavigatePlugin for tabtabtab integration
- Depends on: `link.py` (predicates and FQNN utilities), `constants.py`, `labels.py`, `tabtabtab.py` (plugin base class)
- Used by: Menu commands, keyboard shortcuts, tabtabtab picker widgets

**Copy/Paste Layer:**
- Purpose: Override Nuke's clipboard to handle hidden input re-piping and proxy node replacement
- Location: `paste_hidden.py`
- Contains: copy_hidden(), cut_hidden(), paste_hidden(), paste_multiple_hidden(), and fallback old-style copy/cut/paste functions
- Depends on: `link.py` (node classification and setup), `constants.py`, Nuke API
- Used by: Menu shortcuts (Ctrl+C, Ctrl+X, Ctrl+V) and Paste Multiple command

**Link/Utilities Layer:**
- Purpose: Shared predicates, FQNN tracking, link node setup, and cross-script reference detection
- Location: `link.py`, `util.py`
- Contains: is_anchor/is_link predicates, FQNN generation, link node wiring, anchor finding by FQNN, color resolution fallback, backdrop containment search, link class mapping
- Depends on: `constants.py`, Nuke API
- Used by: All other modules (anchor, paste_hidden, labels)

**Label Utilities Layer:**
- Purpose: Helper functions for Dot and Node label management with font sizing and propagation
- Location: `labels.py`
- Contains: Label application with optional font sizing, Dot-to-link label propagation, user input dialogs
- Depends on: `link.py` (FQNN, link detection, reconnection), `constants.py`, Nuke API
- Used by: Anchor system (Dot anchor creation), menu commands (Label shortcuts)

**Configuration Layer:**
- Purpose: Centralized constants and lookup tables
- Location: `constants.py`
- Contains: Knob names (KNOB_NAME, TAB_NAME, etc.), node class mappings (LINK_CLASSES, HIDDEN_INPUT_CLASSES), prefix strings (ANCHOR_PREFIX), font sizes, default colors
- Depends on: Nothing (pure data)
- Used by: All other modules for configuration consistency

## Data Flow

**Copy Operation:**
1. User selects node(s) and presses Ctrl+C
2. `copy_hidden()` iterates selected nodes
3. For each node: checks if anchor/link/hidden-input-class node; calls `get_fully_qualified_node_name()` to store origin
4. Adds hidden knob (KNOB_NAME) with FQNN string to node
5. For hidden-input nodes: calls `setup_link_node()` to configure as proxy
6. Calls `nuke.nodeCopy()` to perform standard Nuke copy
7. Node data + hidden knobs saved to Nuke's clipboard file

**Paste Operation:**
1. User presses Ctrl+V
2. `paste_hidden()` calls `nuke.nodePaste()` to instantiate nodes
3. Iterates pasted nodes checking for KNOB_NAME (stored FQNN)
4. For each: calls `find_anchor_node()` to locate original via FQNN
5. If FQNN is same script/group level: calls `setup_link_node()` to reconnect
6. If anchor/link type: replaces with appropriate link node class, re-positions
7. Updates selection to new nodes
8. Returns last pasted node (matching Nuke API contract)

**Anchor Creation:**
1. User presses A with node selected OR with nothing selected (picker mode)
2. `create_anchor()` or `select_anchor_and_create()` called
3. Prompts for name, suggests from input node's file path + backdrop label
4. Calls `create_anchor_named()`: creates NoOp with ANCHOR_PREFIX + sanitized name
5. Positions below input node
6. Sets tile color via `find_anchor_color()` (backdrop → input node → default purple)
7. Adds reconnect and rename knobs

**Link Creation:**
1. User presses A with nothing selected OR uses Create Link menu command
2. `select_anchor_and_create()` or `create_link_for_anchor_named()` called
3. TabTabTab picker lists all anchors (from `all_anchors()`)
4. User fuzzy-searches and selects anchor
5. `create_from_anchor()` creates link node (class determined by source node)
6. `setup_link_node()` wires link to anchor, stores FQNN in KNOB_NAME, sets label/color

**Anchor Rename:**
1. User presses A with anchor selected OR clicks Rename on anchor properties
2. `rename_anchor()` prompts for new name
3. For Dot: updates label, finds all link nodes via FQNN match, updates their labels
4. For NoOp: updates ANCHOR_PREFIX + name, updates all referencing link FQNN values
5. All link labels updated to reflect new anchor name

**Link Reconnection:**
1. User clicks "Reconnect" button on link OR calls `reconnect_all_links()`
2. `reconnect_link_node()` calls `find_anchor_node()` to locate anchor via stored FQNN
3. Cross-script/cross-group references return None (safe no-op)
4. `link_node.setInput(0, anchor_node)` re-wires connection

**State Management:**
- **Anchor nodes:** NoOp (name prefixed ANCHOR_PREFIX) or Dot (with hidden DOT_ANCHOR_KNOB_NAME marker knob)
- **Link nodes:** PostageStamp/NoOp/Dot with hidden KNOB_NAME knob storing FQNN of referenced anchor
- **Copy state:** Hidden KNOB_NAME knob temporarily added during copy, remains on pasted node
- **Persistence:** All state stored as node properties/knobs; survives save/load without callbacks
- **Cross-script:** FQNN includes script name; same-script check in `find_anchor_node()` prevents invalid cross-script references

## Key Abstractions

**Fully Qualified Node Name (FQNN):**
- Purpose: Unique, cross-script-aware identifier for a node
- Format: `<script_stem>.<node.fullName()>` (e.g., `main.Group1.myNode`)
- Examples: `anchor.py:18`, `link.py:149-162`
- Pattern: Generated once during copy, stored on node knob, used to find anchor during paste/reconnect
- Cross-script detection: Script stem prefix allows `find_anchor_node()` to reject invalid references

**Node Classification:**
- Purpose: Determine how a node is handled during copy/paste
- Predicate `is_anchor(node)`: True if node name starts ANCHOR_PREFIX, or is Dot with anchor marker knob, or legacy labelled Dot
- Predicate `is_link(node)`: True if KNOB_NAME present in knobs
- Predicate classifications: LINK_CLASSES (which input types get replaced), HIDDEN_INPUT_CLASSES (which nodes can have hidden inputs)
- Files: `link.py:77-95`

**Link Node Setup:**
- Purpose: Configure a node as a link to an anchor
- Steps: Hide input, inherit anchor color, set label prefix "Link: ", store anchor FQNN in knob
- Files: `link.py:131-145`
- Re-used by: paste_hidden, anchor system

**Color Resolution:**
- Purpose: Determine anchor tile color with fallback priority
- Priority: 1) Smallest containing BackdropNode (Read nodes only), 2) Input node color, 3) Default purple
- Files: `anchor.py:44-68`, `link.py:33-37`
- Used by: Anchor creation, link node setup, tabtabtab color hints

**Tabtabtab Plugin System:**
- Purpose: Reusable fuzzy-search menu picker
- Pattern: Implement `TabTabTabPlugin` with `get_items()`, `get_weights_file()`, `invoke()`, optional `get_icon()` and `get_color()`
- Implementations: `AnchorPlugin` (anchor link creation), `AnchorNavigatePlugin` (anchor DAG navigation)
- Files: `anchor.py:296-326`, `anchor.py:400-429`, `tabtabtab.py:20-53`
- Persistence: User selection frequency stored in weights file, affects search result ranking

## Entry Points

**Nuke Menu Integration:**
- Location: `menu.py`
- Triggers: Plugin load (via `nuke.pluginAddPath()` in init.py)
- Responsibilities: Replace Ctrl+C/Ctrl+X/Ctrl+V with hidden-aware versions, add Edit > Anchors submenu with all anchor/label/search commands

**Copy/Paste Commands:**
- `copy_hidden()`: Ctrl+C override
- `cut_hidden()`: Ctrl+X override
- `paste_hidden()`: Ctrl+V override
- `paste_multiple_hidden()`: Edit > Paste Multiple
- Triggered by: Keyboard shortcuts, menu clicks
- Dependencies: Nuke clipboard file via nukescripts.cut_paste_file()

**Anchor Creation:**
- `anchor_shortcut()` (keyboard A): Context-aware entry point (create new, rename existing, or open picker)
- `create_anchor()`: Prompted creation
- `select_anchor_and_create()`: Fuzzy-search picker
- Triggered by: Keyboard shortcut A, menu commands
- Dependencies: User input dialogs, tabtabtab picker

**Anchor Navigation:**
- `select_anchor_and_navigate()`: Fuzzy-search picker to jump DAG view to anchor
- Triggered by: Keyboard shortcut Alt+A, menu command "Anchor Find"
- Dependencies: tabtabtab picker, `navigate_to_anchor()` zoom-to-fit

**Label Utilities:**
- `create_large_label()`, `create_medium_label()`, `append_to_label()`
- Triggered by: Keyboard shortcuts (Shift+M, Shift+N, Ctrl+M), menu commands
- Responsibilities: Prompt for label, apply with optional font sizing, propagate to link nodes if Dot

## Error Handling

**Strategy:** Silent fail-safe with exception guards; operations continue after errors.

**Patterns:**
- Anchor node existence checks: `nuke.exists(node.name())` before operations in tabtabtab invoke
- FQNN lookup guards: `find_anchor_node()` returns None if cross-script/cross-group detected
- Link reconnection: Safe no-op if anchor not found (returns None, link stays unconnected)
- User input cancellation: Check for None return from `nuke.getInput()`
- Name sanitization: `sanitize_anchor_name()` validates non-empty string, raises ValueError if empty
- Tabtabtab error guards: Try-except around widget existence checks, catches RuntimeError if widget deleted
- File I/O: tabtabtab weights file loading wrapped in exception handler, prints traceback but continues

**No-op patterns:**
- `paste_hidden()` skips nodes without KNOB_NAME (user copy, not our copy)
- `reconnect_link_node()` skips if FQNN points to different script/group (safe cross-script)
- Anchor predicates catch and return False on exception (missing knobs, etc.)

## Cross-Cutting Concerns

**Logging:** Print statements in tabtabtab for weight file load/save errors; no structured logging.

**Validation:**
- FQNN cross-script check: `prefix_from_knob != prefix_from_current` in `find_anchor_node()`
- Name sanitization: Anchor names stripped of non-alphanumeric-underscore characters
- Input node classification: Only LINK_CLASSES and HIDDEN_INPUT_CLASSES nodes are proxy-eligible

**Authentication:** None (local-only Nuke plugin, no external auth).

**Backward Compatibility:** Legacy labelled Dot detection in `is_anchor()` (Dot with label not marked with knob still counts as anchor if no "Link: " prefix).

---

*Architecture analysis: 2026-03-03*
