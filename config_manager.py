"""
AHK Manager — Configuration persistence.

Handles loading and saving application config to a JSON file.
"""

import json
import os
from typing import Optional

from constants import CONFIG_FILENAME, get_app_dir
from models import AppConfig, ScriptInfo


class ConfigManager:
    """Manages application configuration persistence."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            self._config_path = os.path.join(get_app_dir(), CONFIG_FILENAME)
        else:
            self._config_path = config_path

        self.config = AppConfig()
        self._scripts_data: list[dict] = []

    @property
    def config_path(self) -> str:
        return self._config_path

    def load(self) -> AppConfig:
        """
        Load configuration from the JSON file.
        Returns default config if file doesn't exist or is invalid.
        """
        if not os.path.isfile(self._config_path):
            self.config = AppConfig()
            return self.config

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError, IOError):
            self.config = AppConfig()
            return self.config

        self.config = AppConfig.from_dict(data)
        self._scripts_data = data.get("scripts", [])

        return self.config

    def save(
        self,
        config: Optional[AppConfig] = None,
        scripts: Optional[list[ScriptInfo]] = None,
    ) -> bool:
        """
        Save configuration and script data to the JSON file.

        Args:
            config: AppConfig to save. Uses current if None.
            scripts: List of ScriptInfo to persist (without runtime state).

        Returns:
            True if saved successfully, False otherwise.
        """
        if config is not None:
            self.config = config

        data = self.config.to_dict()

        if scripts is not None:
            data["scripts"] = [s.to_dict() for s in scripts]
        else:
            data["scripts"] = self._scripts_data

        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (OSError, IOError):
            return False

    def load_scripts(self) -> list[ScriptInfo]:
        """
        Load saved script entries from config.
        These are "skeleton" scripts — they have no running state.
        """
        scripts = []
        for entry in self._scripts_data:
            try:
                script = ScriptInfo.from_dict(entry)
                # Verify the file still exists
                if os.path.isfile(script.path):
                    scripts.append(script)
            except (KeyError, TypeError):
                continue
        return scripts

    def update_window_geometry(self, x: int, y: int, w: int, h: int) -> None:
        """Update the stored window geometry."""
        self.config.window_geometry = {
            "x": x,
            "y": y,
            "width": w,
            "height": h,
        }
