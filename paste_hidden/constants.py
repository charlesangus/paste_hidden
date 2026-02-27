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
