"""
AHK Manager — Data models.
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid
import time

from constants import DEFAULT_AHK_EXE, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT


@dataclass
class ScriptInfo:
    """Represents a single AutoHotkey script file."""

    name: str
    path: str
    folder: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "OFF"
    pid: Optional[int] = None
    runtime: float = 0.0
    start_time: Optional[float] = None
    hotkeys: list[str] = field(default_factory=list)
    description: str = ""
    error: str = ""

    def start(self, pid: int) -> None:
        """Mark this script as started with the given PID."""
        self.status = "ON"
        self.pid = pid
        self.start_time = time.time()
        self.runtime = 0.0
        self.error = ""

    def stop(self) -> None:
        """Mark this script as stopped."""
        self.status = "OFF"
        self.pid = None
        self.start_time = None
        self.runtime = 0.0

    def update_runtime(self) -> None:
        """Update the runtime based on start_time."""
        if self.start_time is not None:
            self.runtime = time.time() - self.start_time

    @property
    def runtime_formatted(self) -> str:
        """Return runtime as HH:MM:SS string."""
        if self.status == "OFF":
            return "—"
        total = int(self.runtime)
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def hotkeys_display(self) -> str:
        """Return hotkeys as comma-separated string."""
        if not self.hotkeys:
            return "—"
        return ", ".join(self.hotkeys)

    @property
    def pid_display(self) -> str:
        """Return PID as string or dash if not running."""
        if self.pid is None:
            return "—"
        return str(self.pid)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "folder": self.folder,
            "hotkeys": self.hotkeys,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScriptInfo":
        """Deserialize from dict."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            path=data["path"],
            folder=data.get("folder", ""),
            hotkeys=data.get("hotkeys", []),
            description=data.get("description", ""),
        )


@dataclass
class AppConfig:
    """Application-wide configuration."""

    ahk_exe_path: str = DEFAULT_AHK_EXE
    scan_subfolders: bool = True
    auto_start_scripts: list[str] = field(default_factory=list)
    folders: list[str] = field(default_factory=list)
    window_geometry: dict = field(default_factory=lambda: {
        "x": -1,   # -1 means center on screen
        "y": -1,
        "width": DEFAULT_WINDOW_WIDTH,
        "height": DEFAULT_WINDOW_HEIGHT,
    })

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return {
            "ahk_exe_path": self.ahk_exe_path,
            "scan_subfolders": self.scan_subfolders,
            "auto_start_scripts": self.auto_start_scripts,
            "folders": self.folders,
            "window_geometry": self.window_geometry,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        """Deserialize from dict, using defaults for missing keys."""
        config = cls()
        if "ahk_exe_path" in data:
            config.ahk_exe_path = data["ahk_exe_path"]
        if "scan_subfolders" in data:
            config.scan_subfolders = data["scan_subfolders"]
        if "auto_start_scripts" in data:
            config.auto_start_scripts = data["auto_start_scripts"]
        if "folders" in data:
            config.folders = data["folders"]
        if "window_geometry" in data:
            config.window_geometry = {
                **config.window_geometry,
                **data["window_geometry"],
            }
        return config
