"""
Replace default copy-cut-paste behaviour to re-connect hidden inputs
and replace input-type nodes with hidden-inputted dummy nodes.

Configure additional nodes to replace and the dummy to replace them
with by editing REPLACEMENT_CLASSES.
"""

import nuke
import nukescripts

TAB_NAME = 'copy_hidden_tab'
KNOB_NAME = 'copy_hidden_input_node'
HIDDEN_INPUT_CLASSES = ['PostageStamp', 'Dot', 'NoOp']
REPLACEMENT_CLASSES = {
    "Read": "PostageStamp",
    "DeepRead": "NoOp",
    "ReadGeo": "NoOp",
    "Camera": "NoOp",
    "Camera2": "NoOp",
    "Camera3": "NoOp",
    "Camera4": "NoOp",
    "GeoImport": "NoOp",
}
PARENT_CLASSES = ['NoOp', 'Dot']


def setup_replacement_node(input_node, replacement_node):
    replacement_node["hide_input"].setValue(True)
    replacement_node["tile_color"].setValue(find_node_color(input_node))
    if input_node.Class() == "Dot" and input_node["label"].getText() != "":
        replacement_node["label"].setValue(f"Pointed to: {input_node['label'].getText()}")
    else:
        replacement_node["label"].setValue(
            f"Pointed to: {input_node.name()}\n"
            f"{input_node['label'].getText()}"
        )
    replacement_node["note_font_size"].setValue(input_node["note_font_size"].value())
    replacement_node.setInput(0, input_node)


def find_node_default_color(node):
    prefs = nuke.toNode("preferences")
    node_colour_slots = [
        prefs[knob_name].value().split(' ')
        for knob_name in prefs.knobs()
        if knob_name.startswith("NodeColourSlot")
    ]
    node_colour_slots = [
        [item.replace("'", "").lower() for item in parent_item]
        for parent_item in node_colour_slots
    ]
    node_colour_choices = [
        prefs[knob_name].value()
        for knob_name in prefs.knobs()
        if knob_name.startswith("NodeColourChoice")
    ]
    for i, slot in enumerate(node_colour_slots):
        if node.Class().lower() in slot:
            return node_colour_choices[i]
    return prefs["NodeColor"].value()


def find_node_color(node):
    tile_color = node["tile_color"].value()
    if tile_color == 0:
        tile_color = find_node_default_color(node)
    return tile_color


def add_input_knob(node):
    # remove our custom knobs to make sure they're at the end
    try:
        node.removeKnob(node[KNOB_NAME])
    except Exception as e:
        pass
    try:
        node.removeKnob(node[TAB_NAME])
    except Exception as e:
        pass

    tab = nuke.Tab_Knob(TAB_NAME)
    tab.setFlag(nuke.INVISIBLE)
    tab.setVisible(False)
    node.addKnob(tab)

    k = nuke.String_Knob(KNOB_NAME)
    k.setVisible(False)
    node.addKnob(k)


def get_fully_qualified_node_name(node):
    """We need the script name as part of the full name of the node,
    to avoid attempting to make a PostageStamp etc. in another script"""

    return f"{nuke.root().name().split('.')[0]}.{node.fullName()}"


def copy_hidden(cut=False):
    """Add a hidden knob storing the original name of the node/node's input. We
    can then, when pasting, replace the node or reconnect its inputs.

    Setting cut to True does not store the original name on nodes in REPLACEMENT_CLASSES,
    causing our paste routine to do a normal paste without replacement. This is required
    for cuts, as the original node will have been deleted.
    """
    selected_nodes = nuke.selectedNodes()
    for node in selected_nodes:
        if node.Class() in HIDDEN_INPUT_CLASSES and node['hide_input'].getValue():
            input_node = node.input(0)
            if input_node is None or input_node in selected_nodes:
                input_node_name = ""
            else:
                input_node_name = get_fully_qualified_node_name(input_node)
            add_input_knob(node)
            node[KNOB_NAME].setText(input_node_name)
            setup_replacement_node(input_node, node)
        elif node.Class() in REPLACEMENT_CLASSES.keys():
            input_node_name = get_fully_qualified_node_name(node)
            if cut:
                # don't store the replacement name, we do not want to replace
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


def find_input_node(node):
    if KNOB_NAME not in node.knobs():
        # we haven't stored any info on this node, do nothing
        return
    fully_qualifed_name_from_knob = node[KNOB_NAME].getText()
    fqn_from_knob_split = fully_qualifed_name_from_knob.split(".")

    # strip off the script name to get Nuke's version of a full name
    full_name_from_knob = ".".join(fqn_from_knob_split[1:])
    fully_qualifed_name_from_current = get_fully_qualified_node_name(node)
    fqn_from_current_split = fully_qualifed_name_from_current.split(".")
    prefix_from_knob = fqn_from_knob_split[:-1]
    prefix_from_current = fqn_from_current_split[:-1]
    if prefix_from_knob != prefix_from_current:
        # we are in a different script and/or Group, do nothing
        return
    input_node = nuke.toNode(full_name_from_knob)
    return input_node



def paste_hidden():
    last_pasted_node = nuke.nodePaste(nukescripts.cut_paste_file())
    selected_nodes = nuke.selectedNodes()

    for node in selected_nodes:
        if node.Class() in REPLACEMENT_CLASSES.keys():
            input_node = find_input_node(node)
            if not input_node:
                continue
            nukescripts.clear_selection_recursive()
            node["selected"].setValue(True)
            replacement_node = nuke.createNode(REPLACEMENT_CLASSES[node.Class()])
            input_node = nuke.toNode(full_name_from_knob)
            setup_replacement_node(input_node, replacement_node)
            # add_input_knob(replacement_node)
            # replacement_node[KNOB_NAME].setValue(fully_qualifed_name_from_knob)
            replacement_node.setXYpos(node.xpos(), node.ypos())
            selected_nodes.remove(node)
            selected_nodes.append(replacement_node)
            nuke.delete(node)
        elif node.Class() in HIDDEN_INPUT_CLASSES:
            input_node = find_input_node(node)
            if not input_node:
                continue
            setup_replacement_node(input_node, node)

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
        dependents = node.dependent()

        nukescripts.clear_selection_recursive()
        node["selected"].setValue(True)
        last_pasted_node = paste_hidden()

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


def reconnect_all():
    hidden_input_nodes = [
        node
        for node in nuke.allNodes()
        if node.Class() in HIDDEN_INPUT_CLASSES and
        node["hide_input"].getValue()
    ]
    for node in hidden_input_nodes:
        input_node = find_input_node(node)
        if input_node is None:
            continue
        setup_replacement_node(input_node, node)


def find_labelled_parents():
    candidates = [
        node for node in nuke.allNodes()
        if node.Class() in PARENT_CLASSES and
        node["label"].getText() != ""
    ]
    return candidates
