"""Shared constants for the paste_hidden package."""

import os

TAB_NAME = 'copy_hidden_tab'
KNOB_NAME = 'copy_hidden_input_node'
LINK_RECONNECT_KNOB_NAME = "reconnect_link"
HIDDEN_INPUT_CLASSES = ['PostageStamp', 'Dot', 'NoOp']
LINK_SOURCE_CLASSES = frozenset({
    "Read", "DeepRead", "ReadGeo",
    "Camera", "Camera2", "Camera3", "Camera4",
    "GeoImport",
})

ANCHOR_PREFIX = 'Anchor_'
ANCHOR_RECONNECT_KNOB_NAME = "reconnect_child_links"
ANCHOR_RENAME_KNOB_NAME = "rename_anchor"
ANCHOR_DEFAULT_COLOR = 0x6f3399ff

DOT_LABEL_FONT_SIZE_LARGE = 111
DOT_LABEL_FONT_SIZE_MEDIUM = 66
NODE_LABEL_FONT_SIZE_LARGE = 33
DOT_LINK_LABEL_FONT_SIZE = 33

DOT_ANCHOR_KNOB_NAME = 'paste_hidden_dot_anchor'

DOT_TYPE_KNOB_NAME = 'paste_hidden_dot_type'
LOCAL_DOT_COLOR = 0x7A3A00FF  # darkened burnt orange: R=122,G=58,B=0 (~30% darker than previous 0xB35A00FF)

ANCHOR_SET_COLOR_KNOB_NAME = "set_anchor_color"
USER_PALETTE_PATH = os.path.expanduser('~/.nuke/paste_hidden_user_palette.json')
PREFS_PATH = os.path.expanduser('~/.nuke/paste_hidden_prefs.json')
