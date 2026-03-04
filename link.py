"""Shared predicates and link-node utilities.

Neither anchor.py nor paste_hidden.py need to import from each other;
both pull what they need from here and from constants.py.
"""

import nuke
import nukescripts

from constants import (
    TAB_NAME, KNOB_NAME, LINK_RECONNECT_KNOB_NAME,
    HIDDEN_INPUT_CLASSES, LINK_CLASSES, ANCHOR_PREFIX,
    DOT_ANCHOR_KNOB_NAME, DOT_LINK_LABEL_FONT_SIZE,
    ANCHOR_LINK_CLASS_KNOB_NAME,
)


def get_fully_qualified_node_name(node):
    """Return <script_stem>.<node.fullName()> so we can detect cross-script refs."""
    return f"{nuke.root().name().split('.')[0]}.{node.fullName()}"


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


def find_smallest_containing_backdrop(node):
    """Return the smallest BackdropNode that fully contains *node*, or None."""
    nx, ny = node.xpos(), node.ypos()
    containing = []
    for bd in nuke.allNodes('BackdropNode'):
        bx = bd.xpos()
        by = bd.ypos()
        bw = bd['bdwidth'].value()
        bh = bd['bdheight'].value()
        if bx <= nx < bx + bw and by <= ny < by + bh:
            containing.append(bd)
    if not containing:
        return None
    return min(containing, key=lambda bd: bd['bdwidth'].value() * bd['bdheight'].value())


_2D_CHANNEL_PREFIXES = ('rgba', 'depth', 'forward')


def detect_link_class_for_node(source_node):
    """Detect the correct link node class for a given source node.

    Uses Nuke API channel inspection for unknown node classes so that the
    detection result is accurate rather than a static dict lookup.

    Returns 'Dot' for Dot nodes, a value from LINK_CLASSES for known
    file-node classes, 'PostageStamp' when 2D channels are detected, and
    'NoOp' in all other cases (including None input and Nuke API errors).
    This implements LINK-04: fall back to NoOp when detection is inconclusive.
    """
    if source_node is None:
        return 'NoOp'
    node_class = source_node.Class()
    if node_class == 'Dot':
        return 'Dot'
    if node_class in LINK_CLASSES:
        return LINK_CLASSES[node_class]
    try:
        channels = source_node.channels()
        if not channels:
            return 'NoOp'
        for channel_name in channels:
            if channel_name.startswith(_2D_CHANNEL_PREFIXES):
                return 'PostageStamp'
        return 'NoOp'
    except Exception:
        return 'NoOp'


def get_link_class_for_anchor(anchor_node):
    """Read the stored link class from an anchor node's hidden knob.

    Returns the stored class string, or 'NoOp' if the knob is absent.
    """
    if ANCHOR_LINK_CLASS_KNOB_NAME in anchor_node.knobs():
        return anchor_node[ANCHOR_LINK_CLASS_KNOB_NAME].getValue()
    return 'NoOp'


def get_link_class_for_source(source_node):
    """Return the appropriate link node class for a given source node.

    Dispatch order:
      1. Anchor node → read stored class from hidden knob (avoids re-detection).
      2. Dot node → 'Dot'.
      3. Known file-node class in LINK_CLASSES → direct lookup.
      4. Else → 'PostageStamp' (direct-file-node paste path fallback).
    """
    if source_node is not None and is_anchor(source_node):
        return get_link_class_for_anchor(source_node)
    if source_node is None:
        return 'PostageStamp'
    if source_node.Class() == 'Dot':
        return 'Dot'
    return LINK_CLASSES.get(source_node.Class(), 'PostageStamp')


def mark_dot_as_anchor(dot_node):
    """Add the canonical anchor marker knob to a Dot node if not already present."""
    if DOT_ANCHOR_KNOB_NAME in dot_node.knobs():
        dot_node[DOT_ANCHOR_KNOB_NAME].setValue(True)
        return
    knob = nuke.Boolean_Knob(DOT_ANCHOR_KNOB_NAME, 'Dot Anchor')
    knob.setVisible(False)
    knob.setValue(True)
    dot_node.addKnob(knob)


def is_anchor(node):
    try:
        if node.name().startswith(ANCHOR_PREFIX):
            return True
        if node.Class() == 'Dot':
            # Explicit anchor knob (set by mark_dot_as_anchor)
            if DOT_ANCHOR_KNOB_NAME in node.knobs():
                return True
            # Legacy: labelled dot that is not a link, not hidden-input, no "Link: " prefix
            label = node['label'].getValue().strip()
            if label and not label.startswith('Link: ') and not is_link(node) and not node['hide_input'].getValue():
                return True
        return False
    except Exception:
        return False


def is_link(node):
    return KNOB_NAME in node.knobs()


def add_link_reconnect_knob(node):
    if LINK_RECONNECT_KNOB_NAME in node.knobs():
        return
    knob = nuke.PyScript_Knob(LINK_RECONNECT_KNOB_NAME, "Reconnect",
        """import link
link.reconnect_link_node(nuke.thisNode())""")
    node.addKnob(knob)


def add_input_knob(node):
    if not is_anchor(node):
        add_link_reconnect_knob(node)

    # remove our custom knobs to make sure they're at the end
    try:
        node.removeKnob(node[KNOB_NAME])
    except Exception:
        pass
    try:
        node.removeKnob(node[TAB_NAME])
    except Exception:
        pass

    tab = nuke.Tab_Knob(TAB_NAME)
    tab.setFlag(nuke.INVISIBLE)
    tab.setVisible(False)
    node.addKnob(tab)

    k = nuke.String_Knob(KNOB_NAME)
    k.setVisible(False)
    node.addKnob(k)


def setup_link_node(input_node, link_node):
    link_node["hide_input"].setValue(True)
    link_node["tile_color"].setValue(find_node_color(input_node))

    if input_node["label"].getText():
        link_node["label"].setValue(f"Link: {input_node['label'].getText()}")
    else:
        link_node["label"].setValue(f"Link: {input_node.name()}")

    if link_node.Class() == 'Dot':
        link_node["note_font_size"].setValue(DOT_LINK_LABEL_FONT_SIZE)

    add_input_knob(link_node)
    link_node[KNOB_NAME].setValue(get_fully_qualified_node_name(input_node))
    link_node.setInput(0, input_node)


def find_anchor_node(link_node):
    fully_qualified_name_from_knob = link_node[KNOB_NAME].getText()
    fqn_from_knob_split = fully_qualified_name_from_knob.split(".")

    # strip off the script name to get Nuke's version of a full name
    full_name_from_knob = ".".join(fqn_from_knob_split[1:])
    fully_qualified_name_from_current = get_fully_qualified_node_name(link_node)
    fqn_from_current_split = fully_qualified_name_from_current.split(".")
    prefix_from_knob = fqn_from_knob_split[:-1]
    prefix_from_current = fqn_from_current_split[:-1]
    if prefix_from_knob != prefix_from_current:
        # we are in a different script and/or Group, do nothing
        return None
    anchor_node = nuke.toNode(full_name_from_knob)
    return anchor_node


def reconnect_link_node(link_node):
    anchor_node = find_anchor_node(link_node)
    if not anchor_node:
        return None
    link_node.setInput(0, anchor_node)
