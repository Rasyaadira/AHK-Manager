"""
AHK Manager — Entry Point

A desktop application for managing AutoHotkey (.ahk) scripts.
Built with Python 3.10+ and PySide6.

Usage:
    python main.py
"""

import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from constants import APP_NAME, FONT_FAMILY, FONT_SIZE, get_app_dir
from gui import MainWindow


def load_stylesheet() -> str:
    """Load the QSS stylesheet from the resources directory."""
    qss_path = os.path.join(get_app_dir(), "resources", "style.qss")

    if os.path.isfile(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()

    # Fallback: return empty string if QSS not found
    print(f"[WARN] Stylesheet not found: {qss_path}")
    return ""


def main():
    """Application entry point."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")  # Fusion style works best with custom QSS

    # Set default font
    font = QFont(FONT_FAMILY, FONT_SIZE)
    app.setFont(font)

    # Load and apply stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
