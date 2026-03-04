"""Shared constants for the paste_hidden package."""

TAB_NAME = 'copy_hidden_tab'
KNOB_NAME = 'copy_hidden_input_node'
LINK_RECONNECT_KNOB_NAME = "reconnect_link"
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

ANCHOR_PREFIX = 'Anchor_'
ANCHOR_RECONNECT_KNOB_NAME = "reconnect_child_links"
ANCHOR_RENAME_KNOB_NAME = "rename_anchor"
ANCHOR_DEFAULT_COLOR = 0x6f3399ff

DOT_LABEL_FONT_SIZE_LARGE = 111
DOT_LABEL_FONT_SIZE_MEDIUM = 66
NODE_LABEL_FONT_SIZE_LARGE = 33
DOT_LINK_LABEL_FONT_SIZE = 33

DOT_ANCHOR_KNOB_NAME = 'paste_hidden_dot_anchor'

ANCHOR_LINK_CLASS_KNOB_NAME = 'paste_hidden_anchor_link_class'
