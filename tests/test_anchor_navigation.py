"""Tests for Phase 4 anchor navigation features (NAV-01, NAV-02, NAV-03, FIND-01).

Covers:
- NAV-01: _save_dag_position() captures zoom+center into anchor._back_position
- NAV-01: AnchorNavigatePlugin.invoke() calls _save_dag_position() before navigating
- NAV-02: navigate_back() calls nuke.zoom(saved_zoom, saved_center) and clears the slot
- NAV-02: navigate_back() is a silent no-op when _back_position is None
- FIND-01: AnchorNavigatePlugin.get_items() includes labelled BackdropNodes prefixed with Backdrops/
- FIND-01: unlabelled BackdropNodes are excluded from get_items()
- FIND-01: picker launches when only labelled Backdrops exist (no anchors)
"""

import sys
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
    """Create a minimal nuke stub for offline testing.

    Includes all knob machinery from test_anchor_color_system.py plus
    the DAG viewport methods needed for Phase 4 navigation:
      - stub.zoom: MagicMock returning 1.0 (current zoom float)
      - stub.center: MagicMock returning [0.0, 0.0] (current [x, y] list)
      - stub.exists: MagicMock returning True
      - stub.zoomToFitSelected: MagicMock
      - stub.allNodes: MagicMock returning [] by default
    """
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
    stub.exists = MagicMock(return_value=True)
    stub.delete = MagicMock()
    stub.INVISIBLE = 0
    stub.NUKE_VERSION_MAJOR = 16  # triggers PySide6 import path in anchor.py
    stub.PyScript_Knob = MagicMock(side_effect=lambda knob_name, label, script: _make_pyscript_knob(knob_name, label, script))

    # Phase 4 DAG viewport methods
    stub.zoom = MagicMock(return_value=1.0)
    stub.center = MagicMock(return_value=[0.0, 0.0])
    stub.zoomToFitSelected = MagicMock()

    return stub


def _make_pyscript_knob(knob_name, label, script):
    """Return a minimal PyScript_Knob stand-in that supports .name()."""
    knob = MagicMock()
    knob.name.return_value = knob_name
    knob._knob_name = knob_name
    return knob


_nuke_stub = make_stub_nuke_module()
sys.modules['nuke'] = _nuke_stub

_nukescripts_stub = types.ModuleType('nukescripts')
_nukescripts_stub.cut_paste_file = lambda: '/tmp/nuke_stub_clipboard.nk'
_nukescripts_stub.clear_selection_recursive = MagicMock()
sys.modules['nukescripts'] = _nukescripts_stub


# ---------------------------------------------------------------------------
# Now import anchor — functions referenced by Phase 4 tests do not exist yet.
# Tests will be RED (AttributeError) until Plans 01/02 implement them.
# ---------------------------------------------------------------------------

def _ensure_qt_stubs_support_mock_attributes():
    """Ensure Qt stub modules support auto-attribute access for the anchor tests.

    When the full test suite is discovered, earlier test files may replace
    Qt sub-module stubs with plain types.ModuleType objects that don't
    auto-create attributes on access. This helper patches them back to
    MagicMock-based stubs and ensures NUKE_VERSION_MAJOR is set.
    """
    import nuke as current_nuke
    if not hasattr(current_nuke, 'NUKE_VERSION_MAJOR'):
        current_nuke.NUKE_VERSION_MAJOR = 16

    # Ensure Phase 4 viewport stubs are present on whatever nuke stub is active
    if not hasattr(current_nuke, 'zoom') or not callable(getattr(current_nuke.zoom, 'return_value', None)):
        current_nuke.zoom = MagicMock(return_value=1.0)
    if not hasattr(current_nuke, 'center') or not isinstance(current_nuke.center, MagicMock):
        current_nuke.center = MagicMock(return_value=[0.0, 0.0])
    if not hasattr(current_nuke, 'zoomToFitSelected'):
        current_nuke.zoomToFitSelected = MagicMock()

    for module_key in ('PySide6.QtGui', 'PySide6.QtWidgets', 'PySide6.QtCore'):
        existing = sys.modules.get(module_key)
        if existing is not None and not isinstance(existing, MagicMock):
            mock_replacement = MagicMock()
            sys.modules[module_key] = mock_replacement
            parent_key = 'PySide6'
            attr_name = module_key.split('.')[-1]
            parent_stub = sys.modules.get(parent_key)
            if parent_stub is not None:
                setattr(parent_stub, attr_name, mock_replacement)


import importlib
import anchor


# ---------------------------------------------------------------------------
# NAV-01: _save_dag_position()
# ---------------------------------------------------------------------------

class TestSaveDagPosition(unittest.TestCase):
    """NAV-01: _save_dag_position() captures zoom and center into _back_position."""

    def setUp(self):
        _ensure_qt_stubs_support_mock_attributes()
        importlib.reload(anchor)
        anchor._back_position = None
        import nuke as nuke_stub
        nuke_stub.zoom.reset_mock()
        nuke_stub.zoom.return_value = 1.0
        nuke_stub.center.reset_mock()
        nuke_stub.center.return_value = [0.0, 0.0]

    def test_save_stores_zoom_and_center(self):
        """_save_dag_position() stores (zoom, center) tuple from nuke.zoom() and nuke.center()."""
        anchor._save_dag_position()
        self.assertEqual(anchor._back_position, (1.0, [0.0, 0.0]))

    def test_save_overwrites_previous_slot(self):
        """_save_dag_position() replaces any previously saved position."""
        anchor._back_position = (2.0, [1.0, 1.0])
        anchor._save_dag_position()
        self.assertEqual(anchor._back_position, (1.0, [0.0, 0.0]))


# ---------------------------------------------------------------------------
# NAV-02: navigate_back()
# ---------------------------------------------------------------------------

class TestNavigateBack(unittest.TestCase):
    """NAV-02: navigate_back() restores saved position and clears the slot."""

    def setUp(self):
        _ensure_qt_stubs_support_mock_attributes()
        importlib.reload(anchor)
        anchor._back_position = None
        import nuke as nuke_stub
        nuke_stub.zoom.reset_mock()
        nuke_stub.zoom.return_value = 1.0
        nuke_stub.center.reset_mock()
        nuke_stub.center.return_value = [0.0, 0.0]
        import nukescripts
        nukescripts.clear_selection_recursive.reset_mock()

    def test_navigate_back_restores_zoom_and_center(self):
        """navigate_back() calls nuke.zoom(saved_zoom, saved_center)."""
        anchor._back_position = (2.5, [10.0, 20.0])
        anchor.navigate_back()
        import nuke as nuke_stub
        nuke_stub.zoom.assert_called_with(2.5, [10.0, 20.0])

    def test_navigate_back_clears_slot(self):
        """navigate_back() sets _back_position to None after restoring."""
        anchor._back_position = (2.5, [10.0, 20.0])
        anchor.navigate_back()
        self.assertIsNone(anchor._back_position)

    def test_navigate_back_noop_when_no_position(self):
        """navigate_back() does not call nuke.zoom when _back_position is None."""
        anchor._back_position = None
        anchor.navigate_back()
        import nuke as nuke_stub
        self.assertEqual(nuke_stub.zoom.call_count, 0)

    def test_navigate_back_calls_clear_selection(self):
        """navigate_back() calls nukescripts.clear_selection_recursive."""
        anchor._back_position = (1.0, [0.0, 0.0])
        anchor.navigate_back()
        import nukescripts
        nukescripts.clear_selection_recursive.assert_called()


# ---------------------------------------------------------------------------
# NAV-01: AnchorNavigatePlugin.invoke() saves position before navigating
# ---------------------------------------------------------------------------

class TestInvokeSavesPosition(unittest.TestCase):
    """NAV-01: AnchorNavigatePlugin.invoke() calls _save_dag_position() before navigating."""

    def setUp(self):
        _ensure_qt_stubs_support_mock_attributes()
        importlib.reload(anchor)
        anchor._back_position = None
        import nuke as nuke_stub
        nuke_stub.zoom.reset_mock()
        nuke_stub.zoom.return_value = 1.0
        nuke_stub.center.reset_mock()
        nuke_stub.center.return_value = [0.0, 0.0]
        nuke_stub.exists.reset_mock()
        nuke_stub.exists.return_value = True

    def test_invoke_saves_position_before_navigating_anchor(self):
        """invoke() calls _save_dag_position before navigate_to_anchor for non-BackdropNode."""
        call_order = []

        stub_anchor_node = MagicMock()
        stub_anchor_node.name.return_value = 'Anchor_Foo'
        stub_anchor_node.Class.return_value = 'NoOp'

        plugin = anchor.AnchorNavigatePlugin()

        with patch.object(anchor, '_save_dag_position', side_effect=lambda: call_order.append('save')) as mock_save, \
             patch.object(anchor, 'navigate_to_anchor', side_effect=lambda node: call_order.append('navigate')) as mock_navigate:
            plugin.invoke({'menuobj': stub_anchor_node})

        mock_save.assert_called_once()
        mock_navigate.assert_called_once_with(stub_anchor_node)
        self.assertLess(call_order.index('save'), call_order.index('navigate'),
                        "_save_dag_position must be called before navigate_to_anchor")

    def test_invoke_saves_position_before_navigating_backdrop(self):
        """invoke() calls _save_dag_position and then navigate_to_backdrop for BackdropNode."""
        call_order = []

        stub_backdrop_node = MagicMock()
        stub_backdrop_node.name.return_value = 'BackdropNode1'
        stub_backdrop_node.Class.return_value = 'BackdropNode'

        plugin = anchor.AnchorNavigatePlugin()

        with patch.object(anchor, '_save_dag_position', side_effect=lambda: call_order.append('save')) as mock_save, \
             patch.object(anchor, 'navigate_to_backdrop', side_effect=lambda node: call_order.append('navigate_bd')) as mock_navigate_bd:
            plugin.invoke({'menuobj': stub_backdrop_node})

        mock_save.assert_called_once()
        mock_navigate_bd.assert_called_once_with(stub_backdrop_node)
        self.assertLess(call_order.index('save'), call_order.index('navigate_bd'),
                        "_save_dag_position must be called before navigate_to_backdrop")


# ---------------------------------------------------------------------------
# FIND-01: AnchorNavigatePlugin.get_items() includes labelled BackdropNodes
# ---------------------------------------------------------------------------

class TestGetItemsIncludesBackdrops(unittest.TestCase):
    """FIND-01: get_items() includes labelled BackdropNodes with Backdrops/ prefix."""

    def setUp(self):
        _ensure_qt_stubs_support_mock_attributes()
        importlib.reload(anchor)
        import nuke as nuke_stub
        nuke_stub.allNodes.reset_mock()
        nuke_stub.allNodes.return_value = []

    def _make_stub_backdrop(self, label_value):
        """Return a StubNode acting as BackdropNode with the given label."""
        import nuke as nuke_stub
        label_knob = nuke_stub.StubKnob(label_value)
        knobs = {'label': label_knob}
        return nuke_stub.StubNode(name='BackdropNode1', node_class='BackdropNode', knobs_dict=knobs)

    def _make_stub_anchor(self, name):
        """Return a StubNode acting as a NoOp anchor with the ANCHOR_PREFIX."""
        import nuke as nuke_stub
        from constants import ANCHOR_PREFIX
        full_name = ANCHOR_PREFIX + name
        knobs = {
            'label': nuke_stub.StubKnob(name),
            'anchor': nuke_stub.StubKnob('anchor'),
        }
        return nuke_stub.StubNode(name=full_name, node_class='NoOp', knobs_dict=knobs)

    def test_get_items_includes_labelled_backdrop(self):
        """get_items() includes an item with menupath 'Backdrops/GradeStack' for labelled backdrop."""
        labelled_backdrop = self._make_stub_backdrop('GradeStack')

        def _allNodes_side_effect(class_name=None):
            if class_name == 'BackdropNode':
                return [labelled_backdrop]
            return []

        import nuke as nuke_stub
        nuke_stub.allNodes.side_effect = _allNodes_side_effect

        plugin = anchor.AnchorNavigatePlugin()
        items = plugin.get_items()

        menupaths = [item['menupath'] for item in items]
        self.assertIn('Backdrops/GradeStack', menupaths)

    def test_get_items_excludes_unlabelled_backdrop(self):
        """get_items() excludes BackdropNodes with an empty label."""
        unlabelled_backdrop = self._make_stub_backdrop('')

        def _allNodes_side_effect(class_name=None):
            if class_name == 'BackdropNode':
                return [unlabelled_backdrop]
            return []

        import nuke as nuke_stub
        nuke_stub.allNodes.side_effect = _allNodes_side_effect

        plugin = anchor.AnchorNavigatePlugin()
        items = plugin.get_items()

        backdrop_items = [item for item in items if item['menupath'].startswith('Backdrops/')]
        self.assertEqual(backdrop_items, [])

    def test_get_items_excludes_whitespace_only_label(self):
        """get_items() excludes BackdropNodes whose label is whitespace only."""
        whitespace_backdrop = self._make_stub_backdrop('   ')

        def _allNodes_side_effect(class_name=None):
            if class_name == 'BackdropNode':
                return [whitespace_backdrop]
            return []

        import nuke as nuke_stub
        nuke_stub.allNodes.side_effect = _allNodes_side_effect

        plugin = anchor.AnchorNavigatePlugin()
        items = plugin.get_items()

        backdrop_items = [item for item in items if item['menupath'].startswith('Backdrops/')]
        self.assertEqual(backdrop_items, [])

    def test_get_items_includes_anchors_bare(self):
        """get_items() includes anchor nodes with Anchors/ prefix."""
        stub_anchor_node = self._make_stub_anchor('Foo')

        def _allNodes_side_effect(class_name=None):
            if class_name == 'BackdropNode':
                return []
            return [stub_anchor_node]

        import nuke as nuke_stub
        nuke_stub.allNodes.side_effect = _allNodes_side_effect

        plugin = anchor.AnchorNavigatePlugin()
        items = plugin.get_items()

        anchor_items = [item for item in items if item['menupath'].startswith('Anchors/')]
        self.assertTrue(len(anchor_items) >= 1,
                        f"Expected at least one Anchors/ item but got: {[i['menupath'] for i in items]}")


# ---------------------------------------------------------------------------
# FIND-01: navigate_to_backdrop()
# ---------------------------------------------------------------------------

class TestNavigateToBackdrop(unittest.TestCase):
    """FIND-01: navigate_to_backdrop() selects the BackdropNode and zooms to fit."""

    def setUp(self):
        _ensure_qt_stubs_support_mock_attributes()
        importlib.reload(anchor)
        import nuke as nuke_stub
        nuke_stub.zoomToFitSelected.reset_mock()
        import nukescripts
        nukescripts.clear_selection_recursive.reset_mock()

    def test_navigate_to_backdrop_selects_and_zooms(self):
        """navigate_to_backdrop() calls backdrop['selected'].setValue(True) and nuke.zoomToFitSelected()."""
        selected_knob = MagicMock()
        stub_backdrop = MagicMock()
        stub_backdrop.__getitem__ = MagicMock(return_value=selected_knob)

        anchor.navigate_to_backdrop(stub_backdrop)

        selected_knob.setValue.assert_called_with(True)
        import nuke as nuke_stub
        nuke_stub.zoomToFitSelected.assert_called_once()

    def test_navigate_to_backdrop_clears_selection_before_and_after(self):
        """navigate_to_backdrop() calls nukescripts.clear_selection_recursive at least twice."""
        stub_backdrop = MagicMock()
        stub_backdrop.__getitem__ = MagicMock(return_value=MagicMock())

        anchor.navigate_to_backdrop(stub_backdrop)

        import nukescripts
        self.assertGreaterEqual(nukescripts.clear_selection_recursive.call_count, 2,
                                "clear_selection_recursive must be called before and after zoom")


# ---------------------------------------------------------------------------
# FIND-01: select_anchor_and_navigate() picker launch guard
# ---------------------------------------------------------------------------

class TestPickerLaunchGuard(unittest.TestCase):
    """FIND-01: select_anchor_and_navigate() uses updated guard including labelled backdrops."""

    def setUp(self):
        _ensure_qt_stubs_support_mock_attributes()
        importlib.reload(anchor)
        import nuke as nuke_stub
        nuke_stub.allNodes.reset_mock()
        nuke_stub.allNodes.side_effect = None
        nuke_stub.allNodes.return_value = []

    def _make_stub_backdrop(self, label_value):
        """Return a MagicMock BackdropNode with the given label knob value."""
        backdrop = MagicMock()
        label_knob = MagicMock()
        label_knob.value.return_value = label_value
        backdrop.__getitem__ = MagicMock(side_effect=lambda key: label_knob if key == 'label' else MagicMock())
        return backdrop

    def test_picker_launches_when_only_backdrops_exist(self):
        """select_anchor_and_navigate() launches picker when no anchors but labelled backdrops exist."""
        labelled_backdrop = self._make_stub_backdrop('GradeStack')

        def _allNodes_side_effect(class_name=None):
            if class_name == 'BackdropNode':
                return [labelled_backdrop]
            return []

        import nuke as nuke_stub
        nuke_stub.allNodes.side_effect = _allNodes_side_effect

        # Reset any cached widget
        anchor._anchor_navigate_widget = None

        widget_mock = MagicMock()
        with patch.object(_tabtabtab_stub, 'TabTabTabWidget', return_value=widget_mock) as mock_widget_cls:
            anchor.select_anchor_and_navigate()
            mock_widget_cls.assert_called_once()

    def test_picker_suppressed_when_no_anchors_and_no_labelled_backdrops(self):
        """select_anchor_and_navigate() returns without creating widget when nothing to show."""
        def _allNodes_side_effect(class_name=None):
            return []

        import nuke as nuke_stub
        nuke_stub.allNodes.side_effect = _allNodes_side_effect

        anchor._anchor_navigate_widget = None

        with patch.object(_tabtabtab_stub, 'TabTabTabWidget') as mock_widget_cls:
            anchor.select_anchor_and_navigate()
            mock_widget_cls.assert_not_called()


if __name__ == '__main__':
    unittest.main()
