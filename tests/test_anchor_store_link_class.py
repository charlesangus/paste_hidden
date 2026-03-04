"""Tests for _store_link_class_on_anchor() in anchor.py.

These tests verify that when input_node is None, the function probes via
anchor_node.input(0) rather than silently defaulting to 'NoOp'.

TDD: RED phase — tests written before implementation.
"""
import sys
import types
import importlib.util
import os
import unittest


# ---------------------------------------------------------------------------
# Reuse the nuke stub scaffolding from test_link_probe if already loaded,
# otherwise build enough infrastructure to load anchor.py.
# ---------------------------------------------------------------------------

class _StubKnob:
    def __init__(self, val=None):
        self._val = val if val is not None else ""

    def value(self):
        return self._val

    def getValue(self):
        return self._val

    def setValue(self, val):
        self._val = val

    def getText(self):
        return str(self._val)

    def setVisible(self, visible):
        pass


class _StubNode:
    def __init__(self, node_class="NoOp", name="Node1"):
        self._class = node_class
        self._name = name
        self._knobs = {}
        self._inputs = {}
        self._can_set_input_results = {}

    def Class(self):
        return self._class

    def name(self):
        return self._name

    def fullName(self):
        return self._name

    def knobs(self):
        return self._knobs

    def __getitem__(self, knob_name):
        if knob_name not in self._knobs:
            self._knobs[knob_name] = _StubKnob()
        return self._knobs[knob_name]

    def __contains__(self, knob_name):
        return knob_name in self._knobs

    def addKnob(self, knob):
        if hasattr(knob, "_name"):
            self._knobs[knob._name] = knob

    def input(self, index):
        return self._inputs.get(index)

    def setInput(self, index, node):
        self._inputs[index] = node

    def canSetInput(self, input_index, candidate_node):
        slot_map = self._can_set_input_results.get(input_index, {})
        return slot_map.get(candidate_node.Class(), False)

    def xpos(self):
        return 0

    def ypos(self):
        return 0

    def screenWidth(self):
        return 80

    def screenHeight(self):
        return 28

    NUKE_VERSION_MAJOR = 13


def _install_stubs():
    """Install or refresh minimal nuke/nukescripts stubs."""
    if "nuke" in sys.modules:
        nuke_module = sys.modules["nuke"]
    else:
        nuke_module = types.ModuleType("nuke")
        sys.modules["nuke"] = nuke_module

    # Track created/deleted scratch nodes
    created_nodes = []
    deleted_nodes = []

    def _create_node(node_class, **kwargs):
        node = _StubNode(node_class=node_class, name=node_class + "_scratch")
        created_nodes.append(node)
        return node

    def _delete(node):
        deleted_nodes.append(node)

    nuke_module._created_nodes = created_nodes
    nuke_module._deleted_nodes = deleted_nodes
    nuke_module.createNode = _create_node
    nuke_module.delete = _delete
    nuke_module.INVISIBLE = 0
    nuke_module.NUKE_VERSION_MAJOR = 13

    def _make_string_knob(name, label=""):
        knob = _StubKnob()
        knob._name = name
        return knob

    def _make_bool_knob(name, label=""):
        knob = _StubKnob(val=False)
        knob._name = name
        return knob

    def _make_pyscript_knob(name, label="", script=""):
        knob = _StubKnob()
        knob._name = name
        return knob

    def _make_tab_knob(name, label=""):
        knob = _StubKnob()
        knob._name = name
        return knob

    nuke_module.String_Knob = _make_string_knob
    nuke_module.Boolean_Knob = _make_bool_knob
    nuke_module.PyScript_Knob = _make_pyscript_knob
    nuke_module.Tab_Knob = _make_tab_knob

    class _Root:
        def name(self):
            return "test_script.nk"

    nuke_module.root = lambda: _Root()
    nuke_module.toNode = lambda name: None
    nuke_module.allNodes = lambda node_class=None: []
    nuke_module.selectedNodes = lambda: []
    nuke_module.getInput = lambda *args: None
    nuke_module.exists = lambda name: False

    if "nukescripts" not in sys.modules:
        nukescripts_stub = types.ModuleType("nukescripts")
        nukescripts_stub.clear_selection_recursive = lambda: None
        sys.modules["nukescripts"] = nukescripts_stub

    return nuke_module


def _load_constants():
    module_path = os.path.join(os.path.dirname(__file__), "..", "constants.py")
    spec = importlib.util.spec_from_file_location("constants_for_anchor_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["constants"] = module
    return module


def _load_link():
    module_path = os.path.join(os.path.dirname(__file__), "..", "link.py")
    spec = importlib.util.spec_from_file_location("link_for_anchor_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["link"] = module
    return module


# Install stubs and load modules
_nuke = _install_stubs()
_constants = _load_constants()
_link = _load_link()

# Stub out tabtabtab before loading anchor.py
if "tabtabtab" not in sys.modules:
    tabtabtab_stub = types.ModuleType("tabtabtab")

    class _FakePlugin:
        pass

    class _FakeWidget:
        def __init__(self, *args, **kwargs):
            pass

    tabtabtab_stub.TabTabTabPlugin = _FakePlugin
    tabtabtab_stub.TabTabTabWidget = _FakeWidget
    sys.modules["tabtabtab"] = tabtabtab_stub

# Stub out labels before loading anchor.py
if "labels" not in sys.modules:
    labels_stub = types.ModuleType("labels")
    labels_stub._apply_label = lambda *args, **kwargs: None
    sys.modules["labels"] = labels_stub

# Stub out util before loading anchor.py
if "util" not in sys.modules:
    util_stub = types.ModuleType("util")
    util_stub.upstream_ignoring_hidden = lambda node: set()
    sys.modules["util"] = util_stub

# Stub out PySide2/PySide6 before loading anchor.py
for qt_module in ["PySide2", "PySide2.QtGui", "PySide2.QtWidgets", "PySide2.QtCore",
                   "PySide6", "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"]:
    if qt_module not in sys.modules:
        stub = types.ModuleType(qt_module)
        sys.modules[qt_module] = stub

# Now load anchor.py
_anchor_path = os.path.join(os.path.dirname(__file__), "..", "anchor.py")
_anchor_spec = importlib.util.spec_from_file_location("anchor_under_test", _anchor_path)
_anchor = importlib.util.module_from_spec(_anchor_spec)
_anchor_spec.loader.exec_module(_anchor)


# ---------------------------------------------------------------------------
# Tests for _store_link_class_on_anchor()
# ---------------------------------------------------------------------------

class TestStoreLinkClassOnAnchorWithExplicitInputNode(unittest.TestCase):
    """When input_node is provided explicitly, behavior is unchanged."""

    def _make_anchor(self):
        anchor = _StubNode(node_class="NoOp", name="Anchor_test")
        return anchor

    def test_explicit_2d_input_stores_postage_stamp(self):
        """Explicit Read input_node stores 'PostageStamp'."""
        anchor = self._make_anchor()
        read_node = _StubNode(node_class="Read", name="Read1")
        _anchor._store_link_class_on_anchor(anchor, read_node)
        stored = anchor[_constants.ANCHOR_LINK_CLASS_KNOB_NAME].getValue()
        self.assertEqual(stored, "PostageStamp")

    def test_explicit_3d_input_stores_noop(self):
        """Explicit Camera input_node stores 'NoOp'."""
        anchor = self._make_anchor()
        camera_node = _StubNode(node_class="Camera", name="Camera1")
        _anchor._store_link_class_on_anchor(anchor, camera_node)
        stored = anchor[_constants.ANCHOR_LINK_CLASS_KNOB_NAME].getValue()
        self.assertEqual(stored, "NoOp")

    def test_explicit_none_input_stores_noop(self):
        """Explicit None input_node stores 'NoOp' (safe fallback, no input to probe)."""
        anchor = self._make_anchor()
        # anchor has no input(0) either
        _anchor._store_link_class_on_anchor(anchor, None)
        stored = anchor[_constants.ANCHOR_LINK_CLASS_KNOB_NAME].getValue()
        self.assertEqual(stored, "NoOp")


class TestStoreLinkClassOnAnchorWithNoneAndConnectedInput(unittest.TestCase):
    """When input_node is None but anchor.input(0) exists, probe runs via that node."""

    def _make_anchor_with_input(self, input_node_class):
        """Create an anchor whose input(0) is a node of given class."""
        anchor = _StubNode(node_class="NoOp", name="Anchor_probed")
        connected_node = _StubNode(node_class=input_node_class, name="ConnectedNode1")
        anchor._inputs[0] = connected_node
        return anchor, connected_node

    def test_none_input_node_with_2d_anchor_input_stores_postage_stamp(self):
        """input_node=None but anchor.input(0) is a Read node -> stores 'PostageStamp'."""
        anchor, _connected = self._make_anchor_with_input("Read")
        # Call with no explicit input_node (None)
        _anchor._store_link_class_on_anchor(anchor, None)
        stored = anchor[_constants.ANCHOR_LINK_CLASS_KNOB_NAME].getValue()
        self.assertEqual(stored, "PostageStamp",
            "When input_node is None, should probe anchor.input(0) and classify Read as PostageStamp")

    def test_none_input_node_with_3d_anchor_input_stores_noop(self):
        """input_node=None but anchor.input(0) is a Camera node -> stores 'NoOp'."""
        anchor, _connected = self._make_anchor_with_input("Camera")
        _anchor._store_link_class_on_anchor(anchor, None)
        stored = anchor[_constants.ANCHOR_LINK_CLASS_KNOB_NAME].getValue()
        self.assertEqual(stored, "NoOp",
            "When input_node is None, should probe anchor.input(0) and classify Camera as NoOp")

    def test_none_input_node_no_anchor_input_stores_noop(self):
        """input_node=None and anchor.input(0) is also None -> stores 'NoOp'."""
        anchor = _StubNode(node_class="NoOp", name="Anchor_disconnected")
        # No inputs connected to anchor
        _anchor._store_link_class_on_anchor(anchor, None)
        stored = anchor[_constants.ANCHOR_LINK_CLASS_KNOB_NAME].getValue()
        self.assertEqual(stored, "NoOp",
            "When both input_node and anchor.input(0) are None, should store 'NoOp'")

    def test_explicit_input_takes_priority_over_anchor_input(self):
        """When explicit input_node is given, anchor.input(0) is NOT consulted."""
        anchor = _StubNode(node_class="NoOp", name="Anchor_priority")
        # anchor.input(0) is a Camera (would give NoOp)
        camera_node = _StubNode(node_class="Camera", name="Camera1")
        anchor._inputs[0] = camera_node

        # But explicit input_node is a Read (should give PostageStamp)
        read_node = _StubNode(node_class="Read", name="Read1")
        _anchor._store_link_class_on_anchor(anchor, read_node)

        stored = anchor[_constants.ANCHOR_LINK_CLASS_KNOB_NAME].getValue()
        self.assertEqual(stored, "PostageStamp",
            "Explicit input_node should take priority over anchor.input(0)")

    def test_knob_created_if_absent(self):
        """The hidden knob is created when it does not yet exist on the anchor."""
        anchor = _StubNode(node_class="NoOp", name="Anchor_fresh")
        read_node = _StubNode(node_class="Read", name="Read1")
        # Ensure knob is not present initially
        self.assertNotIn(_constants.ANCHOR_LINK_CLASS_KNOB_NAME, anchor.knobs())

        _anchor._store_link_class_on_anchor(anchor, read_node)

        # After the call, knob should exist with correct value
        self.assertIn(_constants.ANCHOR_LINK_CLASS_KNOB_NAME, anchor.knobs())
        stored = anchor[_constants.ANCHOR_LINK_CLASS_KNOB_NAME].getValue()
        self.assertEqual(stored, "PostageStamp")


if __name__ == "__main__":
    unittest.main()
