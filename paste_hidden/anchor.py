"""Anchor system: creation, renaming, reconnection, and the tabtabtab picker."""

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

from link import (
    ANCHOR_PREFIX, KNOB_NAME,
    is_anchor, is_link,
    get_fully_qualified_node_name,
    add_input_knob,
    reconnect_link_node,
    find_node_color,
    find_smallest_containing_backdrop,
    get_link_class_for_source,
    setup_link_node,
)

ANCHOR_RECONNECT_KNOB_NAME = "reconnect_child_links"
ANCHOR_RENAME_KNOB_NAME = "rename_anchor"


def sanitize_anchor_name(name):
    return re.sub(r'[^A-Za-z0-9_]', '_', name.strip())


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
        smallest = find_smallest_containing_backdrop(anchor)
        if smallest is not None:
            color = smallest['tile_color'].value()
            if color != 0:
                return color

    # --- 2. Attached input node color (with Preferences fallback) ---
    if input_node is not None:
        return find_node_color(input_node)

    # --- 3. Default anchor color ---
    return ANCHOR_DEFAULT_COLOR


def add_reconnect_anchor_knob(node):
    if ANCHOR_RECONNECT_KNOB_NAME in node.knobs():
        return
    # Bug fix: use ANCHOR_RECONNECT_KNOB_NAME (not LINK_RECONNECT_KNOB_NAME) so
    # the guard above actually fires on subsequent calls.
    knob = nuke.PyScript_Knob(ANCHOR_RECONNECT_KNOB_NAME, "Reconnect Child Links",
        """import anchor
anchor.reconnect_anchor_node(nuke.thisNode())""")
    node.addKnob(knob)


def add_rename_anchor_knob(node):
    if ANCHOR_RENAME_KNOB_NAME in node.knobs():
        return
    knob = nuke.PyScript_Knob(ANCHOR_RENAME_KNOB_NAME, "Rename",
        """import anchor
anchor.rename_anchor(nuke.thisNode())""")
    node.addKnob(knob)


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

    smallest = find_smallest_containing_backdrop(input_node)
    if smallest is not None:
        label = smallest['label'].getValue().strip()
        if label:
            suggestion = label + '_' + suggestion

    return suggestion


def rename_anchor(anchor_node):
    """Rename an anchor and update all link nodes that reference it."""
    input_node = anchor_node.input(0)
    suggested = suggest_anchor_name(input_node) if input_node is not None else anchor_display_name(anchor_node)
    name = nuke.getInput("Rename anchor:", suggested)
    if not name or not name.strip():
        return

    sanitized = sanitize_anchor_name(name)
    if not sanitized:
        return

    old_fqn = get_fully_qualified_node_name(anchor_node)
    anchor_node.setName(ANCHOR_PREFIX + sanitized)
    anchor_node['label'].setValue(anchor_display_name(anchor_node))
    new_fqn = get_fully_qualified_node_name(anchor_node)

    new_label = anchor_node['label'].getText() or anchor_node.name()
    for node in nuke.allNodes():
        if is_link(node) and node[KNOB_NAME].getText() == old_fqn:
            node[KNOB_NAME].setValue(new_fqn)
            node['label'].setValue(f"Link: {new_label}")


def rename_selected_anchor():
    selected = nuke.selectedNodes()
    if len(selected) == 1 and is_anchor(selected[0]):
        rename_anchor(selected[0])


def reconnect_anchor_node(anchor_node):
    # Bug fix: filter by exact FQNN match so only this anchor's links reconnect,
    # not all links in the script (the old substring check was commented out).
    fqnn = get_fully_qualified_node_name(anchor_node)
    for node in nuke.allNodes():
        if is_link(node) and node[KNOB_NAME].getText() == fqnn:
            reconnect_link_node(node)


def reconnect_all_links():
    for node in nuke.allNodes():
        if is_link(node):
            reconnect_link_node(node)


def create_anchor():
    selected = nuke.selectedNodes()
    input_node = selected[0] if len(selected) == 1 else None

    suggested = suggest_anchor_name(input_node) if input_node is not None else ""
    name = nuke.getInput("Anchor name:", suggested)
    if not name or not name.strip():
        return

    sanitized = sanitize_anchor_name(name)
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
    add_rename_anchor_knob(anchor)


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
    selected = nuke.selectedNodes()
    if len(selected) == 1 and is_anchor(selected[0]):
        rename_anchor(selected[0])
    elif selected:
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
