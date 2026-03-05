"""Replace default copy-cut-paste behaviour to re-connect hidden inputs
and replace input-type nodes with hidden-inputted NoOp link nodes.

Configure which node classes trigger link replacement by editing LINK_SOURCE_CLASSES
in constants.py.
"""

import nuke
import nukescripts

from constants import (
    KNOB_NAME, LINK_SOURCE_CLASSES, HIDDEN_INPUT_CLASSES,
    DOT_TYPE_KNOB_NAME, LOCAL_DOT_COLOR, ANCHOR_DEFAULT_COLOR,
)
from anchor import find_anchor_by_name
from link import (
    is_anchor, is_link,
    get_fully_qualified_node_name,
    get_link_class_for_source,
    setup_link_node, add_input_knob,
    find_anchor_node,
)


def copy_hidden(cut=False):
    """Add a hidden knob storing the original name of the node/node's input. We
    can then, when pasting, replace the node or reconnect its inputs.

    Setting cut to True does not store the original name on nodes in LINK_SOURCE_CLASSES,
    causing our paste routine to do a normal paste without replacement. This is required
    for cuts, as the original node will have been deleted.
    """
    selected_nodes = nuke.selectedNodes()
    for node in selected_nodes:
        if is_link(node):
            continue

        # Path A — LINK_SOURCE_CLASSES file node: scan for an anchor whose input is this
        # node and store the anchor's FQNN so paste can read the correct link class
        # from the anchor's hidden knob. Falls back to the file node's own FQNN when
        # no anchor points at it (legacy direct-file-node path).
        if node.Class() in LINK_SOURCE_CLASSES:
            if cut:
                stored_fqnn = ""
            else:
                anchor_for_node = None
                for candidate in nuke.allNodes():
                    if is_anchor(candidate) and candidate.input(0) is node:
                        anchor_for_node = candidate
                        break
                if anchor_for_node is not None:
                    stored_fqnn = get_fully_qualified_node_name(anchor_for_node)
                else:
                    # Legacy fallback: no anchor found, store the file node's own FQNN
                    stored_fqnn = get_fully_qualified_node_name(node)
            add_input_knob(node)
            node[KNOB_NAME].setText(stored_fqnn)

        # Path B — hidden-input Dot (or PostageStamp/NoOp with hide_input set):
        # split on whether the upstream input is an anchor (Link Dot) or a plain node (Local Dot).
        elif node.Class() in HIDDEN_INPUT_CLASSES and node['hide_input'].getValue():
            input_node = node.input(0)
            if input_node is None or input_node in selected_nodes:
                stored_fqnn = ""
                add_input_knob(node)
            elif is_anchor(input_node):
                # Link Dot: anchor-backed, cross-script capable.
                # Override tile_color to canonical purple — setup_link_node() may apply a
                # custom anchor color via find_node_color(), which we do not want here.
                stored_fqnn = get_fully_qualified_node_name(input_node)
                setup_link_node(input_node, node)
                node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)
                add_input_knob(node, dot_type='link')
            else:
                # Local Dot: plain-node-backed, same-script only.
                # Restore Local appearance after setup_link_node() overwrites label/color.
                stored_fqnn = get_fully_qualified_node_name(input_node)
                setup_link_node(input_node, node)
                source_label = input_node['label'].getText() or input_node.name()
                node['label'].setValue(f"Local: {source_label}")
                node['tile_color'].setValue(LOCAL_DOT_COLOR)
                add_input_knob(node, dot_type='local')
            node[KNOB_NAME].setText(stored_fqnn)

        # Path C — existing anchor node (e.g. a NoOp named Anchor_*) being copied.
        elif is_anchor(node):
            stored_fqnn = "" if cut else get_fully_qualified_node_name(node)
            add_input_knob(node)
            node[KNOB_NAME].setText(stored_fqnn)

    # now that we've stored the info we need on the nodes, do a regular copy
    nuke.nodeCopy(nukescripts.cut_paste_file())


def cut_hidden():
    """Cut selected nodes (i.e. copy then delete). Do not store the original
    name in KNOB_NAME. This will disable replacement on paste.
    """
    selected_nodes = nuke.selectedNodes()
    copy_hidden(cut=True)
    for node in selected_nodes:
        nuke.delete(node)


def _extract_display_name_from_fqnn(stored_fqnn):
    """Extract the anchor display name from a stored FQNN for cross-script lookup.

    Returns the display name string (with ANCHOR_PREFIX stripped) if the last
    segment of the FQNN starts with ANCHOR_PREFIX, or None otherwise.
    Returns None for empty or blank FQNNs.
    """
    from constants import ANCHOR_PREFIX
    if not stored_fqnn:
        return None
    node_full_name = stored_fqnn.split('.')[-1]
    if node_full_name.startswith(ANCHOR_PREFIX):
        return node_full_name[len(ANCHOR_PREFIX):]
    return None


def paste_hidden():
    last_pasted_node = nuke.nodePaste(nukescripts.cut_paste_file())
    selected_nodes = nuke.selectedNodes()

    for node in selected_nodes:
        if KNOB_NAME not in node.knobs():
            # we haven't stored any info on this node, do nothing
            continue

        input_node = find_anchor_node(node)

        if node.Class() in LINK_SOURCE_CLASSES or is_anchor(node):
            # Path A/C: file node or anchor node pasted → replace with a link node.
            # find_anchor_node() resolves the stored FQNN; None means cross-script or
            # deleted.
            if not input_node:
                # Cross-script case: find_anchor_node() returned None because the
                # stored FQNN belongs to a different script. Attempt name-based
                # reconnect for NoOp anchors (XSCRIPT-01). Dot anchors and file
                # nodes are left disconnected as placeholders.
                if is_anchor(node) and node.Class() != 'Dot':
                    display_name = _extract_display_name_from_fqnn(
                        node[KNOB_NAME].getText()
                    )
                    if display_name:
                        destination_anchor = find_anchor_by_name(display_name)
                        if destination_anchor:
                            nukescripts.clear_selection_recursive()
                            node["selected"].setValue(True)
                            link_node = nuke.createNode(get_link_class_for_source(destination_anchor))
                            setup_link_node(destination_anchor, link_node)
                            link_node.setXYpos(node.xpos(), node.ypos())
                            selected_nodes.remove(node)
                            selected_nodes.append(link_node)
                            nuke.delete(node)
                            continue
                continue
            nukescripts.clear_selection_recursive()
            node["selected"].setValue(True)
            link_node = nuke.createNode(get_link_class_for_source(input_node))
            setup_link_node(input_node, link_node)
            link_node.setXYpos(node.xpos(), node.ypos())
            selected_nodes.remove(node)
            selected_nodes.append(link_node)
            nuke.delete(node)

        elif node.Class() in HIDDEN_INPUT_CLASSES:
            # Path B: hidden-input Dot (Link Dot or Local Dot).
            # Determine DOT_TYPE from the explicit knob if present; fall back to FQNN inspection
            # for pre-Phase-5 nodes that lack the knob.
            stored_fqnn = node[KNOB_NAME].getText()
            if DOT_TYPE_KNOB_NAME in node.knobs():
                dot_type = node[DOT_TYPE_KNOB_NAME].getValue()
            else:
                # Backward compat: infer from FQNN — anchor-prefix last segment → 'link',
                # else → 'local'.
                display_name_for_compat = _extract_display_name_from_fqnn(stored_fqnn)
                dot_type = 'link' if display_name_for_compat is not None else 'local'

            # Detect cross-script: compare stored FQNN script stem against current script stem.
            # Using FQNN stem comparison (not find_anchor_node() return value) as the cross-script
            # gate prevents same-stem false positives where find_anchor_node() returns a same-named
            # node from the destination script for a Local Dot.
            current_stem = nuke.root().name().split('.')[0]
            fqnn_stem = stored_fqnn.split('.')[0] if stored_fqnn else ''
            is_cross_script = bool(fqnn_stem) and (fqnn_stem != current_stem)

            if is_cross_script or not input_node:
                # Cross-script (or unresolvable FQNN): gate on DOT_TYPE.
                if dot_type == 'link':
                    # Link Dot: attempt name-based reconnect to same-named anchor in destination.
                    display_name = _extract_display_name_from_fqnn(stored_fqnn)
                    if display_name:
                        destination_anchor = find_anchor_by_name(display_name)
                        if destination_anchor:
                            setup_link_node(destination_anchor, node)
                            node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)
                # Local Dot: silent no-op — do not reconnect under any circumstances.
                continue

            # Same-script: reconnect to the original source by identity.
            # Read dot_type before calling setup_link_node() because setup_link_node()
            # calls add_input_knob() without dot_type, which strips the DOT_TYPE_KNOB_NAME
            # knob. Saving the value here makes the restoration guard reliable regardless
            # of whether the knob survives setup_link_node().
            saved_dot_type = (
                node[DOT_TYPE_KNOB_NAME].getValue()
                if DOT_TYPE_KNOB_NAME in node.knobs()
                else None
            )
            setup_link_node(input_node, node)
            if saved_dot_type == 'local':
                # Re-add the DOT_TYPE knob that setup_link_node stripped, then restore
                # Local Dot appearance (label and color overwritten by setup_link_node).
                add_input_knob(node, dot_type='local')
                source_label = input_node['label'].getText() or input_node.name()
                node['label'].setValue(f"Local: {source_label}")
                node['tile_color'].setValue(LOCAL_DOT_COLOR)

    # it's possible we changed selection, reset it
    nukescripts.clear_selection_recursive()
    for node in selected_nodes:
        node['selected'].setValue(True)

    # same return as nuke.nodePaste()
    return last_pasted_node


def paste_multiple_hidden():
    selected_nodes = nuke.selectedNodes()
    new_selection = []

    for node in selected_nodes:
        nukescripts.clear_selection_recursive()
        node["selected"].setValue(True)
        paste_hidden()

        new_selection.extend(nuke.selectedNodes())

    nukescripts.clear_selection_recursive()
    for node in new_selection:
        node["selected"].setValue(True)


def copy_old():
    nuke.nodeCopy(nukescripts.cut_paste_file())


def cut_old():
    selected_nodes = nuke.selectedNodes()
    nuke.nodeCopy(nukescripts.cut_paste_file())
    for node in selected_nodes:
        nuke.delete(node)


def paste_old():
    nuke.nodePaste(nukescripts.cut_paste_file())
