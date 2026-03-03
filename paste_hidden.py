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
        if is_anchor(node):
            input_node_name = get_fully_qualified_node_name(node)
            if cut:
                input_node_name = ""
            add_input_knob(node)
            node[KNOB_NAME].setText(input_node_name)
        elif node.Class() in HIDDEN_INPUT_CLASSES and node['hide_input'].getValue():
            input_node = node.input(0)
            if input_node is None or input_node in selected_nodes:
                input_node_name = ""
            else:
                input_node_name = get_fully_qualified_node_name(input_node)
                setup_link_node(input_node, node)
            add_input_knob(node)
            node[KNOB_NAME].setText(input_node_name)
        elif node.Class() in LINK_CLASSES.keys():
            input_node_name = get_fully_qualified_node_name(node)
            if cut:
                # don't store the link name, we do not want to replace
                input_node_name = ""
            add_input_knob(node)
            node[KNOB_NAME].setText(input_node_name)

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
        if not input_node:
            continue

        if is_anchor(node) or node.Class() in LINK_CLASSES.keys():
            nukescripts.clear_selection_recursive()
            node["selected"].setValue(True)
            link_node = nuke.createNode(get_link_class_for_source(input_node))
            setup_link_node(input_node, link_node)
            link_node.setXYpos(node.xpos(), node.ypos())
            selected_nodes.remove(node)
            selected_nodes.append(link_node)
            nuke.delete(node)
        elif node.Class() in HIDDEN_INPUT_CLASSES:
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
