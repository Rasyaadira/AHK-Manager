"""
AHK Manager — AutoHotkey file parser.

Responsibilities:
  - Scan folders for .ahk files
  - Parse hotkey definitions from script content
  - Extract description comments from script headers
"""

import os
import re
from typing import Optional

from models import ScriptInfo

# ─── Regex Patterns ──────────────────────────────────────────────────
# Matches AHK v1 hotkeys like: ^j::, !a::, #s::, +x::, F1::, ^!k::, etc.
# Ignores lines that are comments or inside functions
HOTKEY_PATTERN = re.compile(
    r"^([#!^+<>*~$]*"                # Modifier symbols: # ! ^ + < > * ~ $
    r"(?:[a-zA-Z0-9]+"              # Key name (letters/digits)
    r"|F[0-9]{1,2}"                 # Function keys F1-F24
    r"|(?:Numpad\w+)"              # Numpad keys
    r"|(?:Space|Tab|Enter|Escape"   # Special key names
    r"|Backspace|Delete|Insert"
    r"|Home|End|PgUp|PgDn"
    r"|Up|Down|Left|Right"
    r"|CapsLock|ScrollLock|NumLock"
    r"|PrintScreen|Pause|Break)"
    r"))"
    r"::(?!:)",                     # Followed by :: but not ::: (ternary)
    re.IGNORECASE | re.MULTILINE,
)

# Matches description comments at the top of the file
# Formats: ; description: some text  OR  ; desc: some text
DESC_PATTERN = re.compile(
    r"^\s*;\s*(?:description|desc)\s*:\s*(.+)",
    re.IGNORECASE,
)


def scan_folder(folder_path: str, scan_subfolders: bool = True) -> list[str]:
    """
    Scan a folder for .ahk files.

    Args:
        folder_path: Path to the folder to scan.
        scan_subfolders: If True, also scan subdirectories recursively.

    Returns:
        List of absolute file paths to .ahk files.
    """
    ahk_files = []

    if not os.path.isdir(folder_path):
        return ahk_files

    if scan_subfolders:
        for root, _dirs, files in os.walk(folder_path):
            for filename in sorted(files):
                if filename.lower().endswith(".ahk"):
                    ahk_files.append(os.path.join(root, filename))
    else:
        try:
            for filename in sorted(os.listdir(folder_path)):
                filepath = os.path.join(folder_path, filename)
                if os.path.isfile(filepath) and filename.lower().endswith(".ahk"):
                    ahk_files.append(filepath)
        except PermissionError:
            pass

    return ahk_files


def parse_hotkeys(file_path: str) -> list[str]:
    """
    Read a .ahk file and extract hotkey definitions.

    Args:
        file_path: Path to the .ahk file.

    Returns:
        List of hotkey strings, e.g. ["^j", "!a", "#s"].
    """
    hotkeys = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, IOError):
        return hotkeys

    for match in HOTKEY_PATTERN.finditer(content):
        hotkey = match.group(1).strip()
        if hotkey and hotkey not in hotkeys:
            hotkeys.append(hotkey)

    return hotkeys


def parse_description(file_path: str) -> str:
    """
    Read the first 20 lines of a .ahk file and extract description.

    Looks for patterns like:
        ; description: script untuk auto typing
        ; desc: shortcut manager

    Args:
        file_path: Path to the .ahk file.

    Returns:
        Description string or empty string if not found.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            # Only check the first 20 lines for description
            for i, line in enumerate(f):
                if i >= 20:
                    break
                match = DESC_PATTERN.match(line)
                if match:
                    return match.group(1).strip()
    except (OSError, IOError):
        pass

    return ""


def parse_script(file_path: str, folder: str = "") -> Optional[ScriptInfo]:
    """
    Parse a single .ahk file and return a ScriptInfo object.

    Args:
        file_path: Absolute path to the .ahk file.
        folder: The parent folder that was scanned.

    Returns:
        ScriptInfo object, or None if the file doesn't exist.
    """
    if not os.path.isfile(file_path):
        return None

    name = os.path.basename(file_path)
    hotkeys = parse_hotkeys(file_path)
    description = parse_description(file_path)

    return ScriptInfo(
        name=name,
        path=file_path,
        folder=folder or os.path.dirname(file_path),
        hotkeys=hotkeys,
        description=description,
    )


def scan_and_parse_folder(
    folder_path: str, scan_subfolders: bool = True
) -> list[ScriptInfo]:
    """
    Scan a folder and parse all .ahk files found.

    Args:
        folder_path: Path to scan.
        scan_subfolders: Whether to recurse into subdirectories.

    Returns:
        List of ScriptInfo objects for each .ahk file found.
    """
    scripts = []
    file_paths = scan_folder(folder_path, scan_subfolders)

    for filepath in file_paths:
        script = parse_script(filepath, folder=folder_path)
        if script is not None:
            scripts.append(script)

    return scripts
