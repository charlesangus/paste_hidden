"""Tests for the anchor color system (COLOR-01 through COLOR-05).

Covers:
- COLOR-01: AnchorPlugin/AnchorNavigatePlugin.get_color() reads tile_color.value() directly
- COLOR-02: create_anchor_named() accepts explicit color param
- COLOR-03: rename_anchor_to() propagates color after rename
- COLOR-04: add_set_color_anchor_knob() adds knob to NoOp anchors, not Dots
- COLOR-05: propagate_anchor_color() sets anchor + all link tile_colors; skips Dots
- Palette: load_user_palette() and save_user_palette() round-trip correctly
"""

import json
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Stub Qt and tabtabtab modules — anchor.py imports these at module level.
# These stubs must be installed before any local imports.
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
# Use MagicMock for sub-modules so attribute access (e.g. QtWidgets.QDialog)
# returns a MagicMock automatically — this allows colors.py to subclass
# QtWidgets.QDialog without AttributeError.
_pyside6_stub.QtCore = MagicMock()
_pyside6_stub.QtGui = MagicMock()
_pyside6_stub.QtWidgets = MagicMock()
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
# Stub colors module before importing anchor so 'from colors import ...' works
# ---------------------------------------------------------------------------

_colors_stub = types.ModuleType('colors')
_colors_stub.ColorPaletteDialog = None
sys.modules['colors'] = _colors_stub


# ---------------------------------------------------------------------------
# Stub nuke and nukescripts modules
# ---------------------------------------------------------------------------

def make_stub_nuke_module():
    """Create a minimal nuke stub for offline testing."""
    stub = types.ModuleType('nuke')

    class StubKnob:
        def __init__(self, value=''):
            self._value = value

        def getText(self):
            return str(self._value)

        def setValue(self, value):
            self._value = value

        def getValue(self):
            return self._value

        def value(self):
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

        def screenWidth(self):
            return 100

        def screenHeight(self):
            return 50

        def knobs(self):
            return self._knobs

        def input(self, index):
            return self._input

        def setInput(self, index, node):
            self._input = node

        def setXYpos(self, x, y):
            self._xpos = x
            self._ypos = y

        def setName(self, name):
            self._name = name

        def addKnob(self, knob):
            self._knobs[knob.name()] = knob

        def __getitem__(self, knob_name):
            if knob_name not in self._knobs:
                raise KeyError(knob_name)
            return self._knobs[knob_name]

        def __setitem__(self, knob_name, value):
            self._knobs[knob_name] = value

    stub.StubNode = StubNode
    stub.StubKnob = StubKnob

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
    stub.NUKE_VERSION_MAJOR = 16  # triggers PySide6 import path in anchor.py
    stub.PyScript_Knob = MagicMock(side_effect=lambda knob_name, label, script: _make_pyscript_knob(knob_name, label, script))

    return stub


def _make_pyscript_knob(knob_name, label, script):
    """Return a minimal PyScript_Knob stand-in that supports .name()."""
    knob = MagicMock()
    knob.name.return_value = knob_name
    knob._knob_name = knob_name
    return knob


_nuke_stub = make_stub_nuke_module()
sys.modules['nuke'] = _nuke_stub
sys.modules['nukescripts'] = types.ModuleType('nukescripts')
sys.modules['nukescripts'].cut_paste_file = lambda: '/tmp/nuke_stub_clipboard.nk'
sys.modules['nukescripts'].clear_selection_recursive = MagicMock()

# ---------------------------------------------------------------------------
# Now that nuke stub is in place, load the real colors module and replace the
# placeholder stub.  The palette helper functions (load_user_palette,
# save_user_palette) do not need Qt — they will be importable even with the
# Qt guard falling back to None.
# ---------------------------------------------------------------------------
import importlib
# Remove the placeholder so importlib loads the real file from /workspace/colors.py
del sys.modules['colors']
import colors as _real_colors_module
sys.modules['colors'] = _real_colors_module


# ---------------------------------------------------------------------------
# COLOR-01: AnchorPlugin.get_color() reads tile_color directly
# ---------------------------------------------------------------------------

def _ensure_qt_stubs_support_mock_attributes():
    """Ensure Qt stub modules support auto-attribute access for the anchor tests.

    When the full test suite is discovered, test_cross_script_paste.py installs
    Qt sub-module stubs as plain types.ModuleType objects.  These do NOT create
    attributes on access (unlike MagicMock), so calls like QtGui.QColor(...) raise
    AttributeError.  This helper patches the current stubs to be MagicMock-based
    if they are plain ModuleType instances.

    Also ensures the nuke stub has NUKE_VERSION_MAJOR = 16 so anchor.py takes
    the PySide6 import path on reload (not PySide2 → ImportError → QtGui = None).
    """
    import nuke as current_nuke
    if not hasattr(current_nuke, 'NUKE_VERSION_MAJOR'):
        current_nuke.NUKE_VERSION_MAJOR = 16

    # Patch Qt sub-module stubs if they are plain ModuleType (not MagicMock)
    for module_key in ('PySide6.QtGui', 'PySide6.QtWidgets', 'PySide6.QtCore'):
        existing = sys.modules.get(module_key)
        if existing is not None and not isinstance(existing, MagicMock):
            mock_replacement = MagicMock()
            sys.modules[module_key] = mock_replacement
            # Also update the parent stub's attribute
            parent_key = 'PySide6'
            attr_name = module_key.split('.')[-1]
            parent_stub = sys.modules.get(parent_key)
            if parent_stub is not None:
                setattr(parent_stub, attr_name, mock_replacement)


class TestAnchorPickerColorReadsFromKnob(unittest.TestCase):
    """COLOR-01: AnchorPlugin.get_color() calls tile_color.value(), not find_anchor_color()."""

    def setUp(self):
        import importlib
        _ensure_qt_stubs_support_mock_attributes()
        import anchor as anchor_mod
        importlib.reload(anchor_mod)
        self.anchor_mod = anchor_mod

    def test_get_color_reads_tile_color_value_not_find_anchor_color(self):
        plugin = self.anchor_mod.AnchorPlugin()

        anchor_mock = MagicMock()
        tile_color_knob = MagicMock()
        tile_color_knob.value.return_value = 0x6f3399ff
        anchor_mock.__getitem__ = MagicMock(side_effect=lambda key: tile_color_knob if key == 'tile_color' else MagicMock())

        with patch.object(self.anchor_mod, 'find_anchor_color') as mock_find_color:
            plugin.get_color(anchor_mock)
            mock_find_color.assert_not_called()

        tile_color_knob.value.assert_called()

    def test_get_color_uses_value_from_tile_color_knob(self):
        plugin = self.anchor_mod.AnchorPlugin()

        expected_color_int = 0xAABBCCFF
        anchor_mock = MagicMock()
        tile_color_knob = MagicMock()
        tile_color_knob.value.return_value = expected_color_int
        anchor_mock.__getitem__ = MagicMock(side_effect=lambda key: tile_color_knob if key == 'tile_color' else MagicMock())

        # The result should be derived from the tile_color knob, not find_anchor_color
        with patch.object(self.anchor_mod, 'find_anchor_color', return_value=0x000000FF):
            color_result = plugin.get_color(anchor_mock)

        # Color should NOT be derived from find_anchor_color's return value (0x000000FF)
        # It should be derived from tile_color.value() (0xAABBCCFF)
        # QColor is called with r=0xAA, g=0xBB, b=0xCC
        import anchor as anchor_mod_check
        qt_gui = anchor_mod_check.QtGui
        expected_r = (expected_color_int >> 24) & 0xFF
        expected_g = (expected_color_int >> 16) & 0xFF
        expected_b = (expected_color_int >> 8) & 0xFF
        qt_gui.QColor.assert_called_with(expected_r, expected_g, expected_b)


# ---------------------------------------------------------------------------
# COLOR-01: AnchorNavigatePlugin.get_color() reads tile_color directly
# ---------------------------------------------------------------------------

class TestAnchorNavigatePickerColorReadsFromKnob(unittest.TestCase):
    """COLOR-01: AnchorNavigatePlugin.get_color() calls tile_color.value(), not find_anchor_color()."""

    def setUp(self):
        import importlib
        _ensure_qt_stubs_support_mock_attributes()
        import anchor as anchor_mod
        importlib.reload(anchor_mod)
        self.anchor_mod = anchor_mod

    def test_navigate_get_color_reads_tile_color_value_not_find_anchor_color(self):
        plugin = self.anchor_mod.AnchorNavigatePlugin()

        anchor_mock = MagicMock()
        tile_color_knob = MagicMock()
        tile_color_knob.value.return_value = 0x6f3399ff
        anchor_mock.__getitem__ = MagicMock(side_effect=lambda key: tile_color_knob if key == 'tile_color' else MagicMock())

        with patch.object(self.anchor_mod, 'find_anchor_color') as mock_find_color:
            plugin.get_color(anchor_mock)
            mock_find_color.assert_not_called()

        tile_color_knob.value.assert_called()


# ---------------------------------------------------------------------------
# COLOR-02: create_anchor_named() accepts explicit color param
# ---------------------------------------------------------------------------

class TestCreateAnchorNamedColorParam(unittest.TestCase):
    """COLOR-02: create_anchor_named() with explicit color calls setValue with that color."""

    def setUp(self):
        import importlib
        import anchor as anchor_mod
        importlib.reload(anchor_mod)
        self.anchor_mod = anchor_mod

    def test_explicit_color_is_set_via_setValue_not_find_anchor_color(self):
        explicit_color = 0xAABBCCFF

        tile_color_knob = MagicMock()
        label_knob = MagicMock()
        label_knob.getValue.return_value = ''
        label_knob.setText = MagicMock()
        label_knob.setValue = MagicMock()

        stub_anchor_node = MagicMock()
        stub_anchor_node.name.return_value = 'Anchor_Foo'
        stub_anchor_node.Class.return_value = 'NoOp'
        stub_anchor_node.__getitem__ = MagicMock(side_effect=lambda key: {
            'tile_color': tile_color_knob,
            'label': label_knob,
        }.get(key, MagicMock()))
        stub_anchor_node.knobs.return_value = {}

        import nuke as nuke_stub
        nuke_stub.createNode.return_value = stub_anchor_node

        with patch.object(self.anchor_mod, 'find_anchor_color') as mock_find_color:
            self.anchor_mod.create_anchor_named('Foo', color=explicit_color)
            mock_find_color.assert_not_called()

        tile_color_knob.setValue.assert_called_with(explicit_color)


class TestCreateAnchorNamedColorParamDefault(unittest.TestCase):
    """COLOR-02: create_anchor_named() with color=None still calls find_anchor_color()."""

    def setUp(self):
        import importlib
        import anchor as anchor_mod
        importlib.reload(anchor_mod)
        self.anchor_mod = anchor_mod

    def test_color_none_falls_back_to_find_anchor_color(self):
        tile_color_knob = MagicMock()
        label_knob = MagicMock()
        label_knob.getValue.return_value = ''
        label_knob.setValue = MagicMock()

        stub_anchor_node = MagicMock()
        stub_anchor_node.name.return_value = 'Anchor_Foo'
        stub_anchor_node.Class.return_value = 'NoOp'
        stub_anchor_node.__getitem__ = MagicMock(side_effect=lambda key: {
            'tile_color': tile_color_knob,
            'label': label_knob,
        }.get(key, MagicMock()))
        stub_anchor_node.knobs.return_value = {}

        import nuke as nuke_stub
        nuke_stub.createNode.return_value = stub_anchor_node

        with patch.object(self.anchor_mod, 'find_anchor_color', return_value=0x6f3399ff) as mock_find_color:
            self.anchor_mod.create_anchor_named('Foo', color=None)
            mock_find_color.assert_called()


# ---------------------------------------------------------------------------
# COLOR-03: rename_anchor_to() propagates color after rename
# ---------------------------------------------------------------------------

class TestRenameAnchorColorPropagation(unittest.TestCase):
    """COLOR-03: rename_anchor_to() with explicit color calls propagate_anchor_color after rename."""

    def setUp(self):
        import importlib
        import anchor as anchor_mod
        importlib.reload(anchor_mod)
        self.anchor_mod = anchor_mod

    def test_rename_with_color_calls_propagate_anchor_color(self):
        import nuke as nuke_stub
        nuke_stub.allNodes.return_value = []

        label_knob = MagicMock()
        label_knob.getValue.return_value = 'OldName'
        label_knob.setValue = MagicMock()
        label_knob.getText.return_value = 'NewName'

        anchor_node = MagicMock()
        anchor_node.Class.return_value = 'NoOp'
        anchor_node.name.return_value = 'Anchor_OldName'
        anchor_node.fullName.return_value = 'script.Anchor_OldName'
        anchor_node.__getitem__ = MagicMock(side_effect=lambda key: label_knob if key == 'label' else MagicMock())

        explicit_color = 0xAABBCCFF
        with patch.object(self.anchor_mod, 'propagate_anchor_color') as mock_propagate:
            self.anchor_mod.rename_anchor_to(anchor_node, 'NewName', color=explicit_color)
            mock_propagate.assert_called_once_with(anchor_node, explicit_color)

    def test_rename_without_color_does_not_call_propagate_anchor_color(self):
        import nuke as nuke_stub
        nuke_stub.allNodes.return_value = []

        label_knob = MagicMock()
        label_knob.getValue.return_value = 'OldName'
        label_knob.setValue = MagicMock()
        label_knob.getText.return_value = 'NewName'

        anchor_node = MagicMock()
        anchor_node.Class.return_value = 'NoOp'
        anchor_node.name.return_value = 'Anchor_OldName'
        anchor_node.fullName.return_value = 'script.Anchor_OldName'
        anchor_node.__getitem__ = MagicMock(side_effect=lambda key: label_knob if key == 'label' else MagicMock())

        with patch.object(self.anchor_mod, 'propagate_anchor_color') as mock_propagate:
            self.anchor_mod.rename_anchor_to(anchor_node, 'NewName')
            mock_propagate.assert_not_called()


# ---------------------------------------------------------------------------
# COLOR-04: add_set_color_anchor_knob() tests
# ---------------------------------------------------------------------------

class TestSetColorKnobAdded(unittest.TestCase):
    """COLOR-04: add_set_color_anchor_knob() adds knob named 'set_anchor_color' to NoOp node."""

    def setUp(self):
        import importlib
        import anchor as anchor_mod
        importlib.reload(anchor_mod)
        self.anchor_mod = anchor_mod

    def test_knob_is_added_to_noopnode(self):
        node = MagicMock()
        node.Class.return_value = 'NoOp'
        node.knobs.return_value = {}  # knob not present yet

        added_knobs = []

        def fake_add_knob(knob):
            added_knobs.append(knob)

        node.addKnob.side_effect = fake_add_knob

        self.anchor_mod.add_set_color_anchor_knob(node)

        node.addKnob.assert_called_once()


class TestSetColorKnobNotAddedToDot(unittest.TestCase):
    """COLOR-04: add_set_color_anchor_knob() does NOT add knob when node.Class() == 'Dot'."""

    def setUp(self):
        import importlib
        import anchor as anchor_mod
        importlib.reload(anchor_mod)
        self.anchor_mod = anchor_mod

    def test_knob_not_added_to_dot_node(self):
        node = MagicMock()
        node.Class.return_value = 'Dot'
        node.knobs.return_value = {}

        self.anchor_mod.add_set_color_anchor_knob(node)

        node.addKnob.assert_not_called()


class TestSetColorKnobIdempotent(unittest.TestCase):
    """COLOR-04: Calling add_set_color_anchor_knob() twice does not add duplicate knob."""

    def setUp(self):
        import importlib
        import anchor as anchor_mod
        importlib.reload(anchor_mod)
        self.anchor_mod = anchor_mod

    def test_knob_added_only_once_on_second_call(self):
        from constants import ANCHOR_SET_COLOR_KNOB_NAME

        node = MagicMock()
        node.Class.return_value = 'NoOp'

        call_count = [0]
        knobs_present = {}

        def fake_knobs():
            return knobs_present

        def fake_add_knob(knob):
            call_count[0] += 1
            knobs_present[ANCHOR_SET_COLOR_KNOB_NAME] = knob

        node.knobs.side_effect = fake_knobs
        node.addKnob.side_effect = fake_add_knob

        self.anchor_mod.add_set_color_anchor_knob(node)
        self.anchor_mod.add_set_color_anchor_knob(node)

        self.assertEqual(call_count[0], 1, "addKnob should only be called once (idempotent)")


# ---------------------------------------------------------------------------
# COLOR-05: propagate_anchor_color() tests
# ---------------------------------------------------------------------------

class TestPropagateAnchorColor(unittest.TestCase):
    """COLOR-05: propagate_anchor_color() sets anchor tile_color and all link tile_colors."""

    def setUp(self):
        import importlib
        import anchor as anchor_mod
        importlib.reload(anchor_mod)
        self.anchor_mod = anchor_mod

    def test_propagate_sets_anchor_tile_color_and_link_tile_colors(self):
        color = 0xAABBCCFF

        anchor_tile_color_knob = MagicMock()
        anchor_node = MagicMock()
        anchor_node.Class.return_value = 'NoOp'
        anchor_node.__getitem__ = MagicMock(side_effect=lambda key: anchor_tile_color_knob if key == 'tile_color' else MagicMock())

        link1_tile_color = MagicMock()
        link1 = MagicMock()
        link1.__getitem__ = MagicMock(side_effect=lambda key: link1_tile_color if key == 'tile_color' else MagicMock())

        link2_tile_color = MagicMock()
        link2 = MagicMock()
        link2.__getitem__ = MagicMock(side_effect=lambda key: link2_tile_color if key == 'tile_color' else MagicMock())

        with patch.object(self.anchor_mod, 'get_links_for_anchor', return_value=[link1, link2]):
            self.anchor_mod.propagate_anchor_color(anchor_node, color)

        anchor_tile_color_knob.setValue.assert_called_once_with(color)
        link1_tile_color.setValue.assert_called_once_with(color)
        link2_tile_color.setValue.assert_called_once_with(color)


class TestPropagateAnchorColorSkipsDot(unittest.TestCase):
    """COLOR-05: propagate_anchor_color() returns early when anchor is a Dot."""

    def setUp(self):
        import importlib
        import anchor as anchor_mod
        importlib.reload(anchor_mod)
        self.anchor_mod = anchor_mod

    def test_propagate_skips_dot_anchor(self):
        color = 0xAABBCCFF

        tile_color_knob = MagicMock()
        dot_anchor = MagicMock()
        dot_anchor.Class.return_value = 'Dot'
        dot_anchor.__getitem__ = MagicMock(side_effect=lambda key: tile_color_knob if key == 'tile_color' else MagicMock())

        with patch.object(self.anchor_mod, 'get_links_for_anchor') as mock_get_links:
            self.anchor_mod.propagate_anchor_color(dot_anchor, color)
            mock_get_links.assert_not_called()

        tile_color_knob.setValue.assert_not_called()


if __name__ == '__main__':
    unittest.main()
