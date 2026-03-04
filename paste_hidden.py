"""Replace default copy-cut-paste behaviour to re-connect hidden inputs
and replace input-type nodes with hidden-inputted link nodes.

Configure additional nodes to replace and the link node to replace them
with by editing LINK_CLASSES in constants.py.
"""

import nuke
import nukescripts

from constants import KNOB_NAME, LINK_CLASSES, HIDDEN_INPUT_CLASSES
from link import (
    is_anchor, is_link,
    get_fully_qualified_node_name,
    setup_link_node, add_input_knob,
    find_anchor_node, get_link_class_for_source,
)


def copy_hidden(cut=False):
    """Add a hidden knob storing the original name of the node/node's input. We
    can then, when pasting, replace the node or reconnect its inputs.

    Setting cut to True does not store the original name on nodes in LINK_CLASSES,
    causing our paste routine to do a normal paste without replacement. This is required
    for cuts, as the original node will have been deleted.
    """
    selected_nodes = nuke.selectedNodes()
    for node in selected_nodes:
        if is_link(node):
            continue

        # Path A — LINK_CLASSES file node: scan for an anchor whose input is this
        # node and store the anchor's FQNN so paste can read the correct link class
        # from the anchor's hidden knob. Falls back to the file node's own FQNN when
        # no anchor points at it (legacy direct-file-node path).
        if node.Class() in LINK_CLASSES.keys():
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
        # split on whether the upstream input is an anchor or a plain node.
        elif node.Class() in HIDDEN_INPUT_CLASSES and node['hide_input'].getValue():
            input_node = node.input(0)
            if input_node is None or input_node in selected_nodes:
                stored_fqnn = ""
            elif is_anchor(input_node):
                # Dot/link node whose input IS an anchor → treat as a Link node;
                # store the anchor's FQNN so paste can reconnect via setup_link_node.
                stored_fqnn = get_fully_qualified_node_name(input_node)
                setup_link_node(input_node, node)
            else:
                # Legacy: non-anchor input — identity reconnect path on paste.
                stored_fqnn = get_fully_qualified_node_name(input_node)
                setup_link_node(input_node, node)
            add_input_knob(node)
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


def paste_hidden():
    last_pasted_node = nuke.nodePaste(nukescripts.cut_paste_file())
    selected_nodes = nuke.selectedNodes()

    for node in selected_nodes:
        if KNOB_NAME not in node.knobs():
            # we haven't stored any info on this node, do nothing
            continue

        input_node = find_anchor_node(node)

        if node.Class() in LINK_CLASSES.keys() or is_anchor(node):
            # Path A/C: file node or anchor node pasted → replace with a link node.
            # find_anchor_node() resolves the stored FQNN; None means cross-script or
            # deleted — skip silently so the pasted placeholder node remains as-is.
            if not input_node:
                continue
            nukescripts.clear_selection_recursive()
            node["selected"].setValue(True)
            # get_link_class_for_source dispatches to the anchor's stored knob when
            # input_node is an anchor (Camera anchor → NoOp, Read anchor → PostageStamp).
            # Do NOT pass the anchor directly expecting re-detection — the dispatch
            # handles this correctly via get_link_class_for_anchor().
            link_class = get_link_class_for_source(input_node)
            link_node = nuke.createNode(link_class)
            setup_link_node(input_node, link_node)
            link_node.setXYpos(node.xpos(), node.ypos())
            selected_nodes.remove(node)
            selected_nodes.append(link_node)
            nuke.delete(node)

        elif node.Class() in HIDDEN_INPUT_CLASSES:
            # Path B: hidden-input Dot — reconnect to the stored source node.
            # find_anchor_node() returns None for cross-script or unresolvable FQNNs;
            # skip silently in that case (PASTE-03/PASTE-04 legacy Dot cross-script).
            if not input_node:
                continue
            setup_link_node(input_node, node)

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
