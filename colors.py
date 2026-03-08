"""Color palette dialog and user palette helpers for the anchor color system."""

import json
import os

import nuke

try:
    if hasattr(nuke, 'NUKE_VERSION_MAJOR') and nuke.NUKE_VERSION_MAJOR >= 16:
        from PySide6 import QtCore, QtGui, QtWidgets
        from PySide6.QtCore import Qt
    else:
        from PySide2 import QtGui, QtWidgets, QtCore
        from PySide2.QtCore import Qt
except ImportError:
    QtGui = None
    QtWidgets = None
    QtCore = None
    Qt = None

from constants import USER_PALETTE_PATH


# ---------------------------------------------------------------------------
# Non-Qt helpers — always available
# ---------------------------------------------------------------------------

def load_user_palette():
    """Return the saved user color palette as a list of ints (0xRRGGBBAA format).

    Returns an empty list if the file does not exist or is invalid.
    """
    try:
        with open(USER_PALETTE_PATH) as file_handle:
            data = json.load(file_handle)
        return [int(c) for c in data if isinstance(c, (int, float))]
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return []


def save_user_palette(colors):
    """Save *colors* (list of ints) to the user palette JSON file."""
    os.makedirs(os.path.dirname(USER_PALETTE_PATH), exist_ok=True)
    with open(USER_PALETTE_PATH, 'w') as file_handle:
        json.dump(colors, file_handle)


def _get_nuke_pref_colors():
    """Return list of color ints from Nuke's Edit > Preferences > Colors.

    Returns an empty list when called outside a Nuke session.
    """
    prefs = nuke.toNode("preferences")
    if prefs is None:
        return []
    colors = []
    for knob_name in prefs.knobs():
        if knob_name.startswith("NodeColourChoice"):
            val = prefs[knob_name].value()
            if val and val != 0:
                colors.append(int(val))
    return colors


def _get_script_backdrop_colors():
    """Return list of unique backdrop tile_color ints from the current script.

    Returns an empty list when called outside a Nuke session.
    """
    seen = set()
    colors = []
    for backdrop_node in nuke.allNodes('BackdropNode'):
        color = backdrop_node['tile_color'].value()
        if color and color not in seen:
            seen.add(color)
            colors.append(color)
    return colors


# ---------------------------------------------------------------------------
# Qt color palette dialog — only defined when Qt is available
# ---------------------------------------------------------------------------

def _color_int_to_rgb(color_int):
    """Unpack a 0xRRGGBBAA int into (r, g, b) tuple."""
    red = (color_int >> 24) & 0xFF
    green = (color_int >> 16) & 0xFF
    blue = (color_int >> 8) & 0xFF
    return red, green, blue


if QtWidgets is None:
    ColorPaletteDialog = None
else:
    # Column addresses: a-z (26 columns max)
    _COLUMN_KEYS = 'abcdefghijklmnopqrstuvwxyz'
    # Row addresses: 1-9, 0 (10 rows max)
    _ROW_KEYS = '1234567890'
    _SWATCHES_PER_ROW = 8

    class ColorPaletteDialog(QtWidgets.QDialog):
        """Color palette dialog showing swatches from Nuke prefs, backdrop colors, and user palette.

        Parameters
        ----------
        initial_color : int or None
            0xRRGGBBAA color int to pre-highlight on open.
        show_name_field : bool
            If True, shows a name QLineEdit at the top (for creation/rename dialogs).
        initial_name : str
            Pre-filled value for the name field (only relevant when show_name_field=True).
        parent : QWidget or None
            Parent widget.
        """

        def __init__(self, initial_color=None, show_name_field=False, initial_name="", parent=None):
            super().__init__(parent)

            self._selected_color = initial_color
            self._hint_mode = False
            self._hint_col = None
            self._swatch_cells = []  # list of (col_index, row_index, color_int, button)
            self.chosen_name = initial_name

            # Map from (col_index, row_index) to button for hint navigation
            self._cell_map = {}

            self._build_ui(show_name_field, initial_name)

        def _build_ui(self, show_name_field, initial_name):
            self.setWindowTitle("Color Palette")
            outer_layout = QtWidgets.QVBoxLayout()
            self.setLayout(outer_layout)

            # Optional name field at top
            self._name_edit = None
            if show_name_field:
                self._name_edit = QtWidgets.QLineEdit(initial_name)
                outer_layout.addWidget(self._name_edit)

            # Swatch grid
            grid_widget = QtWidgets.QWidget()
            self._grid_layout = QtWidgets.QGridLayout()
            self._grid_layout.setSpacing(2)
            grid_widget.setLayout(self._grid_layout)
            outer_layout.addWidget(grid_widget)

            # Collect all color sources
            nuke_pref_colors = _get_nuke_pref_colors()
            backdrop_colors = _get_script_backdrop_colors()
            user_palette_colors = load_user_palette()

            all_color_groups = [
                group for group in [nuke_pref_colors, backdrop_colors, user_palette_colors]
                if group
            ]

            grid_row = 0
            col_index = 0
            row_index = 0

            for color_group in all_color_groups:
                group_col = 0
                for color_int in color_group:
                    button = QtWidgets.QPushButton()
                    button.setFixedSize(24, 24)
                    button.setFocusPolicy(Qt.NoFocus)

                    red, green, blue = _color_int_to_rgb(color_int)
                    button.setStyleSheet(
                        f"background-color: rgb({red},{green},{blue}); "
                        "border: 1px solid #555; "
                        "border-radius: 2px;"
                    )

                    # Highlight pre-selected color
                    if color_int == self._selected_color:
                        button.setStyleSheet(
                            f"background-color: rgb({red},{green},{blue}); "
                            "border: 2px solid white; "
                            "border-radius: 2px;"
                        )

                    color_to_capture = color_int
                    button.clicked.connect(lambda checked=False, c=color_to_capture: self._on_swatch_clicked(c))

                    self._grid_layout.addWidget(button, grid_row, group_col)
                    cell = (group_col, grid_row, color_int, button)
                    self._swatch_cells.append(cell)
                    self._cell_map[(group_col, grid_row)] = (color_int, button)

                    group_col += 1
                    if group_col >= _SWATCHES_PER_ROW:
                        group_col = 0
                        grid_row += 1

                # Move to next group row
                if group_col > 0:
                    grid_row += 1

            # "Custom Color..." button
            custom_button = QtWidgets.QPushButton("Custom Color...")
            custom_button.setFocusPolicy(Qt.NoFocus)
            custom_button.clicked.connect(self._on_custom_color_clicked)
            outer_layout.addWidget(custom_button)

            # Cancel button
            cancel_button = QtWidgets.QPushButton("Cancel")
            cancel_button.setFocusPolicy(Qt.NoFocus)
            cancel_button.clicked.connect(self.reject)
            outer_layout.addWidget(cancel_button)

        def _on_swatch_clicked(self, color_int):
            self._selected_color = color_int
            if self._name_edit is not None:
                self.chosen_name = self._name_edit.text()
            self.accept()

        def _on_custom_color_clicked(self):
            result = nuke.getColor()
            if result == 0:
                return
            self._selected_color = result
            if self._name_edit is not None:
                self.chosen_name = self._name_edit.text()
            self.accept()

        def selected_color_int(self):
            """Return the selected color as a 0xRRGGBBAA int, or None if cancelled."""
            return self._selected_color

        def keyPressEvent(self, event):
            key_text = event.text().lower()

            if event.key() == Qt.Key_Escape:
                event.accept()
                self.reject()
                return

            if event.key() == Qt.Key_Tab:
                self._hint_mode = not self._hint_mode
                self._hint_col = None
                self._update_hint_overlays()
                event.accept()
                return

            if self._hint_mode:
                if key_text in _COLUMN_KEYS and self._hint_col is None:
                    self._hint_col = _COLUMN_KEYS.index(key_text)
                    self._highlight_hint_column(self._hint_col)
                    event.accept()
                    return

                if key_text in _ROW_KEYS and self._hint_col is not None:
                    row_index = _ROW_KEYS.index(key_text)
                    target_cell = self._cell_map.get((self._hint_col, row_index))
                    if target_cell is not None:
                        color_int, button = target_cell
                        self._selected_color = color_int
                        if self._name_edit is not None:
                            self.chosen_name = self._name_edit.text()
                        self.accept()
                    event.accept()
                    return

                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    # Accept with currently highlighted cell if any
                    if self._selected_color is not None:
                        if self._name_edit is not None:
                            self.chosen_name = self._name_edit.text()
                        self.accept()
                    event.accept()
                    return

                event.accept()
                return

            super().keyPressEvent(event)

        def _update_hint_overlays(self):
            """Show or hide column/row address labels on swatches in hint mode."""
            for grid_col, grid_row, color_int, button in self._swatch_cells:
                if self._hint_mode:
                    col_label = _COLUMN_KEYS[grid_col] if grid_col < len(_COLUMN_KEYS) else '?'
                    row_label = _ROW_KEYS[grid_row] if grid_row < len(_ROW_KEYS) else '?'
                    button.setText(f"{col_label}{row_label}")
                else:
                    button.setText("")

        def _highlight_hint_column(self, column_index):
            """Highlight swatches in the given column when column key pressed in hint mode."""
            for grid_col, grid_row, color_int, button in self._swatch_cells:
                red, green, blue = _color_int_to_rgb(color_int)
                if grid_col == column_index:
                    button.setStyleSheet(
                        f"background-color: rgb({red},{green},{blue}); "
                        "border: 2px solid yellow; "
                        "border-radius: 2px;"
                    )
                else:
                    button.setStyleSheet(
                        f"background-color: rgb({red},{green},{blue}); "
                        "border: 1px solid #555; "
                        "border-radius: 2px;"
                    )
