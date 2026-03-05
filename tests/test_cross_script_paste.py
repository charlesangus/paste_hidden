"""Tests for cross-script paste reconnection logic.

Covers:
- _extract_display_name_from_fqnn() helper
- paste_hidden() Path A/C cross-script name-based reconnect for NoOp anchors (XSCRIPT-01)
- paste_hidden() Path B Dot cross-script disconnection (XSCRIPT-02 / PASTE-04)
- LINK_SOURCE_CLASSES frozenset membership
- ANCHOR_LINK_CLASS_KNOB_NAME removed from constants
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Stub nuke and nukescripts modules — must be inserted before any local imports
# ---------------------------------------------------------------------------

def make_stub_nuke_module():
    """Create a minimal nuke stub for offline testing."""
    stub = types.ModuleType('nuke')

    class StubKnob:
        def __init__(self, value=''):
            self._value = value

        def getText(self):
            return self._value

        def setValue(self, value):
            self._value = value

        def getValue(self):
            return self._value

    class StubNode:
        def __init__(self, name='Node', node_class='NoOp', xpos=0, ypos=0, knobs_dict=None):
            self._name = name
            self._class = node_class
            self._xpos = xpos
            self._ypos = ypos
            self._knobs = knobs_dict or {}
            self._input = None
            self._selected = False

        def name(self):
            return self._name

        def fullName(self):
            return self._name

        def Class(self):
            return self._class

        def xpos(self):
            return self._xpos

        def ypos(self):
            return self._ypos

        def knobs(self):
            return self._knobs

        def input(self, index):
            return self._input

        def setInput(self, index, node):
            self._input = node

        def setXYpos(self, x, y):
            self._xpos = x
            self._ypos = y

        def __getitem__(self, knob_name):
            if knob_name not in self._knobs:
                raise KeyError(knob_name)
            return self._knobs[knob_name]

        def __setitem__(self, knob_name, value):
            self._knobs[knob_name] = value

    stub.StubNode = StubNode
    stub.StubKnob = StubKnob

    # nuke.root() returns an object whose .name() returns a script path
    root_obj = MagicMock()
    root_obj.name.return_value = 'destScript.nk'
    stub.root = MagicMock(return_value=root_obj)

    stub.allNodes = MagicMock(return_value=[])
    stub.toNode = MagicMock(return_value=None)
    stub.createNode = MagicMock()
    stub.selectedNodes = MagicMock(return_value=[])
    stub.nodeCopy = MagicMock()
    stub.nodePaste = MagicMock(return_value=None)
    stub.exists = MagicMock(return_value=False)
    stub.delete = MagicMock()
    stub.INVISIBLE = 0

    return stub


sys.modules['nuke'] = make_stub_nuke_module()
sys.modules['nukescripts'] = types.ModuleType('nukescripts')
sys.modules['nukescripts'].cut_paste_file = lambda: '/tmp/nuke_stub_clipboard.nk'
sys.modules['nukescripts'].clear_selection_recursive = MagicMock()


# ---------------------------------------------------------------------------
# Tests for LINK_SOURCE_CLASSES and removed ANCHOR_LINK_CLASS_KNOB_NAME
# ---------------------------------------------------------------------------

class TestConstantsCleanup(unittest.TestCase):

    def test_link_source_classes_contains_all_eight_expected_class_names(self):
        from constants import LINK_SOURCE_CLASSES
        expected_classes = {
            "Read", "DeepRead", "ReadGeo",
            "Camera", "Camera2", "Camera3", "Camera4",
            "GeoImport",
        }
        self.assertEqual(LINK_SOURCE_CLASSES, expected_classes)

    def test_link_source_classes_is_a_frozenset(self):
        from constants import LINK_SOURCE_CLASSES
        self.assertIsInstance(LINK_SOURCE_CLASSES, frozenset)

    def test_anchor_link_class_knob_name_not_importable_from_constants(self):
        import constants
        self.assertFalse(
            hasattr(constants, 'ANCHOR_LINK_CLASS_KNOB_NAME'),
            "ANCHOR_LINK_CLASS_KNOB_NAME should have been removed from constants.py",
        )


# ---------------------------------------------------------------------------
# Tests for _extract_display_name_from_fqnn() helper
# ---------------------------------------------------------------------------

class TestExtractDisplayNameFromFqnn(unittest.TestCase):

    def setUp(self):
        # Import inside setUp to ensure stub is in place
        from paste_hidden import _extract_display_name_from_fqnn
        self.extract = _extract_display_name_from_fqnn

    def test_simple_anchor_fqnn_returns_display_name(self):
        result = self.extract('shotA.Anchor_MyFootage')
        self.assertEqual(result, 'MyFootage')

    def test_group_nested_anchor_fqnn_returns_last_segment_display_name(self):
        # last segment only — Group nesting is collapsed
        result = self.extract('shotA.Group1.Anchor_MyFootage')
        self.assertEqual(result, 'MyFootage')

    def test_empty_fqnn_returns_none(self):
        result = self.extract('')
        self.assertIsNone(result)

    def test_fqnn_without_anchor_prefix_returns_none(self):
        # File node case — last segment does not start with ANCHOR_PREFIX
        result = self.extract('shotA.Read1')
        self.assertIsNone(result)

    def test_fqnn_with_anchor_prefix_only_returns_empty_string(self):
        # 'Anchor_' with nothing after the prefix — edge case
        result = self.extract('shotA.Anchor_')
        self.assertEqual(result, '')


# ---------------------------------------------------------------------------
# Integration tests for paste_hidden() cross-script reconnect behavior
# ---------------------------------------------------------------------------

class TestCrossScriptReconnect(unittest.TestCase):
    """Test paste_hidden() Path A/C cross-script reconnection via stubs."""

    def _make_noop_anchor_node(self, anchor_name, stored_fqnn, xpos=100, ypos=200):
        """Return a stub NoOp anchor node with KNOB_NAME set."""
        import nuke as _nuke
        from constants import KNOB_NAME, ANCHOR_PREFIX
        knob = _nuke.StubKnob(stored_fqnn)
        selected_knob = _nuke.StubKnob(False)
        node = _nuke.StubNode(
            name=ANCHOR_PREFIX + anchor_name,
            node_class='NoOp',
            xpos=xpos,
            ypos=ypos,
            knobs_dict={KNOB_NAME: knob, 'selected': selected_knob},
        )
        return node

    def _make_dot_anchor_node(self, stored_fqnn):
        """Return a stub Dot anchor node with KNOB_NAME set."""
        import nuke as _nuke
        from constants import KNOB_NAME
        knob = _nuke.StubKnob(stored_fqnn)
        selected_knob = _nuke.StubKnob(False)
        node = _nuke.StubNode(
            name='Dot1',
            node_class='Dot',
            knobs_dict={KNOB_NAME: knob, 'selected': selected_knob},
        )
        return node

    def test_cross_script_reconnect_with_matching_anchor_creates_link_and_deletes_placeholder(self):
        """When a NoOp anchor is pasted cross-script and a matching anchor exists in the
        destination script, paste_hidden() should create a new link node, wire it, and
        delete the pasted placeholder."""
        import nuke as _nuke
        from constants import KNOB_NAME

        pasted_anchor_node = self._make_noop_anchor_node(
            anchor_name='MyFootage',
            stored_fqnn='sourceScript.Anchor_MyFootage',
            xpos=100,
            ypos=200,
        )

        destination_anchor = _nuke.StubNode(
            name='Anchor_MyFootage',
            node_class='NoOp',
        )
        created_link_node = _nuke.StubNode(name='NoOp1', node_class='NoOp',
                                           knobs_dict={'selected': _nuke.StubKnob(False)})

        with patch('paste_hidden.nuke') as mock_nuke, \
             patch('paste_hidden.nukescripts') as mock_nukescripts, \
             patch('paste_hidden.find_anchor_node', return_value=None) as mock_find_anchor_node, \
             patch('paste_hidden.find_anchor_by_name', return_value=destination_anchor) as mock_find_by_name, \
             patch('paste_hidden.setup_link_node') as mock_setup_link_node, \
             patch('paste_hidden.is_anchor', return_value=True) as mock_is_anchor:

            mock_nuke.nodePaste.return_value = None
            mock_nuke.selectedNodes.return_value = [pasted_anchor_node]
            mock_nuke.createNode.return_value = created_link_node

            from paste_hidden import paste_hidden
            paste_hidden()

            # A new NoOp link node should have been created
            mock_nuke.createNode.assert_called_once_with('NoOp')

            # setup_link_node should have been called to wire the new link
            mock_setup_link_node.assert_called_once_with(destination_anchor, created_link_node)

            # The placeholder node should have been deleted
            mock_nuke.delete.assert_called_once_with(pasted_anchor_node)

    def test_cross_script_reconnect_with_no_matching_anchor_leaves_placeholder(self):
        """When a NoOp anchor is pasted cross-script but no matching anchor exists in
        the destination, paste_hidden() should leave the placeholder node intact."""
        import nuke as _nuke

        pasted_anchor_node = self._make_noop_anchor_node(
            anchor_name='UnknownFootage',
            stored_fqnn='sourceScript.Anchor_UnknownFootage',
        )

        with patch('paste_hidden.nuke') as mock_nuke, \
             patch('paste_hidden.nukescripts') as mock_nukescripts, \
             patch('paste_hidden.find_anchor_node', return_value=None), \
             patch('paste_hidden.find_anchor_by_name', return_value=None), \
             patch('paste_hidden.setup_link_node') as mock_setup_link_node, \
             patch('paste_hidden.is_anchor', return_value=True):

            mock_nuke.nodePaste.return_value = None
            mock_nuke.selectedNodes.return_value = [pasted_anchor_node]

            from paste_hidden import paste_hidden
            paste_hidden()

            # No new node should be created; placeholder stays
            mock_nuke.createNode.assert_not_called()
            mock_nuke.delete.assert_not_called()

    def test_dot_anchor_pasted_cross_script_does_not_attempt_reconnect(self):
        """A Dot anchor pasted cross-script must NOT trigger the name-based
        reconnect — the node.Class() == 'Dot' gate must prevent it."""
        import nuke as _nuke

        dot_anchor_node = self._make_dot_anchor_node(
            stored_fqnn='sourceScript.Dot1',
        )

        with patch('paste_hidden.nuke') as mock_nuke, \
             patch('paste_hidden.nukescripts') as mock_nukescripts, \
             patch('paste_hidden.find_anchor_node', return_value=None), \
             patch('paste_hidden.find_anchor_by_name') as mock_find_by_name, \
             patch('paste_hidden.setup_link_node') as mock_setup_link_node, \
             patch('paste_hidden.is_anchor', return_value=True):

            mock_nuke.nodePaste.return_value = None
            mock_nuke.selectedNodes.return_value = [dot_anchor_node]

            from paste_hidden import paste_hidden
            paste_hidden()

            # find_anchor_by_name must NOT be called for Dot anchors
            mock_find_by_name.assert_not_called()
            mock_nuke.createNode.assert_not_called()
            mock_nuke.delete.assert_not_called()


if __name__ == '__main__':
    unittest.main()
