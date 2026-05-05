"""
AHK Manager — Log / Detail panel widget.

Displays detailed information about the currently selected script:
Name, Path, Status, PID, Runtime, Hotkeys, Description, Error.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from constants import COLORS, FONT_FAMILY, FONT_SIZE, FONT_SIZE_HEADER, FONT_SIZE_SMALL
from models import ScriptInfo


class LogPanel(QFrame):
    """Right-side panel showing selected script details."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("log_panel")
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Scroll area for content
        scroll = QScrollArea(self)
        scroll.setObjectName("log_scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)

        # Content widget inside scroll
        content = QWidget()
        content.setObjectName("log_content")
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(4)

        # ── Header ───────────────────────────────────────────────────
        self._title = QLabel("Script Details")
        self._title.setObjectName("log_title")
        self._title.setFont(QFont(FONT_FAMILY, FONT_SIZE_HEADER, QFont.Bold))
        self._layout.addWidget(self._title)

        self._separator = QFrame()
        self._separator.setFrameShape(QFrame.HLine)
        self._separator.setObjectName("log_separator")
        self._layout.addWidget(self._separator)
        self._layout.addSpacing(4)

        # ── Info Fields ──────────────────────────────────────────────
        self._fields: dict[str, QLabel] = {}

        field_defs = [
            ("name", "Name"),
            ("path", "Path"),
            ("status", "Status"),
            ("pid", "PID"),
            ("runtime", "Runtime"),
            ("hotkeys", "Hotkeys"),
            ("description", "Description"),
            ("error", "Error"),
        ]

        for key, label_text in field_defs:
            label = QLabel(label_text)
            label.setObjectName(f"log_label_{key}")
            label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SMALL, QFont.Bold))
            label.setProperty("fieldLabel", True)
            self._layout.addWidget(label)

            value = QLabel("—")
            value.setObjectName(f"log_value_{key}")
            value.setFont(QFont(FONT_FAMILY, FONT_SIZE))
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value.setProperty("fieldValue", True)
            self._layout.addWidget(value)

            self._layout.addSpacing(6)
            self._fields[key] = value

        self._layout.addStretch()

        scroll.setWidget(content)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Start with empty state
        self._show_empty()

    def update_info(self, script: ScriptInfo) -> None:
        """Update the panel with information from the given script."""
        self._title.setText(f"📋  {script.name}")

        self._fields["name"].setText(script.name)
        self._fields["path"].setText(script.path)

        # Status with color
        status_text = script.status
        if script.status == "ON":
            self._fields["status"].setText(f"🟢  {status_text}")
            self._fields["status"].setStyleSheet(
                f"color: {COLORS['status_on']}; font-weight: bold;"
            )
        else:
            self._fields["status"].setText(f"🔴  {status_text}")
            self._fields["status"].setStyleSheet(
                f"color: {COLORS['status_off']}; font-weight: bold;"
            )

        self._fields["pid"].setText(script.pid_display)
        self._fields["runtime"].setText(script.runtime_formatted)

        # Hotkeys
        if script.hotkeys:
            hotkey_lines = "\n".join(f"  • {hk}" for hk in script.hotkeys)
            self._fields["hotkeys"].setText(hotkey_lines)
        else:
            self._fields["hotkeys"].setText("No hotkeys detected")

        # Description
        self._fields["description"].setText(
            script.description if script.description else "No description"
        )

        # Error
        if script.error:
            self._fields["error"].setText(f"⚠  {script.error}")
            self._fields["error"].setStyleSheet(
                f"color: {COLORS['error']};"
            )
        else:
            self._fields["error"].setText("—")
            self._fields["error"].setStyleSheet("")

    def clear(self) -> None:
        """Reset the panel to empty state."""
        self._show_empty()

    def _show_empty(self) -> None:
        """Show placeholder content."""
        self._title.setText("Script Details")
        for key, label in self._fields.items():
            label.setText("—")
            label.setStyleSheet("")
