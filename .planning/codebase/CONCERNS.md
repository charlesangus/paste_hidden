# Codebase Concerns

**Analysis Date:** 2026-03-03

## Tech Debt

**Bare Exception Handling:**
- Issue: Multiple functions use bare `except Exception` without specificity, making it difficult to understand which exceptions are expected or to debug unexpected failures.
- Files: `link.py:90`, `link.py:114`, `link.py:118`, `tabtabtab.py:40`, `tabtabtab.py:228`, `tabtabtab.py:263`, `tabtabtab.py:590`
- Impact: Silent failures, harder debugging, loss of exception context in error handling paths. If unexpected exceptions occur, they are silently swallowed.
- Fix approach: Replace bare `except Exception` with specific exception types (e.g., `AttributeError`, `ValueError`, `TypeError`). Add logging to understand why exceptions are being caught.

**Uninitialized Global Widget References:**
- Issue: `_anchor_picker_widget` and `_anchor_navigate_widget` in `anchor.py` are module-level globals that are checked with `try/except RuntimeError` on access.
- Files: `anchor.py:361`, `anchor.py:370-382`, `anchor.py:432`, `anchor.py:440-454`
- Impact: Fragile reference handling; if the widget is garbage collected unexpectedly, the exception is caught and variable is reset, but this is not a reliable pattern. Could mask other RuntimeErrors.
- Fix approach: Use weakref.proxy consistently (as done in `tabtabtab.py:739`) or implement a cleaner widget lifecycle manager with explicit creation/destruction hooks.

**Bare ValueError Catches:**
- Issue: `anchor.py:184` and `anchor.py:220` catch `ValueError` from `rename_anchor_to()` and `create_anchor_named()` silently without any user feedback.
- Files: `anchor.py:181-184`, `anchor.py:217-220`
- Impact: User receives no feedback when anchor name validation fails (e.g., name with only special characters). User expects an error message.
- Fix approach: Catch and display error to user via `nuke.warning()` or keep the exception handling but add console logging.

**File Handle Not Explicitly Closed (tabtabtab.py):**
- Issue: File handles opened in `NodeWeights.load()` and `NodeWeights.save()` may not be closed if exceptions occur before `f.close()`.
- Files: `tabtabtab.py:220-221`, `tabtabtab.py:255-258`
- Impact: Resource leak if JSON parsing fails or if write fails; potential file lock issues on Windows.
- Fix approach: Use context manager `with open(...) as f:` instead of manual open/close.

**Index Error Potential in tabtabtab.py:**
- Issue: Line 423 has a TODO comment noting that `getorig()` may fail with `IndexError` but doesn't check.
- Files: `tabtabtab.py:411-425`
- Impact: If `_items` is empty or index is out of bounds, accessing `self._items[selected.row()]` will raise `IndexError`.
- Fix approach: Add bounds checking before accessing `_items[selected.row()]`.

## Known Bugs

**Cross-Script Reference Detection:**
- Issue: `find_anchor_node()` in `link.py` compares script prefixes to detect cross-script references, but this assumes the FQNN format `<script>.<full_name>` is always followed. If a node's fully qualified name changes or script naming is unusual, this could fail silently.
- Files: `link.py:148-162`
- Symptoms: Link nodes created from anchors in different scripts may fail to reconnect if script names or node hierarchies change.
- Trigger: Save a script with cross-script anchor references, rename the script, reload.
- Workaround: Manually call `anchor.reconnect_all_links()` after script operations.

**Widget Persistence After Exception:**
- Issue: In `anchor.py`, if `_anchor_picker_widget.under_cursor()` raises an exception other than `RuntimeError`, the widget remains in the global state but the exception is not properly handled.
- Files: `anchor.py:370-377`
- Symptoms: Widget state becomes inconsistent; subsequent calls may fail or show stale data.
- Trigger: Call `select_anchor_and_create()` when the widget exists and `under_cursor()` raises an unexpected exception.
- Workaround: Restart Nuke.

**Label Propagation on Dot Anchors:**
- Issue: When a Dot anchor is renamed, `rename_anchor_to()` updates linked node labels, but if a link node is deleted and recreated, it may not automatically update its label from the anchor's current label.
- Files: `anchor.py:147-169`, `labels.py:15-24`
- Symptoms: Stale "Link: " labels on newly created link nodes if they reference Dot anchors with pending label changes.
- Trigger: Rename a Dot anchor, then create a new link without explicitly reconnecting first.
- Workaround: Call `anchor.reconnect_all_links()` after creating new links.

## Security Considerations

**File Path Handling:**
- Risk: `suggest_anchor_name()` in `anchor.py` uses `os.path.basename()` and regex parsing on file paths from Read nodes without validation. If a malicious file path is provided or contains special characters, the regex could fail or produce unexpected names.
- Files: `anchor.py:117-137`
- Current mitigation: `sanitize_anchor_name()` strips non-alphanumeric characters, which provides some protection.
- Recommendations: Add validation for file paths before processing; ensure regex patterns are robust to edge cases.

**User Input Validation:**
- Risk: `rename_anchor_to()` and `create_anchor_named()` accept user input for anchor names. The only validation is `sanitize_anchor_name()`, which strips invalid characters but allows any whitespace/empty-like names after stripping.
- Files: `anchor.py:140-170`, `anchor.py:232-257`
- Current mitigation: `sanitize_anchor_name()` checks if result is empty and raises `ValueError`.
- Recommendations: Consider additional checks (e.g., reserved names, length limits) if anchor names are used in other contexts.

**Preferences Node Access:**
- Risk: `find_node_default_color()` in `link.py` accesses the Nuke preferences node directly without error handling. If the preferences node doesn't exist or is in an unexpected state, this will fail.
- Files: `link.py:22-30`
- Current mitigation: None explicitly.
- Recommendations: Wrap in try/except and provide a sensible fallback color.

## Performance Bottlenecks

**Full Graph Traversal on Anchor Operations:**
- Problem: Multiple operations iterate over `nuke.allNodes()` without filtering, which scans the entire node graph.
- Files: `anchor.py:98` (all_anchors), `anchor.py:114` (get_links_for_anchor), `anchor.py:151`, `anchor.py:165`, `anchor.py:197`, `anchor.py:203` (reconnect operations), `labels.py:18` (label updates), `link.py:44` (backdrop search)
- Cause: No index or caching of anchor/link nodes by name; every operation does a full linear search.
- Impact: In scripts with hundreds of nodes, operations like `rename_anchor()` or `reconnect_all_links()` become noticeably slow.
- Improvement path: Implement a lightweight cache of anchor/link nodes keyed by FQNN or anchor name. Update cache on node creation/deletion. Rebuild cache periodically on script load.

**Repeated Preferences Lookups:**
- Problem: `find_node_default_color()` is called frequently and re-parses all preferences knobs each time.
- Files: `link.py:22-30`
- Cause: Preferences parsing done on every call with no caching.
- Impact: Slow color resolution for many anchor/link nodes.
- Improvement path: Cache `nuke.toNode("preferences")` and knob values during initialization or first lookup.

**Fuzzy Search in Large Anchor Lists:**
- Problem: tabtabtab's `NodeModel.update()` performs fuzzy search on every keystroke, iterating through all items.
- Files: `tabtabtab.py:307-371`
- Cause: No incremental search or indexing.
- Impact: Slow picker response with 100+ anchors.
- Improvement path: Consider implementing prefix-based indexing or asynchronous search if anchor lists grow large.

## Fragile Areas

**Anchor Display Name Detection:**
- Files: `anchor.py:91-94`
- Why fragile: For Dot nodes, relies on label text; for NoOp nodes, uses node name minus prefix. If a label is empty or a node is renamed outside the anchor system, the display name becomes inconsistent.
- Safe modification: Always use `anchor_display_name()` to retrieve display names; never cache them. Validate that label/name exists before using.
- Test coverage: No explicit tests for edge cases (empty labels, renamed nodes).

**Cross-Script Fully Qualified Node Names:**
- Files: `link.py:17-19`, `link.py:148-162`
- Why fragile: FQNN format assumes `<script>.<full_name>`. If Nuke's script naming or node naming conventions change, or if nodes exist in nested Groups with unusual names, the parsing could fail silently.
- Safe modification: Add validation in `get_fully_qualified_node_name()` to ensure the format is correct. Add tests for nested Group structures.
- Test coverage: No tests for Groups or complex hierarchies.

**Widget Lifecycle Management:**
- Files: `anchor.py:361-383`, `anchor.py:432-454`, `tabtabtab.py:707-739`
- Why fragile: Global widget references rely on weakref.proxy and RuntimeError catching. If Qt's object lifecycle changes or if the widget is used from multiple threads, this could break.
- Safe modification: Refactor to use a dedicated widget manager class with explicit lifecycle hooks. Consider using Qt's built-in parent/child relationships.
- Test coverage: No tests for widget creation/destruction or concurrent access.

**Label Synchronization on Dot Anchors:**
- Files: `labels.py:15-24`, `anchor.py:147-169`
- Why fragile: When renaming a Dot anchor, the system updates all linked nodes' labels, but if links are added/removed during this update, or if an exception occurs mid-update, links can become out of sync.
- Safe modification: Implement transactional label updates (batch all updates, then commit). Add validation that all linked nodes have consistent labels.
- Test coverage: No tests for partial updates or exception scenarios.

## Scaling Limits

**Graph Size with Anchors:**
- Current capacity: Works well up to ~50-100 anchors in a single script.
- Limit: Beyond ~200 anchors, picker responsiveness degrades; full-graph operations become slow.
- Scaling path: Implement anchor indexing by name; use tabtabtab's built-in weighting to improve search performance; consider hierarchical anchor grouping (e.g., "Scene/Lighting/main_light").

**Nuke Version Compatibility:**
- Current capacity: Code supports both PySide2 (Nuke <16) and PySide6 (Nuke 16+).
- Limit: Testing likely focused on 1-2 recent Nuke versions; may have undiscovered issues in very old or very new Nuke versions.
- Scaling path: Establish minimum/maximum supported versions; add CI testing across Nuke versions.

## Dependencies at Risk

**PySide2/PySide6 Compatibility:**
- Risk: Code has try/except fallback between PySide6 and PySide2, but both are set to None if both imports fail, causing silent failures in functions that require Qt.
- Files: `anchor.py:9-19`, `tabtabtab.py:12-17`
- Impact: If Qt imports fail, widget-based functions silently return without error. Users get no feedback about the issue.
- Migration plan: Add explicit error handling; warn user at plugin load time if Qt is unavailable. Consider splitting Qt-dependent code into a separate module.

**tabtabtab Integration:**
- Risk: tabtabtab is embedded in this codebase but appears to be maintained separately (comments reference GitHub). If tabtabtab bugs or incompatibilities are discovered, fixes must be applied in two places.
- Files: `tabtabtab.py` (entire file)
- Impact: Bug fixes or features in upstream tabtabtab won't automatically apply here.
- Migration plan: Consider extracting tabtabtab to a separate dependency with version pinning, or establish a merge strategy to keep local version in sync.

## Missing Critical Features

**No Undo/Redo Support:**
- Problem: Anchor creation, renaming, and link reconnection operations don't integrate with Nuke's undo stack.
- Blocks: Users cannot undo anchor operations easily; scripts can become inconsistent if undo is called during an anchor operation.
- Impact: User frustration; potential data loss if user relies on undo after inadvertent anchor renames.

**No Persistence for Cross-Script References:**
- Problem: Anchor references are stored as FQNN strings in knobs, but if a script is moved to a different directory or opened in a different context, cross-script references may break.
- Blocks: Large multi-script projects with shared anchors are fragile.
- Impact: Hard to maintain complex projects with many interdependent scripts.

**No Conflict Resolution for Anchor Name Collisions:**
- Problem: If two scripts have anchors with the same display name, the picker will show both but selection behavior is undefined.
- Blocks: Cross-script anchor merging without manual renaming is not possible.
- Impact: Complex projects require careful naming discipline.

**No Batch Anchor Operations:**
- Problem: Only individual anchor creation/renaming is supported; no bulk import/export or templating.
- Blocks: Applying consistent anchor structures across multiple scripts requires manual work.
- Impact: Large template-based workflows are tedious.

## Test Coverage Gaps

**Widget Lifecycle:**
- What's not tested: Creation, destruction, reshow of picker widgets; behavior when widget is garbage collected; concurrent widget access.
- Files: `anchor.py:361-383`, `anchor.py:432-454`
- Risk: Widget state corruption; RuntimeError exceptions not caught; memory leaks.
- Priority: High

**Cross-Script References:**
- What's not tested: FQNN parsing with nested Groups, script renaming, script path changes, cross-script anchor deletion.
- Files: `link.py:17-19`, `link.py:148-162`
- Risk: Silent reconnection failures; stale references after script operations.
- Priority: High

**Label Propagation on Dot Anchors:**
- What's not tested: Renaming Dot anchors with multiple linked nodes; deleting linked nodes during rename; concurrent rename operations.
- Files: `labels.py:15-24`, `anchor.py:147-169`
- Risk: Label desynchronization; incomplete updates.
- Priority: Medium

**Exception Handling Edge Cases:**
- What's not tested: What happens when `nuke.getInput()` returns None; when `nuke.allNodes()` is called during script load/unload; when Nuke preferences are missing knobs.
- Files: `anchor.py` (throughout), `link.py:22-30`
- Risk: Unhandled exceptions; silent failures; user confusion.
- Priority: Medium

**Paste Operations with Complex Selection:**
- What's not tested: Paste operations with deeply nested Groups; paste with mixed node types; paste into empty selection; multiple paste operations in sequence without full reconnect.
- Files: `paste_hidden.py:69-100`, `paste_hidden.py:103-116`
- Risk: Reconnection failures; orphaned links.
- Priority: Medium

---

*Concerns audit: 2026-03-03*
