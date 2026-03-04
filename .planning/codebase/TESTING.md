# Testing Patterns

**Analysis Date:** 2026-03-03

## Test Framework

**Runner:**
- Not detected - No test framework configured

**Assertion Library:**
- Not applicable - No testing infrastructure

**Run Commands:**
```bash
# No test runner configured
# Manual testing in Nuke application required
```

## Test File Organization

**Location:**
- No test files found in codebase
- Search performed: `find . -name "*test*.py" -o -name "*_test.py" -o -name "test_*.py" -o -name "conftest.py"`
- Result: No matches

**Naming:**
- Not applicable

**Structure:**
- Not applicable

## Testing Strategy

**Approach:** Manual testing in Nuke

This codebase is a Nuke plugin that runs within the Nuke application context. Testing patterns observed:

**Manual verification points:**
- Copy/cut/paste operations with anchor nodes (`paste_hidden.py`)
- Anchor creation and naming (`anchor.py`)
- Link node reconnection (`link.py`)
- Menu registration (`menu.py`)
- Label application (`labels.py`)

**Untestable without Nuke runtime:**
- All Nuke API interactions (`nuke.selectedNodes()`, `nuke.createNode()`, `nuke.allNodes()`)
- Qt framework interactions (PySide2/PySide6 UI widgets)
- File system access in Nuke context

## Mocking

**Framework:**
- Not applicable - no testing framework

**Patterns:**
- Not applicable - all code is tightly coupled to Nuke/Qt APIs

## Testability Constraints

**Hard dependencies preventing isolation:**
1. **Nuke SDK:** All modules import `nuke` and use:
   - `nuke.selectedNodes()` - query application state
   - `nuke.createNode()` - mutate DAG (directed acyclic graph)
   - `nuke.allNodes()` - scan entire scene
   - `nuke.toNode()` - resolve node references
   - `node.knobs()` - access internal node properties

2. **Qt Framework:** Used for UI in multiple modules:
   - `anchor.py:9-19` - Version detection and import fallback (PySide2 vs PySide6)
   - `tabtabtab.py:12-17` - Qt widget system
   - Widget state management (`_anchor_picker_widget` global state)

3. **Environment-dependent behavior:**
   - `get_fully_qualified_node_name()` uses `nuke.root().name()` - file path dependent
   - `find_smallest_containing_backdrop()` scans all nodes - state dependent
   - Widget cleanup tries/excepts RuntimeError - fragile to Qt state

**Strategies to enable testing:**
- Dependency injection: Pass Nuke API client to functions (not currently done)
- Stubbing: Create mock `nuke` module with basic stubs
- Integration testing: Automated Nuke scripts (requires Nuke license/install)

## Test Coverage Gaps

**Untested areas:**

**Copy/cut/paste operations (`paste_hidden.py`):**
- `copy_hidden()` (line 20-56): Complex node classification logic, knob manipulation
- `cut_hidden()` (line 59-66): Deletion side effects
- `paste_hidden()` (line 69-100): Node replacement logic, selection management
- `paste_multiple_hidden()` (line 103-117): Multi-paste edge cases
- Files: `paste_hidden.py`
- Risk: Core functionality untested; bugs in node selection/deletion/replacement undetected

**Anchor management (`anchor.py`):**
- `create_anchor_named()` (line 232-257): Node creation, positioning, color logic
- `rename_anchor_to()` (line 140-169): Rename cascade across link nodes
- `reconnect_anchor_node()` (line 193-200): Link node updates
- `AnchorPlugin.get_color()` (line 319-325): Color extraction from node
- Files: `anchor.py`
- Risk: Anchor tracking broken if renaming fails; name sanitization not validated

**Link node tracking (`link.py`):**
- `find_anchor_node()` (line 148-163): Cross-script reference resolution
- `get_fully_qualified_node_name()` (line 17-19): Script name parsing
- `setup_link_node()` (line 131-146): Complex knob setup
- Files: `link.py`
- Risk: Cross-script links may silently fail; FQNN parsing depends on naming conventions

**Node color detection (`link.py`):**
- `find_node_default_color()` (line 22-30): Preference parsing
- `find_node_color()` (line 33-37): Fallback chain
- `find_anchor_color()` (`anchor.py:44-68`): Multi-step color resolution
- Files: `link.py`, `anchor.py`
- Risk: Color lookup brittle to Nuke preference changes; backdrop detection O(n) scan

**Qt widget management (`anchor.py`):**
- `select_anchor_and_create()` (line 364-383): Widget lifecycle
- `select_anchor_and_navigate()` (line 435-454): Widget recreation on error
- Global state: `_anchor_picker_widget`, `_anchor_navigate_widget`
- Files: `anchor.py`
- Risk: Window state corruption if RuntimeError handling fails; memory leaks if widget not destroyed

**Tabtabtab command palette (`tabtabtab.py`):**
- `launch()` (line 710-733): Plugin initialization and window management
- `_traverse_qt_menu()` (line 63-91): Menu traversal and item collection
- `consec_find()` (line 107-125): Consecutive character matching algorithm
- `nonconsec_find()` (line 127-159): Non-consecutive character matching algorithm
- Files: `tabtabtab.py`
- Risk: Search algorithms untested; menu traversal may skip items

**Edge cases:**
- Empty anchor names after sanitization (`anchor.py:155-157`)
- Cross-script link references (`link.py:158-160`)
- Widget destruction during operation (`anchor.py:371-377`)
- File I/O errors in weights persistence (`tabtabtab.py:249-253`)
- Missing input nodes (None checks scattered throughout)

## TODO Comments Found

**In tabtabtab.py:**

1. Line 256: `# TODO: Limit number of saved items to some sane number`
   - Issue: Weights file unbounded growth
   - Files: `tabtabtab.py`
   - Impact: Memory/storage bloat over time

2. Line 412: `# TODO: Is there a way to get this via data()? There's no`
   - Issue: Alternative API pattern unknown
   - Files: `tabtabtab.py`
   - Context: Qt menu data retrieval in `_traverse_qt_menu()`

3. Line 423: `# TODO: Maybe check for IndexError?`
   - Issue: List access without bounds check
   - Files: `tabtabtab.py`
   - Risk: Potential crash on malformed menu structure

4. Line 714: `# TODO: Is there a better way of doing this? If a`
   - Issue: Code quality concern in `launch()` function
   - Files: `tabtabtab.py`
   - Context: Incomplete comment, implementation unclear

## Common Patterns Observed

**None-safety checks:**
```python
if input_node is None:
    return None
# or
if input_node is not None:
    # use input_node
```
Used throughout for Nuke API calls that return None on failure.

**Node existence checks:**
```python
if nuke.exists(node.name()):
    # node still valid, proceed
```
Found in `anchor.py:313`, `anchor.py:417` - defensive checks before using nodes.

**Silent failures vs exceptions:**
- Silent: `is_anchor()` returns False on exception
- Exception: `create_anchor_named()` raises ValueError if name invalid
- Pattern: Query operations silent, creation operations raise

**Global widget state management:**
```python
global _anchor_picker_widget
if _anchor_picker_widget is not None:
    try:
        _anchor_picker_widget.under_cursor()
        # ...
    except RuntimeError:
        _anchor_picker_widget = None
```
Found in `anchor.py:361-383`, `anchor.py:432-454` - fragile pattern for widget lifecycle.

---

*Testing analysis: 2026-03-03*
