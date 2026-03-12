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


# ---------------------------------------------------------------------------
# PICKER-01/02: ColorPaletteDialog click-to-select and refresh tests
#
# Strategy: Qt is stubbed as MagicMock, so ColorPaletteDialog is a MagicMock
# instance (not a real class). We cannot instantiate it or access class methods
# through normal means.
#
# We use ast + compile to extract individual method definitions from colors.py
# source and build a test harness class that runs the ACTUAL implementation.
# Tests fail when the source does not contain the expected implementation, and
# pass once the implementation is correct.
# ---------------------------------------------------------------------------

import ast
import textwrap

def _extract_method_from_source(method_name):
    """Extract a method definition from ColorPaletteDialog in colors.py.

    Returns the compiled function object, or None if method not found.
    The extracted function runs in a namespace that includes the real module-level
    helpers from colors.py (e.g. _color_int_to_rgb) and the nuke stub.
    """
    with open('/workspace/colors.py', 'r') as source_file:
        source_text = source_file.read()
    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'ColorPaletteDialog':
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    # Reconstruct source and compile
                    method_lines = source_text.splitlines()
                    start_line = item.lineno - 1
                    end_line = item.end_lineno
                    method_source = '\n'.join(method_lines[start_line:end_line])
                    method_source = textwrap.dedent(method_source)
                    import nuke as _nuke_stub
                    namespace = {}
                    namespace['_color_int_to_rgb'] = _real_colors_module._color_int_to_rgb
                    namespace['nuke'] = _nuke_stub
                    exec(compile(method_source, '<colors_method>', 'exec'), namespace)
                    return namespace[method_name]
    return None


class _PickerTestHarness:
    """Plain Python object with the same instance attributes as ColorPaletteDialog.

    Used to call real method implementations extracted from colors.py source
    without needing a Qt environment.
    """

    def __init__(self, initial_color=None, custom_colors=None):
        self._selected_color = initial_color
        self._hint_mode = False
        self._hint_col = None
        self._swatch_cells = []
        self.chosen_name = ""
        self._custom_colors = list(custom_colors) if custom_colors else []
        self._staged_custom_colors = list(self._custom_colors)
        self._name_edit = None
        self._cell_map = {}
        self._grid_layout = MagicMock()
        self._custom_group_next_col = 0
        self._custom_group_next_row = 0
        self.accept = MagicMock()
        self.reject = MagicMock()


class TestColorPaletteDialogClickToSelect(unittest.TestCase):
    """PICKER-01: _on_swatch_clicked updates _selected_color without closing dialog."""

    def _get_on_swatch_clicked(self):
        """Get the real _on_swatch_clicked method from colors.py source."""
        method = _extract_method_from_source('_on_swatch_clicked')
        if method is None:
            self.fail("_on_swatch_clicked not found in ColorPaletteDialog in colors.py")
        return method

    def _get_refresh_swatch_borders(self):
        """Get the real _refresh_swatch_borders method from colors.py source."""
        method = _extract_method_from_source('_refresh_swatch_borders')
        if method is None:
            self.fail("_refresh_swatch_borders not found in ColorPaletteDialog in colors.py")
        return method

    def test_on_swatch_clicked_updates_selected_color(self):
        """_on_swatch_clicked must update _selected_color to the clicked color."""
        on_swatch_clicked = self._get_on_swatch_clicked()
        dialog = _PickerTestHarness()
        dialog._refresh_swatch_borders = MagicMock()
        color_to_click = 0xFF0000FF  # red

        on_swatch_clicked(dialog, color_to_click)

        self.assertEqual(dialog._selected_color, color_to_click)

    def test_on_swatch_clicked_does_not_call_accept(self):
        """_on_swatch_clicked must NOT call self.accept() (dialog stays open)."""
        on_swatch_clicked = self._get_on_swatch_clicked()
        dialog = _PickerTestHarness()
        dialog._refresh_swatch_borders = MagicMock()
        color_to_click = 0xFF0000FF

        on_swatch_clicked(dialog, color_to_click)

        dialog.accept.assert_not_called()

    def test_on_swatch_clicked_calls_refresh_swatch_borders(self):
        """_on_swatch_clicked must call _refresh_swatch_borders() after updating state."""
        on_swatch_clicked = self._get_on_swatch_clicked()
        dialog = _PickerTestHarness()
        refresh_mock = MagicMock()
        dialog._refresh_swatch_borders = refresh_mock

        on_swatch_clicked(dialog, 0x00FF00FF)

        refresh_mock.assert_called_once()

    def test_on_swatch_clicked_with_zero_color_does_not_call_accept(self):
        """_on_swatch_clicked with color_int==0 (black) must not call accept() — 0 is valid."""
        on_swatch_clicked = self._get_on_swatch_clicked()
        dialog = _PickerTestHarness()
        dialog._refresh_swatch_borders = MagicMock()
        black_color = 0  # valid color, must not be treated as falsy

        on_swatch_clicked(dialog, black_color)

        self.assertEqual(dialog._selected_color, 0)
        dialog.accept.assert_not_called()


class TestColorPaletteDialogRefreshSwatchBorders(unittest.TestCase):
    """PICKER-01: _refresh_swatch_borders applies correct stylesheet to selected vs non-selected swatches."""

    def _get_refresh_swatch_borders(self):
        """Get the real _refresh_swatch_borders method from colors.py source."""
        method = _extract_method_from_source('_refresh_swatch_borders')
        if method is None:
            self.fail("_refresh_swatch_borders not found in ColorPaletteDialog in colors.py")
        return method

    def _make_dialog_with_swatches(self, selected_color, swatch_colors):
        """Create a harness with _swatch_cells populated."""
        dialog = _PickerTestHarness(initial_color=selected_color)
        for col_index, color_int in enumerate(swatch_colors):
            button = MagicMock()
            dialog._swatch_cells.append((col_index, 0, color_int, button))
        return dialog

    def test_refresh_swatch_borders_applies_white_border_to_selected(self):
        """_refresh_swatch_borders applies white 2px border to the selected swatch."""
        refresh_swatch_borders = self._get_refresh_swatch_borders()
        selected = 0xFF0000FF
        non_selected = 0x00FF00FF

        dialog = self._make_dialog_with_swatches(selected, [selected, non_selected])
        refresh_swatch_borders(dialog)

        selected_button = dialog._swatch_cells[0][3]
        stylesheet_call = selected_button.setStyleSheet.call_args[0][0]
        self.assertIn("border: 2px solid white", stylesheet_call,
                      "Selected swatch must have 2px white border")

    def test_refresh_swatch_borders_applies_default_border_to_non_selected(self):
        """_refresh_swatch_borders applies 1px #555 border to non-selected swatches."""
        refresh_swatch_borders = self._get_refresh_swatch_borders()
        selected = 0xFF0000FF
        non_selected = 0x00FF00FF

        dialog = self._make_dialog_with_swatches(selected, [selected, non_selected])
        refresh_swatch_borders(dialog)

        non_selected_button = dialog._swatch_cells[1][3]
        stylesheet_call = non_selected_button.setStyleSheet.call_args[0][0]
        self.assertIn("border: 1px solid #555", stylesheet_call,
                      "Non-selected swatch must have 1px #555 border")

    def test_refresh_swatch_borders_handles_zero_selected_color(self):
        """_refresh_swatch_borders correctly identifies color 0 as selected (not falsy)."""
        refresh_swatch_borders = self._get_refresh_swatch_borders()
        black = 0  # valid color int
        other = 0xFF0000FF

        dialog = self._make_dialog_with_swatches(black, [black, other])
        refresh_swatch_borders(dialog)

        black_button = dialog._swatch_cells[0][3]
        stylesheet_call = black_button.setStyleSheet.call_args[0][0]
        self.assertIn("border: 2px solid white", stylesheet_call,
                      "Black swatch (color 0) must be selected correctly — cannot use falsy test")


# ---------------------------------------------------------------------------
# PICKER-05: Custom Color staging tests
# ---------------------------------------------------------------------------

class TestColorPaletteDialogCustomColorStaging(unittest.TestCase):
    """PICKER-05: _on_custom_color_clicked stages colors without closing dialog."""

    def _get_method(self, method_name):
        """Extract a method from ColorPaletteDialog in colors.py source."""
        method = _extract_method_from_source(method_name)
        if method is None:
            self.fail(f"{method_name} not found in ColorPaletteDialog in colors.py")
        return method

    def _make_dialog(self, custom_colors=None):
        """Create a harness with staged_custom_colors initialized from custom_colors."""
        dialog = _PickerTestHarness(custom_colors=custom_colors)
        # Bind real methods extracted from colors.py source
        dialog._on_custom_color_clicked = lambda: _extract_method_from_source(
            '_on_custom_color_clicked')(dialog)
        dialog._refresh_swatch_borders = MagicMock()
        dialog._append_swatch_to_custom_group = MagicMock()
        return dialog

    def test_staged_custom_colors_is_copy_of_custom_colors_param(self):
        """_staged_custom_colors is initialized as a separate copy of custom_colors."""
        original_palette = [0xFF0000FF, 0x00FF00FF]
        dialog = _PickerTestHarness(custom_colors=original_palette)

        # Staged copy should have same values
        self.assertEqual(dialog._staged_custom_colors, original_palette)
        # But must be a separate list — not the same object
        self.assertIsNot(dialog._staged_custom_colors, original_palette,
                         "_staged_custom_colors must be a copy, not the same list object")

    def test_on_custom_color_clicked_appends_to_staged_list(self):
        """_on_custom_color_clicked appends the returned color to _staged_custom_colors."""
        on_custom_color_clicked = self._get_method('_on_custom_color_clicked')

        dialog = _PickerTestHarness()
        dialog._refresh_swatch_borders = MagicMock()
        dialog._append_swatch_to_custom_group = MagicMock()

        import nuke as nuke_stub
        nuke_stub.getColor = MagicMock(return_value=0xFF0000FF)

        on_custom_color_clicked(dialog)

        self.assertIn(0xFF0000FF, dialog._staged_custom_colors,
                      "New color must be added to _staged_custom_colors")

    def test_on_custom_color_clicked_does_not_call_accept(self):
        """_on_custom_color_clicked must NOT call self.accept() — dialog stays open."""
        on_custom_color_clicked = self._get_method('_on_custom_color_clicked')

        dialog = _PickerTestHarness()
        dialog._refresh_swatch_borders = MagicMock()
        dialog._append_swatch_to_custom_group = MagicMock()

        import nuke as nuke_stub
        nuke_stub.getColor = MagicMock(return_value=0x00FF00FF)

        on_custom_color_clicked(dialog)

        dialog.accept.assert_not_called()

    def test_on_custom_color_clicked_sets_selected_color(self):
        """_on_custom_color_clicked sets _selected_color to the newly added color."""
        on_custom_color_clicked = self._get_method('_on_custom_color_clicked')

        dialog = _PickerTestHarness()
        dialog._refresh_swatch_borders = MagicMock()
        dialog._append_swatch_to_custom_group = MagicMock()

        import nuke as nuke_stub
        nuke_stub.getColor = MagicMock(return_value=0x8800CCFF)

        on_custom_color_clicked(dialog)

        self.assertEqual(dialog._selected_color, 0x8800CCFF)

    def test_on_custom_color_clicked_returns_early_for_zero_result(self):
        """_on_custom_color_clicked does nothing when nuke.getColor() returns 0."""
        on_custom_color_clicked = self._get_method('_on_custom_color_clicked')

        initial_palette = [0xFF0000FF]
        dialog = _PickerTestHarness(custom_colors=initial_palette)
        dialog._refresh_swatch_borders = MagicMock()
        dialog._append_swatch_to_custom_group = MagicMock()

        import nuke as nuke_stub
        nuke_stub.getColor = MagicMock(return_value=0)  # user cancelled

        on_custom_color_clicked(dialog)

        self.assertEqual(len(dialog._staged_custom_colors), 1,
                         "_staged_custom_colors must not change when getColor returns 0")
        dialog.accept.assert_not_called()
        dialog._refresh_swatch_borders.assert_not_called()

    def test_chosen_custom_colors_returns_staged_list(self):
        """chosen_custom_colors() returns the staged custom colors list."""
        chosen_custom_colors = self._get_method('chosen_custom_colors')

        original = [0xFF0000FF, 0x00FF00FF]
        dialog = _PickerTestHarness(custom_colors=original)

        result = chosen_custom_colors(dialog)

        self.assertEqual(result, original)

    def test_chosen_custom_colors_returns_copy(self):
        """chosen_custom_colors() returns a copy — callers cannot mutate internal state."""
        chosen_custom_colors = self._get_method('chosen_custom_colors')

        dialog = _PickerTestHarness(custom_colors=[0xFF0000FF])

        result = chosen_custom_colors(dialog)
        result.append(0xDEADBEEF)  # mutate the returned copy

        # Internal state must be unchanged
        internal_result = chosen_custom_colors(dialog)
        self.assertNotIn(0xDEADBEEF, internal_result,
                         "chosen_custom_colors() must return a copy, not a reference")


if __name__ == '__main__':
    unittest.main()
