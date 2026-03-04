# Coding Conventions

**Analysis Date:** 2026-03-03

## Naming Patterns

**Files:**
- All lowercase with underscores: `paste_hidden.py`, `anchor.py`, `link.py`, `labels.py`
- Single words when possible: `constants.py`, `util.py`, `menu.py`
- Core entry point matches package name: `paste_hidden.py`

**Functions:**
- snake_case for all functions: `copy_hidden()`, `paste_multiple_hidden()`, `sanitize_anchor_name()`
- Verb-noun structure for operations: `create_anchor()`, `rename_anchor()`, `find_anchor_node()`
- Query predicates as is_/has_ prefixes: `is_anchor()`, `is_link()`
- Helper/internal functions prefixed with underscore: `_apply_label()`, `_update_dot_link_labels()`, `_normalize_qt_item_name()`
- Find/get/create prefixes for retrieval and creation: `get_fully_qualified_node_name()`, `find_node_color()`, `create_anchor_named()`

**Variables:**
- snake_case for all variables: `selected_nodes`, `input_node`, `anchor_node`, `link_class`
- Descriptive names without abbreviation per user preferences: `display_name` not `dname`, `fully_qualified_name_from_knob` not `fqn`
- Loop iterators: conventional `i`, `j`, `k`, `n` are acceptable
- Node references use full names: `anchor_node`, `link_node`, `input_node`, `source_node`
- Constant parameter names match usage: `node`, `anchor`, `text`, `name`

**Types:**
- No explicit type hints in codebase (Python without type annotations)
- Parameter names convey type: `node`, `nodes_so_far`, `menuobj`, `thing`
- Boolean predicates: `is_anchor`, `is_link`, `is_visible`, `is_enabled`

**Constants:**
- UPPER_CASE for all module-level constants in `constants.py`:
  - `TAB_NAME = 'copy_hidden_tab'`
  - `KNOB_NAME = 'copy_hidden_input_node'`
  - `ANCHOR_PREFIX = 'Anchor_'`
  - `ANCHOR_DEFAULT_COLOR = 0x6f3399ff`
  - `DOT_LABEL_FONT_SIZE_LARGE = 111`
- Magic numbers extracted to named constants: font sizes, color values, indices

## Code Style

**Formatting:**
- No explicit formatter detected (no `.prettierrc`, `black`, `autopep8`)
- Follows PEP 8 conventions:
  - 4-space indentation
  - Max line length ~80-100 characters (most lines well under)
  - Two blank lines between top-level functions
  - One blank line between methods in classes

**Linting:**
- No linter configuration found (no `.flake8`, `.pylintrc`, `pyproject.toml`)
- Code appears to follow PEP 8 organically

## Import Organization

**Order:**
1. Standard library imports: `os`, `re`
2. Third-party Qt imports with fallback handling:
   ```python
   try:
       if hasattr(nuke, 'NUKE_VERSION_MAJOR') and nuke.NUKE_VERSION_MAJOR >= 16:
           from PySide6 import QtCore, QtGui, QtWidgets
       else:
           from PySide2 import QtGui, QtWidgets, QtCore
   except ImportError:
       QtGui = None
   ```
3. Nuke SDK imports: `import nuke`, `import nukescripts`
4. Local module imports: `from constants import`, `from link import`
5. Aliased imports for clarity: `import tabtabtab as _tabtabtab`

**Path Aliases:**
- Local modules use relative imports: `from constants import`, `from link import`
- Cross-module functions imported explicitly: `from link import get_fully_qualified_node_name, is_anchor, is_link`
- No wildcard imports (`from x import *`)

**Grouping Strategy:**
- Group related imports by module section:
  - Foundational: `constants.py` provides all shared configuration
  - Core utilities: `link.py` contains node manipulation predicates
  - Business logic: `anchor.py`, `paste_hidden.py` use link.py and constants.py
  - UI/Integration: `labels.py`, `menu.py` compose the above

## Error Handling

**Patterns:**

**Try-Except with broad exception catching (used sparingly):**
```python
def is_anchor(node):
    try:
        if node.name().startswith(ANCHOR_PREFIX):
            return True
        # ... more logic ...
        return False
    except Exception:
        return False
```
Found in `link.py:77-91`. Used to safely check node properties that may fail if node is invalid.

**Try-Except with specific exceptions:**
```python
try:
    _anchor_picker_widget.under_cursor()
    _anchor_picker_widget.show()
    _anchor_picker_widget.raise_()
    return
except RuntimeError:
    _anchor_picker_widget = None
```
Found in `anchor.py:371-377`. Catches `RuntimeError` when widget is destroyed; resets to None.

**Exception silencing for cleanup:**
```python
try:
    node.removeKnob(node[KNOB_NAME])
except Exception:
    pass
```
Found in `link.py:112-119`. Silently fails if knob doesn't exist, preventing noisy errors during cleanup.

**Explicit ValueError raising with descriptive messages:**
```python
if not sanitized:
    raise ValueError(f"Anchor name {name!r} produces an empty sanitized name")
```
Found in `anchor.py:157`. Raises with context rather than returning None/False.

**Try-except in file I/O:**
```python
try:
    with open(weights_file, 'r') as fp:
        weights = json.load(fp)
except ValueError:
    # JSON parse error
    pass
except OSError as e:
    if e.errno == 2:
        # File not found is acceptable
        pass
    else:
        raise
```
Found in `tabtabtab.py:249-253`. Distinguishes file-not-found from real errors.

## Logging

**Framework:** No logging framework used.

**Patterns:**
- Uses Nuke's built-in user dialogs: `nuke.getInput()`, `nuke.Panel()`
- No debug logging infrastructure
- No structured logging
- Silent failures in utilities (return None/False rather than logging)
- User-facing functions raise `ValueError` with descriptive messages

## Comments

**When to Comment:**
- Function docstrings for all public functions explaining purpose, parameters, and return values
- Inline comments for non-obvious logic or multi-step processes
- Bug fix explanations included in comments (e.g., `anchor.py:74-75`, `anchor.py:194-195`)

**JSDoc/TSDoc:**
Python docstrings follow simple convention:
```python
def rename_anchor_to(anchor_node, name):
    """Rename an anchor to *name* and update all referencing link nodes.

    Raises ValueError if *name* sanitizes to an empty string (NoOp anchors only).
    For Dot anchors the label is updated directly; the node name (and FQNN) is
    left unchanged because it is the stable identifier used in link tracking.
    """
```

Docstrings include:
- One-line summary
- Multi-line explanation of behavior
- Exception documentation (what raises, when)
- Special cases and side effects

## Function Design

**Size:**
- Most functions 5-30 lines
- Longer functions with clear sub-steps (e.g., `find_anchor_color()` ~25 lines with 3 numbered priority sections)
- Complex functions broken into helper functions: `anchor.py:140-169` (rename_anchor_to) calls `sanitize_anchor_name()` and iterates through all nodes

**Parameters:**
- Single responsibility: most functions take 1-2 parameters
- Optional parameters use defaults: `create_anchor_named(name, input_node=None)`, `upstream_ignoring_hidden(node, nodes_so_far=None)`
- No *args or **kwargs patterns
- Parameters are passed objects (nodes, knobs) rather than primitive types

**Return Values:**
- Functions return the primary result: `create_anchor_named()` returns the new anchor node
- Predicates return boolean: `is_anchor()`, `is_link()`
- Queries return None when not found: `find_anchor_by_name()` returns None if not found
- Some functions return None for side-effect-only operations: `rename_anchor()`, `create_large_label()`
- Lists and sets returned when multiple results: `all_anchors()` returns sorted list, `upstream_ignoring_hidden()` returns set

## Module Design

**Exports:**
- No explicit `__all__` defined
- Public functions: no leading underscore
- Private/internal functions: leading underscore `_apply_label()`, `_update_dot_link_labels()`, `_normalize_qt_item_name()`
- Classes: `TabTabTabPlugin`, `AnchorPlugin`, `AnchorNavigatePlugin` defined for plugin system

**Barrel Files:**
None. Each module is imported explicitly:
- `import paste_hidden` → accesses `copy_hidden()`, `paste_hidden()`, `cut_hidden()` functions
- `import anchor` → accesses anchor functions
- `import labels` → accesses label functions

**Module Responsibilities:**
- `constants.py`: configuration and shared constants only
- `link.py`: node predicates and link setup (is_anchor, is_link, setup_link_node)
- `anchor.py`: anchor creation, renaming, navigation
- `paste_hidden.py`: copy/cut/paste operations with anchor support
- `labels.py`: visual label helpers for nodes
- `util.py`: generic graph utilities (upstream traversal)
- `tabtabtab.py`: command palette plugin system
- `menu.py`: Nuke menu registration (entry point)

---

*Convention analysis: 2026-03-03*
