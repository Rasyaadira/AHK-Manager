"""
AHK Manager — Main GUI window.

Orchestrates the layout, connects signals, and manages application state.
"""

import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    PROCESS_CHECK_INTERVAL_MS,
    RUNTIME_UPDATE_INTERVAL_MS,
    SPLITTER_RATIO,
    get_app_dir,
)
from config_manager import ConfigManager
from models import AppConfig, ScriptInfo
from script_manager import ScriptManager
from ahk_parser import scan_and_parse_folder
from widgets.toolbar import ToolBar
from widgets.script_table import ScriptTable
from widgets.log_panel import LogPanel


class MainWindow(QMainWindow):
    """Main application window for AHK Manager."""

    def __init__(self):
        super().__init__()

        # ── Core services ────────────────────────────────────────────
        self._config_mgr = ConfigManager()
        self._script_mgr = ScriptManager()
        self._config: AppConfig = self._config_mgr.load()

        # ── Script data ──────────────────────────────────────────────
        self._scripts: dict[str, ScriptInfo] = {}  # id -> ScriptInfo

        # ── Setup ────────────────────────────────────────────────────
        self._setup_window()
        self._setup_ui()
        self._setup_timers()
        self._connect_signals()

        # ── Load persisted data ──────────────────────────────────────
        self._load_persisted_scripts()
        self._update_status_bar()

    # ═════════════════════════════════════════════════════════════════
    #  SETUP
    # ═════════════════════════════════════════════════════════════════

    def _setup_window(self) -> None:
        """Configure window title, size, and position."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(700, 450)

        # Restore saved geometry or use defaults
        geo = self._config.window_geometry
        w = geo.get("width", DEFAULT_WINDOW_WIDTH)
        h = geo.get("height", DEFAULT_WINDOW_HEIGHT)
        x = geo.get("x", -1)
        y = geo.get("y", -1)

        self.resize(w, h)

        if x == -1 or y == -1:
            # Center on screen
            self._center_on_screen()
        else:
            self.move(x, y)

    def _center_on_screen(self) -> None:
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            x = (screen_geo.width() - self.width()) // 2 + screen_geo.x()
            y = (screen_geo.height() - self.height()) // 2 + screen_geo.y()
            self.move(x, y)

    def _setup_ui(self) -> None:
        """Build the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────────────────
        self._toolbar = ToolBar()
        main_layout.addWidget(self._toolbar)

        # ── Splitter: Table (left) | Log Panel (right) ───────────────
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setObjectName("main_splitter")

        self._table = ScriptTable()
        self._log_panel = LogPanel()

        self._splitter.addWidget(self._table)
        self._splitter.addWidget(self._log_panel)

        # Set ratio 65:35
        total = SPLITTER_RATIO[0] + SPLITTER_RATIO[1]
        left = int(DEFAULT_WINDOW_WIDTH * SPLITTER_RATIO[0] / total)
        right = int(DEFAULT_WINDOW_WIDTH * SPLITTER_RATIO[1] / total)
        self._splitter.setSizes([left, right])

        main_layout.addWidget(self._splitter, 1)

        # ── Status Bar ───────────────────────────────────────────────
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel("")
        self._status_bar.addWidget(self._status_label)

    def _setup_timers(self) -> None:
        """Setup periodic timers for runtime updates and process checks."""
        # Runtime timer — updates every second
        self._runtime_timer = QTimer(self)
        self._runtime_timer.setInterval(RUNTIME_UPDATE_INTERVAL_MS)
        self._runtime_timer.timeout.connect(self._on_runtime_tick)
        self._runtime_timer.start()

        # Process health check — every 3 seconds
        self._health_timer = QTimer(self)
        self._health_timer.setInterval(PROCESS_CHECK_INTERVAL_MS)
        self._health_timer.timeout.connect(self._on_health_check)
        self._health_timer.start()

    def _connect_signals(self) -> None:
        """Wire up all widget signals to handler methods."""
        # Toolbar
        self._toolbar.add_folder_clicked.connect(self._on_add_folder)
        self._toolbar.refresh_clicked.connect(self._on_refresh)
        self._toolbar.start_clicked.connect(self._on_start)
        self._toolbar.stop_clicked.connect(self._on_stop)
        self._toolbar.end_task_clicked.connect(self._on_end_task)
        self._toolbar.settings_clicked.connect(self._on_settings)

        # Table selection
        self._table.script_selected.connect(self._on_script_selected)

    # ═════════════════════════════════════════════════════════════════
    #  DATA MANAGEMENT
    # ═════════════════════════════════════════════════════════════════

    def _load_persisted_scripts(self) -> None:
        """Load scripts from the saved config."""
        saved_scripts = self._config_mgr.load_scripts()
        for script in saved_scripts:
            # Re-parse to get fresh hotkey/description data
            if os.path.isfile(script.path):
                from ahk_parser import parse_hotkeys, parse_description

                script.hotkeys = parse_hotkeys(script.path)
                script.description = parse_description(script.path)

            self._scripts[script.id] = script

        self._refresh_table()

    def _add_scripts_from_folder(self, folder_path: str) -> int:
        """Scan a folder and add new scripts. Returns count of new scripts."""
        existing_paths = {s.path for s in self._scripts.values()}

        new_scripts = scan_and_parse_folder(
            folder_path, self._config.scan_subfolders
        )

        count = 0
        for script in new_scripts:
            if script.path not in existing_paths:
                self._scripts[script.id] = script
                count += 1

        # Save folder to config if not already tracked
        if folder_path not in self._config.folders:
            self._config.folders.append(folder_path)

        return count

    def _get_selected_script(self) -> ScriptInfo | None:
        """Get the currently selected script from the table."""
        script_id = self._table.get_selected_script_id()
        if script_id is None:
            return None
        return self._scripts.get(script_id)

    def _refresh_table(self) -> None:
        """Repopulate the table with current script data."""
        scripts_list = list(self._scripts.values())
        self._table.populate(scripts_list)
        self._update_status_bar()

    def _update_status_bar(self) -> None:
        """Update status bar with script counts."""
        total = len(self._scripts)
        running = sum(1 for s in self._scripts.values() if s.status == "ON")
        folders = len(self._config.folders)
        self._status_label.setText(
            f"  {total} scripts loaded  •  {running} running  •  {folders} folders"
        )

    def _save_state(self) -> None:
        """Persist current state to config file."""
        self._config_mgr.save(
            config=self._config,
            scripts=list(self._scripts.values()),
        )

    # ═════════════════════════════════════════════════════════════════
    #  TOOLBAR HANDLERS
    # ═════════════════════════════════════════════════════════════════

    def _on_add_folder(self) -> None:
        """Open folder dialog and scan for .ahk files."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder Containing .ahk Scripts"
        )
        if not folder:
            return

        count = self._add_scripts_from_folder(folder)
        self._refresh_table()
        self._save_state()

        QMessageBox.information(
            self,
            "Folder Added",
            f"Found {count} new script(s) in:\n{folder}",
        )

    def _on_refresh(self) -> None:
        """Re-scan all tracked folders and refresh the table."""
        # Re-scan all folders
        for folder in list(self._config.folders):
            if os.path.isdir(folder):
                self._add_scripts_from_folder(folder)

        # Re-parse existing scripts for updated hotkeys/description
        for script in self._scripts.values():
            if os.path.isfile(script.path):
                from ahk_parser import parse_hotkeys, parse_description

                script.hotkeys = parse_hotkeys(script.path)
                script.description = parse_description(script.path)

        self._refresh_table()
        self._save_state()
        self._update_status_bar()

    def _on_start(self) -> None:
        """Start the selected script."""
        script = self._get_selected_script()
        if script is None:
            QMessageBox.warning(self, "No Selection", "Please select a script first.")
            return

        if script.status == "ON":
            QMessageBox.information(
                self, "Already Running", f"'{script.name}' is already running."
            )
            return

        try:
            self._script_mgr.start_script(script, self._config.ahk_exe_path)
            self._table.update_script_row(script)
            self._on_script_selected(script.id)
            self._update_status_bar()
            self._save_state()
        except FileNotFoundError as e:
            script.error = str(e)
            QMessageBox.critical(self, "File Not Found", str(e))
        except RuntimeError as e:
            QMessageBox.warning(self, "Already Running", str(e))
        except OSError as e:
            script.error = str(e)
            QMessageBox.critical(self, "Error", str(e))

    def _on_stop(self) -> None:
        """Stop the selected script."""
        script = self._get_selected_script()
        if script is None:
            QMessageBox.warning(self, "No Selection", "Please select a script first.")
            return

        if script.status == "OFF":
            QMessageBox.information(
                self, "Not Running", f"'{script.name}' is not running."
            )
            return

        self._script_mgr.stop_script(script)
        self._table.update_script_row(script)
        self._on_script_selected(script.id)
        self._update_status_bar()
        self._save_state()

    def _on_end_task(self) -> None:
        """Force-end the selected script's process."""
        script = self._get_selected_script()
        if script is None:
            QMessageBox.warning(self, "No Selection", "Please select a script first.")
            return

        if script.status == "OFF":
            QMessageBox.information(
                self, "Not Running", f"'{script.name}' is not running."
            )
            return

        reply = QMessageBox.question(
            self,
            "End Task",
            f"Force-stop '{script.name}' (PID: {script.pid})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self._script_mgr.stop_script(script)
            self._table.update_script_row(script)
            self._on_script_selected(script.id)
            self._update_status_bar()
            self._save_state()

    def _on_settings(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(self._config, self)
        if dialog.exec() == QDialog.Accepted:
            self._config = dialog.get_config()
            self._save_state()

    # ═════════════════════════════════════════════════════════════════
    #  TABLE SELECTION HANDLER
    # ═════════════════════════════════════════════════════════════════

    def _on_script_selected(self, script_id: str) -> None:
        """Update the log panel when a script is selected."""
        script = self._scripts.get(script_id)
        if script:
            self._log_panel.update_info(script)

    # ═════════════════════════════════════════════════════════════════
    #  TIMER HANDLERS
    # ═════════════════════════════════════════════════════════════════

    def _on_runtime_tick(self) -> None:
        """Update runtime display for all running scripts."""
        for script in self._scripts.values():
            if script.status == "ON":
                script.update_runtime()
                self._table.update_script_row(script)

        # Also update log panel if the selected script is running
        selected = self._get_selected_script()
        if selected and selected.status == "ON":
            self._log_panel.update_info(selected)

    def _on_health_check(self) -> None:
        """Check if any running processes died unexpectedly."""
        scripts_list = list(self._scripts.values())
        changed = self._script_mgr.check_all(scripts_list)

        if changed:
            for script in changed:
                self._table.update_script_row(script)

            self._update_status_bar()

            # Update log panel if selected script changed
            selected = self._get_selected_script()
            if selected and selected in changed:
                self._log_panel.update_info(selected)

    # ═════════════════════════════════════════════════════════════════
    #  WINDOW EVENTS
    # ═════════════════════════════════════════════════════════════════

    def closeEvent(self, event) -> None:
        """Save state and stop all scripts on window close."""
        # Save window geometry
        geo = self.geometry()
        self._config_mgr.update_window_geometry(
            geo.x(), geo.y(), geo.width(), geo.height()
        )

        # Stop all running scripts
        self._script_mgr.stop_all()
        for script in self._scripts.values():
            if script.status == "ON":
                script.stop()

        # Persist
        self._save_state()
        event.accept()


# ═════════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ═════════════════════════════════════════════════════════════════════

class SettingsDialog(QDialog):
    """Modal dialog for application settings."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self._config = AppConfig.from_dict(config.to_dict())  # Work on a copy
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Settings")
        self.setMinimumSize(480, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Title ────────────────────────────────────────────────────
        title = QLabel("⚙  Application Settings")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        # ── AutoHotkey Path ──────────────────────────────────────────
        path_group = QGroupBox("AutoHotkey Executable")
        path_group.setStyleSheet(
            "QGroupBox { color: #a78bfa; font-weight: bold; border: 1px solid #3d3d56; "
            "border-radius: 6px; margin-top: 8px; padding-top: 16px; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; }"
        )
        path_layout = QHBoxLayout(path_group)

        self._ahk_path_input = QLineEdit(self._config.ahk_exe_path)
        self._ahk_path_input.setPlaceholderText("Path to AutoHotkey.exe")
        path_layout.addWidget(self._ahk_path_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_ahk)
        path_layout.addWidget(browse_btn)

        layout.addWidget(path_group)

        # ── Scanning Options ─────────────────────────────────────────
        scan_group = QGroupBox("Scanning Options")
        scan_group.setStyleSheet(
            "QGroupBox { color: #a78bfa; font-weight: bold; border: 1px solid #3d3d56; "
            "border-radius: 6px; margin-top: 8px; padding-top: 16px; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; }"
        )
        scan_layout = QVBoxLayout(scan_group)

        self._scan_subfolders_cb = QCheckBox("Scan subfolders recursively")
        self._scan_subfolders_cb.setChecked(self._config.scan_subfolders)
        scan_layout.addWidget(self._scan_subfolders_cb)

        layout.addWidget(scan_group)

        # ── Tracked Folders ──────────────────────────────────────────
        if self._config.folders:
            folders_group = QGroupBox("Tracked Folders")
            folders_group.setStyleSheet(
                "QGroupBox { color: #a78bfa; font-weight: bold; border: 1px solid #3d3d56; "
                "border-radius: 6px; margin-top: 8px; padding-top: 16px; } "
                "QGroupBox::title { subcontrol-origin: margin; left: 12px; }"
            )
            folders_layout = QVBoxLayout(folders_group)
            for folder in self._config.folders:
                folder_label = QLabel(f"  📁  {folder}")
                folder_label.setStyleSheet("color: #94a3b8; font-size: 8pt;")
                folders_layout.addWidget(folder_label)
            layout.addWidget(folders_group)

        layout.addStretch()

        # ── Buttons ──────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾  Save")
        save_btn.setProperty("btnClass", "primary")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _browse_ahk(self) -> None:
        """Open file dialog to select AutoHotkey.exe."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select AutoHotkey Executable",
            "",
            "Executable (*.exe);;All Files (*)",
        )
        if path:
            self._ahk_path_input.setText(path)

    def _save(self) -> None:
        """Apply settings and close."""
        self._config.ahk_exe_path = self._ahk_path_input.text().strip()
        self._config.scan_subfolders = self._scan_subfolders_cb.isChecked()
        self.accept()

    def get_config(self) -> AppConfig:
        """Return the (possibly modified) config."""
        return self._config
