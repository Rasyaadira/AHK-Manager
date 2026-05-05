"""
AHK Manager — Toolbar widget.

Contains action buttons: Add Folder, Refresh, Start, Stop, End Task, Settings.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy


class ToolBar(QWidget):
    """Top toolbar with action buttons."""

    # ── Signals ──────────────────────────────────────────────────────
    add_folder_clicked = Signal()
    refresh_clicked = Signal()
    start_clicked = Signal()
    stop_clicked = Signal()
    end_task_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("toolbar")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # ── Action Buttons ───────────────────────────────────────────
        self.btn_add_folder = self._make_button(
            "📁  Add Folder", "btn_add_folder", primary=True
        )
        self.btn_refresh = self._make_button("🔄  Refresh", "btn_refresh")
        self.btn_start = self._make_button("▶  Start", "btn_start", accent="green")
        self.btn_stop = self._make_button("⏹  Stop", "btn_stop", accent="red")
        self.btn_end_task = self._make_button("✖  End Task", "btn_end_task", accent="red")
        self.btn_settings = self._make_button("⚙  Settings", "btn_settings")

        layout.addWidget(self.btn_add_folder)
        layout.addWidget(self.btn_refresh)
        layout.addSpacing(12)
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.btn_end_task)
        layout.addStretch()
        layout.addWidget(self.btn_settings)

        # ── Connect Signals ──────────────────────────────────────────
        self.btn_add_folder.clicked.connect(self.add_folder_clicked)
        self.btn_refresh.clicked.connect(self.refresh_clicked)
        self.btn_start.clicked.connect(self.start_clicked)
        self.btn_stop.clicked.connect(self.stop_clicked)
        self.btn_end_task.clicked.connect(self.end_task_clicked)
        self.btn_settings.clicked.connect(self.settings_clicked)

    def _make_button(
        self, text: str, name: str, primary: bool = False, accent: str = ""
    ) -> QPushButton:
        """Create a styled toolbar button."""
        btn = QPushButton(text)
        btn.setObjectName(name)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setMinimumHeight(30)

        # Apply accent class via property for QSS targeting
        if primary:
            btn.setProperty("btnClass", "primary")
        elif accent:
            btn.setProperty("btnClass", accent)

        return btn


# Need Qt import for cursor
from PySide6.QtCore import Qt
