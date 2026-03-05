"""Tests for Dot anchor node name sync in mark_dot_as_anchor() and rename_anchor_to().

Covers:
- mark_dot_as_anchor() with labelled Dot: node name becomes 'Anchor_<sanitized_label>'
- mark_dot_as_anchor() with empty-label Dot: node name unchanged
- mark_dot_as_anchor() called twice on same node: idempotent (knob guard fires, name still correct)
- rename_anchor_to() Dot anchor: label updated
- rename_anchor_to() Dot anchor: node name updated to 'Anchor_<sanitized>'
- rename_anchor_to() Dot anchor: old FQNN in link nodes updated to new FQNN
- rename_anchor_to() Dot anchor with name that sanitizes to empty: raises ValueError
- anchor_display_name() for Dot still returns label (not derived from node name)
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Stub Qt and tabtabtab modules — anchor.py imports these at module level.
# These stubs must be installed before any local imports so the import chain
# does not fail in an offline environment without PySide6/PySide2.
# ---------------------------------------------------------------------------

def _make_stub_qt_module(name):
    """Return a minimal Qt sub-module stub with common attribute placeholders."""
    stub = types.ModuleType(name)
    stub.Qt = MagicMock()
    stub.QtCore = MagicMock()
    stub.QtGui = MagicMock()
    stub.QtWidgets = MagicMock()
    return stub


_pyside6_stub = _make_stub_qt_module('PySide6')
_pyside6_stub.QtCore = _make_stub_qt_module('PySide6.QtCore')
_pyside6_stub.QtGui = _make_stub_qt_module('PySide6.QtGui')
_pyside6_stub.QtWidgets = _make_stub_qt_module('PySide6.QtWidgets')
_pyside6_stub.QtCore.Qt = MagicMock()
sys.modules['PySide6'] = _pyside6_stub
sys.modules['PySide6.QtCore'] = _pyside6_stub.QtCore
sys.modules['PySide6.QtGui'] = _pyside6_stub.QtGui
sys.modules['PySide6.QtWidgets'] = _pyside6_stub.QtWidgets

_tabtabtab_stub = types.ModuleType('tabtabtab')
_tabtabtab_stub.TabTabTabPlugin = MagicMock
_tabtabtab_stub.TabTabTabWidget = MagicMock
sys.modules['tabtabtab'] = _tabtabtab_stub


# ---------------------------------------------------------------------------
# Stub nuke and nukescripts modules — must be inserted before any local imports
# ---------------------------------------------------------------------------

def make_stub_nuke_module():
    """Create a minimal nuke stub for offline testing."""
    stub = types.ModuleType('nuke')

    class StubKnob:
        def __init__(self, value=''):
            self._value = value
            self._visible = True

        def getText(self):
            return self._value

        def setValue(self, value):
            self._value = value

        def getValue(self):
            return self._value

        def setVisible(self, visible):
            self._visible = visible

        def setFlag(self, flag):
            pass

        def setText(self, value):
            self._value = value

    class StubNode:
        def __init__(self, name='Node', node_class='NoOp', xpos=0, ypos=0, knobs_dict=None):
            self._name = name
            self._class = node_class
            self._xpos = xpos
            self._ypos = ypos
            self._knobs = knobs_dict or {}
            self._input = None
            self._selected = False
            self._set_name_calls = []

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

        def setName(self, new_name):
            self._name = new_name
            self._set_name_calls.append(new_name)

        def addKnob(self, knob):
            pass

        def removeKnob(self, knob):
            pass

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
    root_obj.name.return_value = 'myScript.nk'
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

    # Knob factory methods
    stub.String_Knob = MagicMock(side_effect=lambda name, *args: StubKnob())
    stub.Tab_Knob = MagicMock(side_effect=lambda name, *args: StubKnob())
    stub.Boolean_Knob = MagicMock(side_effect=lambda name, *args: StubKnob())
    stub.PyScript_Knob = MagicMock(side_effect=lambda *args: StubKnob())

    return stub


sys.modules['nuke'] = make_stub_nuke_module()
sys.modules['nukescripts'] = types.ModuleType('nukescripts')
sys.modules['nukescripts'].cut_paste_file = lambda: '/tmp/nuke_stub_clipboard.nk'
sys.modules['nukescripts'].clear_selection_recursive = MagicMock()


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _make_stub_node(name='Node', node_class='Dot', knobs_dict=None):
    """Create a StubNode with the given knobs dict."""
    import nuke as _nuke
    return _nuke.StubNode(name=name, node_class=node_class, knobs_dict=knobs_dict or {})


def _make_knob(value=''):
    """Create a StubKnob with the given value."""
    import nuke as _nuke
    return _nuke.StubKnob(value)


def _make_dot_node(name='Dot1', label=''):
    """Return a Dot StubNode with a label knob set to the given value."""
    import nuke as _nuke
    return _nuke.StubNode(
        name=name,
        node_class='Dot',
        knobs_dict={
            'label': _nuke.StubKnob(label),
        }
    )


def _make_link_node(knob_name_value='', label=''):
    """Return a NoOp StubNode that looks like a link node (has KNOB_NAME knob)."""
    import nuke as _nuke
    from constants import KNOB_NAME
    return _nuke.StubNode(
        name='NoOp1',
        node_class='NoOp',
        knobs_dict={
            KNOB_NAME: _nuke.StubKnob(knob_name_value),
            'label': _nuke.StubKnob(label),
        }
    )


# ---------------------------------------------------------------------------
# Tests for mark_dot_as_anchor() — node name sync
# ---------------------------------------------------------------------------

class TestMarkDotAsAnchorNameSync(unittest.TestCase):
    """mark_dot_as_anchor() must sync the Dot node name to 'Anchor_<sanitized_label>'."""

    def test_mark_dot_as_anchor_with_labelled_dot_sets_node_name_to_anchor_prefix_plus_sanitized_label(self):
        """mark_dot_as_anchor() on a Dot with label 'My Footage' must set node name to 'Anchor_My_Footage'."""
        import nuke as _nuke
        from constants import DOT_ANCHOR_KNOB_NAME, ANCHOR_PREFIX

        dot_node = _make_dot_node(name='Dot1', label='My Footage')

        stub_boolean_knob = _nuke.StubKnob()
        _nuke.Boolean_Knob = MagicMock(return_value=stub_boolean_knob)

        with patch('link.nuke', _nuke):
            from link import mark_dot_as_anchor
            mark_dot_as_anchor(dot_node)

        self.assertEqual(
            dot_node.name(),
            'Anchor_My_Footage',
            "mark_dot_as_anchor() must set node name to 'Anchor_<sanitized_label>' when label is non-empty"
        )

    def test_mark_dot_as_anchor_with_empty_label_dot_leaves_node_name_unchanged(self):
        """mark_dot_as_anchor() on a Dot with empty label must NOT change the node name."""
        import nuke as _nuke

        dot_node = _make_dot_node(name='Dot3', label='')

        stub_boolean_knob = _nuke.StubKnob()
        _nuke.Boolean_Knob = MagicMock(return_value=stub_boolean_knob)

        with patch('link.nuke', _nuke):
            from link import mark_dot_as_anchor
            mark_dot_as_anchor(dot_node)

        self.assertEqual(
            dot_node.name(),
            'Dot3',
            "mark_dot_as_anchor() must NOT change node name when label is empty"
        )

    def test_mark_dot_as_anchor_called_twice_is_idempotent_and_node_name_is_still_correct(self):
        """Calling mark_dot_as_anchor() twice must be idempotent.

        The second call hits the knob guard (DOT_ANCHOR_KNOB_NAME already present),
        sets the knob to True, and returns early. The node name set on the first call
        must still be 'Anchor_MyClip'.
        """
        import nuke as _nuke
        from constants import DOT_ANCHOR_KNOB_NAME

        stub_anchor_knob = _nuke.StubKnob(True)
        dot_node = _nuke.StubNode(
            name='Dot1',
            node_class='Dot',
            knobs_dict={
                'label': _nuke.StubKnob('MyClip'),
                DOT_ANCHOR_KNOB_NAME: stub_anchor_knob,
            }
        )
        # Pre-set name as if the first call already renamed it
        dot_node._name = 'Anchor_MyClip'

        stub_boolean_knob = _nuke.StubKnob()
        _nuke.Boolean_Knob = MagicMock(return_value=stub_boolean_knob)

        with patch('link.nuke', _nuke):
            from link import mark_dot_as_anchor
            mark_dot_as_anchor(dot_node)

        self.assertEqual(
            dot_node.name(),
            'Anchor_MyClip',
            "Node name must remain 'Anchor_MyClip' after idempotent second call"
        )
        # The early-return path must have set the knob value to True
        self.assertEqual(
            stub_anchor_knob.getValue(),
            True,
            "DOT_ANCHOR_KNOB_NAME knob must be set to True on second call"
        )


# ---------------------------------------------------------------------------
# Tests for rename_anchor_to() Dot anchor path — node name + FQNN sync
# ---------------------------------------------------------------------------

class TestRenameAnchorToDotPath(unittest.TestCase):
    """rename_anchor_to() for Dot anchors must update node name, label, and link FQNNs."""

    def _make_dot_anchor_with_label(self, name='Dot1', label='OldName'):
        """Return a Dot StubNode that represents a Dot anchor with a label."""
        import nuke as _nuke
        return _nuke.StubNode(
            name=name,
            node_class='Dot',
            knobs_dict={
                'label': _nuke.StubKnob(label),
            }
        )

    def test_rename_anchor_to_dot_updates_label(self):
        """rename_anchor_to(dot_anchor, 'NewName') must update the Dot's label knob."""
        import nuke as _nuke

        dot_anchor = self._make_dot_anchor_with_label(name='Anchor_OldName', label='OldName')

        with patch('anchor.nuke', _nuke), \
             patch('anchor.nuke.allNodes', return_value=[]), \
             patch('anchor.is_link', return_value=False), \
             patch('anchor.get_fully_qualified_node_name',
                   side_effect=['myScript.Anchor_OldName', 'myScript.Anchor_NewName']):
            from anchor import rename_anchor_to
            rename_anchor_to(dot_anchor, 'NewName')

        self.assertEqual(
            dot_anchor['label'].getValue(),
            'NewName',
            "rename_anchor_to() must set the Dot's label to 'NewName'"
        )

    def test_rename_anchor_to_dot_updates_node_name_to_anchor_prefix_plus_sanitized(self):
        """rename_anchor_to(dot_anchor, 'New Name') must set node name to 'Anchor_New_Name'."""
        import nuke as _nuke

        dot_anchor = self._make_dot_anchor_with_label(name='Anchor_OldName', label='OldName')

        with patch('anchor.nuke', _nuke), \
             patch('anchor.nuke.allNodes', return_value=[]), \
             patch('anchor.is_link', return_value=False), \
             patch('anchor.get_fully_qualified_node_name',
                   side_effect=['myScript.Anchor_OldName', 'myScript.Anchor_New_Name']):
            from anchor import rename_anchor_to
            rename_anchor_to(dot_anchor, 'New Name')

        self.assertEqual(
            dot_anchor.name(),
            'Anchor_New_Name',
            "rename_anchor_to() must set node name to 'Anchor_New_Name' (sanitized)"
        )

    def test_rename_anchor_to_dot_updates_link_node_knob_name_from_old_fqnn_to_new_fqnn(self):
        """rename_anchor_to() must update KNOB_NAME on all link nodes that stored the old FQNN."""
        import nuke as _nuke
        from constants import KNOB_NAME

        dot_anchor = self._make_dot_anchor_with_label(name='Anchor_OldName', label='OldName')

        old_fqnn = 'myScript.Anchor_OldName'
        new_fqnn = 'myScript.Anchor_NewName'

        link_node_matching = _make_link_node(knob_name_value=old_fqnn, label='Link: OldName')
        link_node_unrelated = _make_link_node(knob_name_value='myScript.Anchor_OtherNode', label='Link: OtherNode')

        def is_link_stub(node):
            return KNOB_NAME in node.knobs()

        with patch('anchor.nuke', _nuke), \
             patch('anchor.nuke.allNodes', return_value=[link_node_matching, link_node_unrelated]), \
             patch('anchor.is_link', side_effect=is_link_stub), \
             patch('anchor.get_fully_qualified_node_name',
                   side_effect=[old_fqnn, new_fqnn]):
            from anchor import rename_anchor_to
            rename_anchor_to(dot_anchor, 'NewName')

        self.assertEqual(
            link_node_matching[KNOB_NAME].getValue(),
            new_fqnn,
            "Matching link node KNOB_NAME must be updated from old FQNN to new FQNN"
        )
        self.assertEqual(
            link_node_unrelated[KNOB_NAME].getValue(),
            'myScript.Anchor_OtherNode',
            "Unrelated link node KNOB_NAME must remain unchanged"
        )

    def test_rename_anchor_to_dot_updates_link_node_label_to_new_name(self):
        """rename_anchor_to() must update the label of matching link nodes to 'Link: NewName'."""
        import nuke as _nuke
        from constants import KNOB_NAME

        dot_anchor = self._make_dot_anchor_with_label(name='Anchor_OldName', label='OldName')

        old_fqnn = 'myScript.Anchor_OldName'
        new_fqnn = 'myScript.Anchor_NewName'

        link_node = _make_link_node(knob_name_value=old_fqnn, label='Link: OldName')

        def is_link_stub(node):
            return KNOB_NAME in node.knobs()

        with patch('anchor.nuke', _nuke), \
             patch('anchor.nuke.allNodes', return_value=[link_node]), \
             patch('anchor.is_link', side_effect=is_link_stub), \
             patch('anchor.get_fully_qualified_node_name',
                   side_effect=[old_fqnn, new_fqnn]):
            from anchor import rename_anchor_to
            rename_anchor_to(dot_anchor, 'NewName')

        self.assertEqual(
            link_node['label'].getValue(),
            'Link: NewName',
            "Matching link node label must be updated to 'Link: NewName'"
        )

    def test_rename_anchor_to_dot_with_name_that_sanitizes_to_empty_raises_value_error(self):
        """rename_anchor_to() with a name that sanitizes to '' must raise ValueError for Dot anchors.

        The sanitize_anchor_name() regex keeps only [A-Za-z0-9_], so a name consisting
        entirely of spaces (after strip() → '') produces an empty sanitized result.
        """
        import nuke as _nuke

        dot_anchor = self._make_dot_anchor_with_label(name='Anchor_OldName', label='OldName')

        with patch('anchor.nuke', _nuke), \
             patch('anchor.nuke.allNodes', return_value=[]), \
             patch('anchor.is_link', return_value=False), \
             patch('anchor.get_fully_qualified_node_name',
                   return_value='myScript.Anchor_OldName'):
            from anchor import rename_anchor_to
            with self.assertRaises(ValueError):
                # A name of only spaces: strip() → '', sanitize → '' → ValueError
                rename_anchor_to(dot_anchor, '   ')


# ---------------------------------------------------------------------------
# Tests for anchor_display_name() — must remain label-based for Dot anchors
# ---------------------------------------------------------------------------

class TestAnchorDisplayNameDotPath(unittest.TestCase):
    """anchor_display_name() must still return label text for Dot anchors, not node name."""

    def test_anchor_display_name_returns_label_for_dot_anchor_with_anchor_prefix_node_name(self):
        """anchor_display_name() on a Dot with node name 'Anchor_MyFootage' must return the label, not the node name."""
        import nuke as _nuke

        dot_anchor = _nuke.StubNode(
            name='Anchor_MyFootage',
            node_class='Dot',
            knobs_dict={
                'label': _nuke.StubKnob('MyFootage'),
            }
        )

        with patch('anchor.nuke', _nuke):
            from anchor import anchor_display_name
            display_name = anchor_display_name(dot_anchor)

        self.assertEqual(
            display_name,
            'MyFootage',
            "anchor_display_name() must return the label text for Dot anchors, not the node name"
        )

    def test_anchor_display_name_returns_label_for_dot_anchor_with_spaces_in_label(self):
        """anchor_display_name() must return the label with spaces preserved."""
        import nuke as _nuke

        dot_anchor = _nuke.StubNode(
            name='Anchor_My_Footage',
            node_class='Dot',
            knobs_dict={
                'label': _nuke.StubKnob('My Footage'),
            }
        )

        with patch('anchor.nuke', _nuke):
            from anchor import anchor_display_name
            display_name = anchor_display_name(dot_anchor)

        self.assertEqual(
            display_name,
            'My Footage',
            "anchor_display_name() must return label text 'My Footage' (spaces preserved)"
        )


if __name__ == '__main__':
    unittest.main()
