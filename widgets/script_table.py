"""
AHK Manager — Script table widget.

Scrollable table displaying all loaded .ahk scripts with columns:
No, Name, Path, Status, Runtime, PID, Hotkeys, Description.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from constants import COLORS, FONT_FAMILY, FONT_SIZE, TABLE_COLUMNS, TABLE_ROW_HEIGHT
from models import ScriptInfo


class ScriptTable(QTableWidget):
    """Table widget for displaying AutoHotkey scripts."""

    # Emitted when a row is selected, with the script ID
    script_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("script_table")

        # Map script_id -> row index for fast lookup
        self._id_to_row: dict[str, int] = {}

        self._setup_table()

    def _setup_table(self) -> None:
        """Initialize table structure and appearance."""
        # Columns
        col_count = len(TABLE_COLUMNS)
        self.setColumnCount(col_count)
        self.setHorizontalHeaderLabels([c["label"] for c in TABLE_COLUMNS])

        # Column widths
        header = self.horizontalHeader()
        for i, col in enumerate(TABLE_COLUMNS):
            if col["key"] == "path":
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            elif col["key"] == "description":
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                self.setColumnWidth(i, col["width"])

        # Behavior
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setSortingEnabled(True)

        # Font
        font = QFont(FONT_FAMILY, FONT_SIZE)
        self.setFont(font)
        self.horizontalHeader().setFont(QFont(FONT_FAMILY, FONT_SIZE, QFont.Bold))

        # Row height
        self.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)

        # Selection signal
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self) -> None:
        """Emit script_selected signal when a row is selected."""
        row = self.currentRow()
        if row < 0:
            return

        # Get script ID from the hidden data in the first column
        item = self.item(row, 0)
        if item is not None:
            script_id = item.data(Qt.UserRole)
            if script_id:
                self.script_selected.emit(script_id)

    def get_selected_script_id(self) -> str | None:
        """Return the ID of the currently selected script, or None."""
        row = self.currentRow()
        if row < 0:
            return None
        item = self.item(row, 0)
        if item is not None:
            return item.data(Qt.UserRole)
        return None

    def populate(self, scripts: list[ScriptInfo]) -> None:
        """Clear and repopulate the table with scripts."""
        self.setSortingEnabled(False)
        self.setRowCount(0)
        self._id_to_row.clear()

        for i, script in enumerate(scripts):
            self._add_row(i, script)

        self.setSortingEnabled(True)

    def _add_row(self, row_num: int, script: ScriptInfo) -> None:
        """Add a single row to the table."""
        row = self.rowCount()
        self.insertRow(row)
        self._id_to_row[script.id] = row

        col_map = {c["key"]: idx for idx, c in enumerate(TABLE_COLUMNS)}

        # No
        no_item = QTableWidgetItem()
        no_item.setData(Qt.DisplayRole, row_num + 1)
        no_item.setData(Qt.UserRole, script.id)  # Store script ID
        no_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col_map["no"], no_item)

        # Name
        name_item = QTableWidgetItem(script.name)
        self.setItem(row, col_map["name"], name_item)

        # Path
        path_item = QTableWidgetItem(script.path)
        path_item.setToolTip(script.path)
        self.setItem(row, col_map["path"], path_item)

        # Status
        status_item = QTableWidgetItem(script.status)
        status_item.setTextAlignment(Qt.AlignCenter)
        self._style_status(status_item, script.status)
        self.setItem(row, col_map["status"], status_item)

        # Runtime
        runtime_item = QTableWidgetItem(script.runtime_formatted)
        runtime_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col_map["runtime"], runtime_item)

        # PID
        pid_item = QTableWidgetItem(script.pid_display)
        pid_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col_map["pid"], pid_item)

        # Hotkeys
        hotkey_item = QTableWidgetItem(script.hotkeys_display)
        hotkey_item.setToolTip(script.hotkeys_display)
        self.setItem(row, col_map["hotkeys"], hotkey_item)

        # Description
        desc_item = QTableWidgetItem(script.description or "—")
        desc_item.setToolTip(script.description)
        self.setItem(row, col_map["description"], desc_item)

    def update_script_row(self, script: ScriptInfo) -> None:
        """Update a single row based on the script's current state."""
        row = self._find_row(script.id)
        if row is None:
            return

        col_map = {c["key"]: idx for idx, c in enumerate(TABLE_COLUMNS)}

        # Status
        status_item = self.item(row, col_map["status"])
        if status_item:
            status_item.setText(script.status)
            self._style_status(status_item, script.status)

        # Runtime
        runtime_item = self.item(row, col_map["runtime"])
        if runtime_item:
            runtime_item.setText(script.runtime_formatted)

        # PID
        pid_item = self.item(row, col_map["pid"])
        if pid_item:
            pid_item.setText(script.pid_display)

    def _find_row(self, script_id: str) -> int | None:
        """Find the row index for a given script ID."""
        # Try cached index first
        cached = self._id_to_row.get(script_id)
        if cached is not None and cached < self.rowCount():
            item = self.item(cached, 0)
            if item and item.data(Qt.UserRole) == script_id:
                return cached

        # Fallback: linear search
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and item.data(Qt.UserRole) == script_id:
                self._id_to_row[script_id] = row
                return row

        return None

    def _style_status(self, item: QTableWidgetItem, status: str) -> None:
        """Apply color styling to a status cell."""
        if status == "ON":
            item.setForeground(QColor(COLORS["status_on"]))
        else:
            item.setForeground(QColor(COLORS["status_off"]))

        font = QFont(FONT_FAMILY, FONT_SIZE, QFont.Bold)
        item.setFont(font)
