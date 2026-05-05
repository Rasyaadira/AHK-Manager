"""
AHK Manager — Script process manager.

Manages subprocess lifecycle for AutoHotkey scripts:
  - Start scripts via subprocess.Popen
  - Stop individual scripts by PID
  - Monitor process health
  - Cleanup on application exit
"""

import os
import subprocess
from typing import Optional

from models import ScriptInfo


class ScriptManager:
    """Manages running AutoHotkey script processes."""

    def __init__(self):
        # Map script_id -> Popen object
        self._processes: dict[str, subprocess.Popen] = {}

    def start_script(self, script: ScriptInfo, ahk_exe: str) -> int:
        """
        Start an AutoHotkey script.

        Args:
            script: The ScriptInfo to start.
            ahk_exe: Path to AutoHotkey.exe.

        Returns:
            Process ID (PID) of the started script.

        Raises:
            FileNotFoundError: If ahk_exe or script file doesn't exist.
            RuntimeError: If the script is already running.
            OSError: If the process fails to start.
        """
        # Validate paths
        if not os.path.isfile(ahk_exe):
            raise FileNotFoundError(
                f"AutoHotkey executable not found: {ahk_exe}"
            )
        if not os.path.isfile(script.path):
            raise FileNotFoundError(
                f"Script file not found: {script.path}"
            )

        # Check if already running
        if script.id in self._processes:
            proc = self._processes[script.id]
            if proc.poll() is None:
                raise RuntimeError(
                    f"Script '{script.name}' is already running (PID: {proc.pid})"
                )
            else:
                # Process finished, clean up stale entry
                del self._processes[script.id]

        # Start the process
        try:
            proc = subprocess.Popen(
                [ahk_exe, script.path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as e:
            raise OSError(f"Failed to start script '{script.name}': {e}")

        self._processes[script.id] = proc

        # Update script model
        script.start(pid=proc.pid)

        return proc.pid

    def stop_script(self, script: ScriptInfo) -> bool:
        """
        Stop a running script by its ID.

        Args:
            script: The ScriptInfo to stop.

        Returns:
            True if the script was stopped, False if it wasn't running.
        """
        proc = self._processes.get(script.id)
        if proc is None:
            script.stop()
            return False

        if proc.poll() is not None:
            # Already terminated
            del self._processes[script.id]
            script.stop()
            return True

        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
        except OSError:
            pass
        finally:
            self._processes.pop(script.id, None)
            script.stop()

        return True

    def is_running(self, script: ScriptInfo) -> bool:
        """
        Check if a script's process is still alive.

        Also handles the case where a process died unexpectedly.
        """
        proc = self._processes.get(script.id)
        if proc is None:
            return False

        if proc.poll() is None:
            return True

        # Process has ended — clean up
        self._read_stderr(proc, script)
        del self._processes[script.id]
        script.stop()
        return False

    def check_all(self, scripts: list[ScriptInfo]) -> list[ScriptInfo]:
        """
        Check all scripts and return ones that died unexpectedly.

        Returns:
            List of scripts whose processes ended without explicit stop.
        """
        changed = []
        for script in scripts:
            if script.status == "ON" and not self.is_running(script):
                changed.append(script)
        return changed

    def stop_all(self) -> None:
        """Stop all running script processes. Called on app exit."""
        for script_id in list(self._processes.keys()):
            proc = self._processes[script_id]
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except (subprocess.TimeoutExpired, OSError):
                    try:
                        proc.kill()
                    except OSError:
                        pass
        self._processes.clear()

    def get_running_count(self) -> int:
        """Return the number of currently running scripts."""
        count = 0
        for proc in self._processes.values():
            if proc.poll() is None:
                count += 1
        return count

    def _read_stderr(self, proc: subprocess.Popen, script: ScriptInfo) -> None:
        """Read stderr from a finished process and store in script.error."""
        try:
            stderr_output = proc.stderr.read().decode("utf-8", errors="replace").strip()
            if stderr_output:
                script.error = stderr_output
        except (OSError, AttributeError):
            pass
