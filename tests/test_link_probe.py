"""Tests for probe_stream_type_via_can_set_input() and detect_link_class_for_node()
in link.py.

These tests verify the canSetInput probe replaces the old channel-prefix
heuristic for unknown node classes, while preserving all fast-path behavior.

TDD: RED phase — tests written before implementation.
"""
import sys
import types
import importlib.util
import os
import unittest


# ---------------------------------------------------------------------------
# Stub nuke module so link.py can be imported without a Nuke runtime.
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


class _StubNode:
    def __init__(self, node_class="NoOp", name="Node1"):
        self._class = node_class
        self._name = name
        self._knobs = {}
        self._inputs = {}
        self._can_set_input_results = {}  # {input_index: {node_class: bool}}

    def Class(self):
        return self._class

    def name(self):
        return self._name

    def fullName(self):
        return self._name

    def knobs(self):
        return self._knobs

    def __getitem__(self, knob_name):
        return self._knobs.get(knob_name, _StubKnob())

    def __contains__(self, knob_name):
        return knob_name in self._knobs

    def addKnob(self, knob):
        pass

    def input(self, index):
        return self._inputs.get(index)

    def setInput(self, index, node):
        self._inputs[index] = node

    def canSetInput(self, input_index, candidate_node):
        """Simulate canSetInput based on per-class configuration."""
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


class _StubNukeModule:
    """Minimal nuke stub for link.py."""

    def __init__(self):
        self._created_nodes = []
        self._deleted_nodes = []
        self._root_name = "test_script.nk"

    def createNode(self, node_class, **kwargs):
        node = _StubNode(node_class=node_class, name=node_class + "_scratch")
        self._created_nodes.append(node)
        return node

    def delete(self, node):
        self._deleted_nodes.append(node)

    def root(self):
        class _Root:
            def name(self):
                return "test_script.nk"
        return _Root()

    def toNode(self, name):
        return None

    def allNodes(self, node_class=None):
        return []

    def selectedNodes(self):
        return []

    def Boolean_Knob(self, name, label=""):
        knob = _StubKnob()
        knob._name = name
        return knob

    def String_Knob(self, name, label=""):
        knob = _StubKnob()
        knob._name = name
        return knob

    def Tab_Knob(self, name, label=""):
        knob = _StubKnob()
        knob._name = name
        return knob

    def PyScript_Knob(self, name, label="", script=""):
        knob = _StubKnob()
        knob._name = name
        return knob

    INVISIBLE = 0

    def getInput(self, *args):
        return None


def _install_nuke_stub():
    """Install the stub nuke module and return it."""
    stub = _StubNukeModule()
    stub_module = types.ModuleType("nuke")
    # Copy all attributes from stub instance onto module
    for attr_name in dir(stub):
        if not attr_name.startswith("__"):
            setattr(stub_module, attr_name, getattr(stub, attr_name))
    stub_module._stub = stub  # keep reference for test introspection
    sys.modules["nuke"] = stub_module
    return stub_module


def _install_nukescripts_stub():
    nukescripts_stub = types.ModuleType("nukescripts")
    nukescripts_stub.clear_selection_recursive = lambda: None
    sys.modules["nukescripts"] = nukescripts_stub


def _load_link_module():
    """Load link.py fresh, bypassing any cached version."""
    module_path = os.path.join(os.path.dirname(__file__), "..", "link.py")
    spec = importlib.util.spec_from_file_location("link_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_constants_module():
    """Load constants.py fresh."""
    module_path = os.path.join(os.path.dirname(__file__), "..", "constants.py")
    spec = importlib.util.spec_from_file_location("constants_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Module setup — install stubs before importing link.py
# ---------------------------------------------------------------------------

_install_nuke_stub()
_install_nukescripts_stub()

# Load constants first so link.py can import it
_constants = _load_constants_module()
sys.modules["constants"] = _constants

# Load link module under test
_link = _load_link_module()


# ---------------------------------------------------------------------------
# Tests for probe_stream_type_via_can_set_input()
# ---------------------------------------------------------------------------

class TestProbeStreamTypeViaCanSetInput(unittest.TestCase):
    """Verify the canSetInput probe function maps stream types correctly."""

    def setUp(self):
        # Reset created/deleted node tracking
        nuke_stub = sys.modules["nuke"]
        nuke_stub._stub._created_nodes.clear()
        nuke_stub._stub._deleted_nodes.clear()

    def _make_node_accepting_class(self, accepted_class):
        """Return a stub node that canSetInput returns True only for accepted_class."""
        node = _StubNode()
        node._can_set_input_results[0] = {accepted_class: True}
        return node

    def test_2d_node_returns_postage_stamp(self):
        """Node that accepts NoOp (2D scratch) returns 'PostageStamp'."""
        node = self._make_node_accepting_class("NoOp")
        result = _link.probe_stream_type_via_can_set_input(node)
        self.assertEqual(result, "PostageStamp")

    def test_3d_node_returns_noop(self):
        """Node that accepts Scene (3D scratch) returns 'NoOp'."""
        node = self._make_node_accepting_class("Scene")
        result = _link.probe_stream_type_via_can_set_input(node)
        self.assertEqual(result, "NoOp")

    def test_deep_node_returns_noop(self):
        """Node that accepts DeepMerge (Deep scratch) returns 'NoOp'."""
        node = self._make_node_accepting_class("DeepMerge")
        result = _link.probe_stream_type_via_can_set_input(node)
        self.assertEqual(result, "NoOp")

    def test_no_match_returns_noop(self):
        """Node that accepts no scratch node class returns 'NoOp'."""
        node = _StubNode()  # canSetInput always returns False
        result = _link.probe_stream_type_via_can_set_input(node)
        self.assertEqual(result, "NoOp")

    def test_scratch_nodes_are_deleted_after_probe(self):
        """All three scratch nodes created during probe are deleted regardless of result."""
        node = self._make_node_accepting_class("NoOp")
        nuke_stub = sys.modules["nuke"]

        _link.probe_stream_type_via_can_set_input(node)

        # Three scratch nodes should have been created (NoOp, Scene, DeepMerge)
        created_classes = [n.Class() for n in nuke_stub._stub._created_nodes]
        self.assertIn("NoOp", created_classes)
        self.assertIn("Scene", created_classes)
        self.assertIn("DeepMerge", created_classes)

        # All three should also be deleted
        deleted_nodes = nuke_stub._stub._deleted_nodes
        self.assertEqual(len(deleted_nodes), 3,
            f"Expected 3 nodes deleted, got {len(deleted_nodes)}: {[n.Class() for n in deleted_nodes]}")

    def test_scratch_nodes_deleted_even_when_no_match(self):
        """Scratch nodes are deleted even when no probe returns True."""
        node = _StubNode()  # no canSetInput match
        nuke_stub = sys.modules["nuke"]
        nuke_stub._stub._created_nodes.clear()
        nuke_stub._stub._deleted_nodes.clear()

        _link.probe_stream_type_via_can_set_input(node)

        self.assertEqual(len(nuke_stub._stub._deleted_nodes), 3)

    def test_exception_in_probe_returns_noop(self):
        """If canSetInput raises an exception, probe returns 'NoOp'."""
        class _ExplodingNode:
            def Class(self):
                return "Unknown"
            def canSetInput(self, index, candidate):
                raise RuntimeError("Nuke API unavailable")

        result = _link.probe_stream_type_via_can_set_input(_ExplodingNode())
        self.assertEqual(result, "NoOp")


# ---------------------------------------------------------------------------
# Tests for detect_link_class_for_node() — ensuring probe replaces heuristic
# ---------------------------------------------------------------------------

class TestDetectLinkClassForNode(unittest.TestCase):
    """Verify detect_link_class_for_node() uses the probe for unknown classes."""

    def test_none_input_returns_noop(self):
        """None input_node returns 'NoOp' without calling any API."""
        result = _link.detect_link_class_for_node(None)
        self.assertEqual(result, "NoOp")

    def test_dot_node_returns_dot(self):
        """Dot node returns 'Dot' via the early-return fast-path."""
        node = _StubNode(node_class="Dot")
        result = _link.detect_link_class_for_node(node)
        self.assertEqual(result, "Dot")

    def test_known_class_read_returns_postage_stamp(self):
        """Read node returns 'PostageStamp' via LINK_CLASSES fast-path."""
        node = _StubNode(node_class="Read")
        result = _link.detect_link_class_for_node(node)
        self.assertEqual(result, "PostageStamp")

    def test_known_class_camera_returns_noop(self):
        """Camera node returns 'NoOp' via LINK_CLASSES fast-path."""
        node = _StubNode(node_class="Camera")
        result = _link.detect_link_class_for_node(node)
        self.assertEqual(result, "NoOp")

    def test_unknown_2d_node_returns_postage_stamp_via_probe(self):
        """Unknown node type that accepts 2D (NoOp) scratch returns 'PostageStamp' via probe."""
        node = _StubNode(node_class="SomeFuture2DNode")
        node._can_set_input_results[0] = {"NoOp": True}
        result = _link.detect_link_class_for_node(node)
        self.assertEqual(result, "PostageStamp")

    def test_unknown_3d_node_returns_noop_via_probe(self):
        """Unknown node type that accepts 3D (Scene) scratch returns 'NoOp' via probe."""
        node = _StubNode(node_class="SomeFuture3DNode")
        node._can_set_input_results[0] = {"Scene": True}
        result = _link.detect_link_class_for_node(node)
        self.assertEqual(result, "NoOp")

    def test_unknown_deep_node_returns_noop_via_probe(self):
        """Unknown node type that accepts Deep (DeepMerge) scratch returns 'NoOp' via probe."""
        node = _StubNode(node_class="SomeFutureDeepNode")
        node._can_set_input_results[0] = {"DeepMerge": True}
        result = _link.detect_link_class_for_node(node)
        self.assertEqual(result, "NoOp")

    def test_no_channel_name_attributes_used(self):
        """detect_link_class_for_node() does NOT call channels() on any node."""
        channels_called = []

        class _NodeThatTracksChannelsCalls(_StubNode):
            def channels(self):
                channels_called.append(True)
                return []

        node = _NodeThatTracksChannelsCalls(node_class="SomeUnknownNode")
        _link.detect_link_class_for_node(node)

        self.assertEqual(channels_called, [],
            "detect_link_class_for_node() must not call node.channels() — use probe instead")

    def test_no_2d_channel_prefixes_constant_referenced(self):
        """The _2D_CHANNEL_PREFIXES constant is removed from link.py."""
        self.assertFalse(
            hasattr(_link, "_2D_CHANNEL_PREFIXES"),
            "_2D_CHANNEL_PREFIXES should be removed from link.py after replacing channel heuristic"
        )


if __name__ == "__main__":
    unittest.main()
