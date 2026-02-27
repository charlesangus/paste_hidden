"""
Replace default copy-cut-paste behaviour to re-connect hidden inputs
and replace input-type nodes with hidden-inputted link nodes.

Configure additional nodes to replace and the link node to replace them
with by editing LINK_CLASSES.
"""

import os
import re

import nuke
import nukescripts

try:
    if hasattr(nuke, 'NUKE_VERSION_MAJOR') and nuke.NUKE_VERSION_MAJOR >= 16:
        from PySide6 import QtCore, QtGui, QtWidgets
        from PySide6.QtCore import Qt
    else:
        from PySide2 import QtGui, QtWidgets, QtCore
        from PySide2.QtCore import Qt
except ImportError:
    QtGui = None
    QtWidgets = None
    QtCore = None

import tabtabtab as _tabtabtab

TAB_NAME = 'copy_hidden_tab'
KNOB_NAME = 'copy_hidden_input_node'
HIDDEN_INPUT_CLASSES = ['PostageStamp', 'Dot', 'NoOp']
LINK_CLASSES = {
    "Read": "PostageStamp",
    "DeepRead": "NoOp",
    "ReadGeo": "NoOp",
    "Camera": "NoOp",
    "Camera2": "NoOp",
    "Camera3": "NoOp",
    "Camera4": "NoOp",
    "GeoImport": "NoOp",
}

ANCHOR_RECONNECT_KNOB_NAME = "reconnect_child_links"
LINK_RECONNECT_KNOB_NAME = "reconnect_link"
ANCHOR_PREFIX = 'Anchor_'


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


def find_anchor_node(link_node):

    fully_qualifed_name_from_knob = link_node[KNOB_NAME].getText()
    fqn_from_knob_split = fully_qualifed_name_from_knob.split(".")

    # strip off the script name to get Nuke's version of a full name
    full_name_from_knob = ".".join(fqn_from_knob_split[1:])
    fully_qualifed_name_from_current = get_fully_qualified_node_name(link_node)
    fqn_from_current_split = fully_qualifed_name_from_current.split(".")
    prefix_from_knob = fqn_from_knob_split[:-1]
    prefix_from_current = fqn_from_current_split[:-1]
    if prefix_from_knob != prefix_from_current:
        # we are in a different script and/or Group, do nothing
        return None
    anchor_node = nuke.toNode(full_name_from_knob)
    return anchor_node


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


def reconnect_link_node(link_node):
    anchor_node = find_anchor_node(link_node)
    if not anchor_node:
        return None
    link_node.setInput(0, anchor_node)


def setup_link_node(input_node, link_node):
    link_node["hide_input"].setValue(True)
    link_node["tile_color"].setValue(find_node_color(input_node))
    
    if input_node["label"].getText():
        link_node["label"].setValue(f"Link: {input_node['label'].getText()}")
    else:
        link_node["label"].setValue(f"Link: {input_node.name()}")

    add_input_knob(link_node)
    link_node[KNOB_NAME].setValue(get_fully_qualified_node_name(input_node))
    link_node.setInput(0, input_node)


def find_node_default_color(node):
    prefs = nuke.toNode("preferences")
    node_colour_slots = [prefs[knob_name].value().split(' ') for knob_name in prefs.knobs() if knob_name.startswith("NodeColourSlot")]
    node_colour_slots = [[item.replace("'", "").lower() for item in parent_item] for parent_item in node_colour_slots]
    node_colour_choices = [prefs[knob_name].value() for knob_name in prefs.knobs() if knob_name.startswith("NodeColourChoice")]
    for i, slot in enumerate(node_colour_slots):
        if node.Class().lower() in slot:
            return node_colour_choices[i]
    return prefs["NodeColor"].value()


def find_node_color(node):
    tile_color = node["tile_color"].value()
    if tile_color == 0:
        tile_color = find_node_default_color(node)
    return tile_color


def find_anchor_color(anchor):
    """Return the tile color an anchor should display.

    Priority:
      1. Smallest BackdropNode containing the anchor — only when the anchor's
         input is a Read node.
      2. The anchor's input node color (with Preferences fallback).
      3. Hard-coded default purple if neither is available.
    """
    ANCHOR_DEFAULT_COLOR = 0x6f3399ff

    input_node = anchor.input(0)

    # --- 1. Backdrop color — only for Read nodes ---
    if input_node is not None and input_node.Class() == 'Read':
        ax, ay = anchor.xpos(), anchor.ypos()
        containing = []
        for bd in nuke.allNodes('BackdropNode'):
            bx = bd.xpos()
            by = bd.ypos()
            bw = bd['bdwidth'].value()
            bh = bd['bdheight'].value()
            if bx <= ax < bx + bw and by <= ay < by + bh:
                containing.append(bd)

        if containing:
            smallest = min(containing, key=lambda bd: bd['bdwidth'].value() * bd['bdheight'].value())
            color = smallest['tile_color'].value()
            if color != 0:
                return color

    # --- 2. Attached input node color (with Preferences fallback) ---
    if input_node is not None:
        return find_node_color(input_node)

    # --- 3. Default anchor color ---
    return ANCHOR_DEFAULT_COLOR


def get_link_class_for_source(source_node):
    """Return the appropriate link node class for a given source node.
    Dot → Dot, LINK_CLASSES lookup, else PostageStamp."""
    if source_node is None:
        return 'PostageStamp'
    if source_node.Class() == 'Dot':
        return 'Dot'
    return LINK_CLASSES.get(source_node.Class(), 'PostageStamp')


def add_input_knob(node):

    if not is_anchor(node):
        add_link_reconnect_knob(node)

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


def add_link_reconnect_knob(node):
    if LINK_RECONNECT_KNOB_NAME in node.knobs():
        return
    knob = nuke.PyScript_Knob(LINK_RECONNECT_KNOB_NAME, "Reconnect", 
        """import paste_hidden
paste_hidden.reconnect_link_node(nuke.thisNode())""")
    node.addKnob(knob)


def get_fully_qualified_node_name(node):
    """We need the script name as part of the full name of the node,
    to avoid attempting to make a PostageStamp etc. in another script"""

    return f"{nuke.root().name().split('.')[0]}.{node.fullName()}"


# ---------------------------------------------------------------------------
# Anchor functionality
# ---------------------------------------------------------------------------

def is_anchor(node):
    try:
        if node.name().startswith(ANCHOR_PREFIX):
            return True
        if node.Class() == 'Dot' and node['label'].getValue().strip():
            return True
        return False
    except Exception:
        return False


def is_link(node):
    if KNOB_NAME in node.knobs():
        return True
    else:
        return False


def add_reconnect_anchor_knob(node):
    if ANCHOR_RECONNECT_KNOB_NAME in node.knobs():
        return
    knob = nuke.PyScript_Knob(LINK_RECONNECT_KNOB_NAME, "Reconnect Child Links", 
        """import paste_hidden
paste_hidden.reconnect_anchor_node(nuke.thisNode())""")
    node.addKnob(knob)


def reconnect_anchor_node(anchor_node):
    for node in [
            node for node in
            nuke.allNodes()
            if is_link(node)
            #and anchor_node.name() in node[KNOB_NAME].getText()
        ]:
        reconnect_link_node(node)


def reconnect_all_links():
    for node in [node for node in nuke.allNodes() if is_link(node)]:
        reconnect_link_node(node)


def anchor_display_name(node):
    if node.Class() == 'Dot':
        return node['label'].getValue().strip()
    return node.name()[len(ANCHOR_PREFIX):]


def all_anchors():
    anchors = [n for n in nuke.allNodes() if is_anchor(n)]
    anchors.sort(key=lambda n: anchor_display_name(n).lower())
    return anchors


def suggest_anchor_name(input_node):
    """Return a suggested anchor name based on the input node's file knob and backdrop context."""
    suggestion = ""

    if 'file' in input_node.knobs():
        filepath = input_node['file'].getValue()
        if filepath:
            filename = os.path.basename(filepath)
            m = re.match(r'^(.+)_v\d+(?:\.[^.]+)?\.[^.]+$', filename)
            if m:
                suggestion = m.group(1)
            else:
                suggestion = os.path.splitext(filename)[0]

    ax, ay = input_node.xpos(), input_node.ypos()
    containing = []
    for bd in nuke.allNodes('BackdropNode'):
        bx = bd.xpos()
        by = bd.ypos()
        bw = bd['bdwidth'].value()
        bh = bd['bdheight'].value()
        if bx <= ax < bx + bw and by <= ay < by + bh:
            containing.append(bd)

    if containing:
        smallest = min(containing, key=lambda bd: bd['bdwidth'].value() * bd['bdheight'].value())
        label = smallest['label'].getValue().strip()
        if label:
            suggestion = label + '_' + suggestion

    return suggestion


def create_anchor():
    selected = nuke.selectedNodes()
    input_node = selected[0] if len(selected) == 1 else None

    suggested = suggest_anchor_name(input_node) if input_node is not None else ""
    name = nuke.getInput("Anchor name:", suggested)
    if not name or not name.strip():
        return

    sanitized = re.sub(r'[^A-Za-z0-9_]', '_', name.strip())
    if not sanitized:
        return

    nukescripts.clear_selection_recursive()
    anchor = nuke.createNode('NoOp')
    anchor.setName(ANCHOR_PREFIX + sanitized)
    anchor['label'].setValue(anchor_display_name(anchor))

    if input_node is not None:
        anchor.setInput(0, input_node)
        anchor.setXYpos(
            input_node.xpos() + input_node.screenWidth() // 2 - anchor.screenWidth() // 2,
            input_node.ypos() + input_node.screenHeight() + 20
        )

    anchor['tile_color'].setValue(find_anchor_color(anchor))
    add_reconnect_anchor_knob(anchor)


def create_from_anchor(anchor_node):
    nukescripts.clear_selection_recursive()
    source = anchor_node if anchor_node.Class() == 'Dot' else anchor_node.input(0)
    link_class = get_link_class_for_source(source)
    link = nuke.createNode(link_class)
    setup_link_node(anchor_node, link)
    return link


class AnchorPlugin(_tabtabtab.TabTabTabPlugin):
    """tabtabtab plugin that lists all anchor nodes for link creation."""

    def get_items(self):
        return [
            {
                'menuobj': anchor,
                'menupath': 'Anchors/' + anchor_display_name(anchor),
            }
            for anchor in all_anchors()
        ]

    def get_weights_file(self):
        return os.path.expanduser('~/.nuke/paste_hidden_anchor_weights.json')

    def invoke(self, thing):
        anchor = thing['menuobj']
        if nuke.exists(anchor.name()):
            create_from_anchor(anchor)

    def get_icon(self, menuobj):
        return None

    def get_color(self, menuobj):
        color_int = find_anchor_color(menuobj)  # 0xRRGGBBAA
        r = (color_int >> 24) & 0xFF
        g = (color_int >> 16) & 0xFF
        b = (color_int >> 8) & 0xFF
        return QtGui.QColor(r, g, b)


def anchor_shortcut():
    """If a node is selected, create an anchor from it. Otherwise, pick an anchor to create from."""
    if nuke.selectedNodes():
        create_anchor()
    else:
        select_anchor_and_create()


_anchor_picker_widget = None


def select_anchor_and_create():
    if QtWidgets is None:
        return
    if not all_anchors():
        return
    global _anchor_picker_widget
    if _anchor_picker_widget is not None:
        try:
            _anchor_picker_widget.under_cursor()
            _anchor_picker_widget.show()
            _anchor_picker_widget.raise_()
            return
        except RuntimeError:
            _anchor_picker_widget = None
    _anchor_picker_widget = _tabtabtab.TabTabTabWidget(
        AnchorPlugin(), winflags=Qt.FramelessWindowHint
    )
    _anchor_picker_widget.under_cursor()
    _anchor_picker_widget.show()
    _anchor_picker_widget.raise_()
