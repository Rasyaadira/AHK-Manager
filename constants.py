"""
AHK Manager — Constants and default values.
"""

import os
import sys

# ─── Application Info ────────────────────────────────────────────────
APP_NAME = "AHK Manager"
APP_VERSION = "1.0.0"

# ─── Default Window Geometry ─────────────────────────────────────────
DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 500
SPLITTER_RATIO = (65, 35)  # left: table, right: log panel

# ─── Default Paths ───────────────────────────────────────────────────
# AutoHotkey v1 default install path
DEFAULT_AHK_EXE = r"C:\Program Files\AutoHotkey\AutoHotkey.exe"

# Config file location (next to main.py)
def get_app_dir() -> str:
    """Return the directory where the application is located."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_FILENAME = "config.json"

# ─── Table Columns ───────────────────────────────────────────────────
TABLE_COLUMNS = [
    {"key": "no",          "label": "No",          "width": 40},
    {"key": "name",        "label": "Name",        "width": 160},
    {"key": "path",        "label": "Path",        "width": 200},
    {"key": "status",      "label": "Status",      "width": 60},
    {"key": "runtime",     "label": "Runtime",     "width": 80},
    {"key": "pid",         "label": "PID",         "width": 60},
    {"key": "hotkeys",     "label": "Hotkeys",     "width": 120},
    {"key": "description", "label": "Description", "width": 180},
]

# ─── Theme Colors ────────────────────────────────────────────────────
COLORS = {
    "bg_primary":    "#1e1e2e",
    "bg_secondary":  "#2a2a3d",
    "bg_tertiary":   "#33334d",
    "accent":        "#7c3aed",
    "accent_hover":  "#6d28d9",
    "accent_light":  "#a78bfa",
    "text_primary":  "#e2e8f0",
    "text_secondary":"#94a3b8",
    "text_muted":    "#64748b",
    "border":        "#3d3d56",
    "status_on":     "#22c55e",
    "status_off":    "#ef4444",
    "status_on_bg":  "#052e16",
    "status_off_bg": "#450a0a",
    "row_alt":       "#242440",
    "selection":     "#4c1d95",
    "warning":       "#f59e0b",
    "error":         "#ef4444",
}

# ─── Fonts ────────────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 9           # points
FONT_SIZE_SMALL = 8
FONT_SIZE_HEADER = 11
TABLE_ROW_HEIGHT = 30   # pixels

# ─── Timer Intervals ─────────────────────────────────────────────────
RUNTIME_UPDATE_INTERVAL_MS = 1000   # 1 second
PROCESS_CHECK_INTERVAL_MS = 3000    # 3 seconds
