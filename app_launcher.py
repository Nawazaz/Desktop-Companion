"""
app_launcher.py — opens Windows apps by friendly name, using the app list
from settings.json (editable via the Settings window, or by hand). Each app
maps to a LIST of candidate paths, since install location varies by machine.

Uses os.startfile() as the primary launch method - Windows' native "just
open this" mechanism, which correctly handles paths containing spaces
without needing to manually quote anything (unlike subprocess with
shell=True, which can misparse an unquoted path like
"C:\\Program Files\\...\\app.exe" as multiple arguments).
"""
import os
import subprocess
from settings import load_settings


def _find_key(name: str, apps: dict):
    if name in apps:
        return name
    for key in apps:
        if key in name or name in key:
            return key
    return None


def _launch(path: str) -> bool:
    """Try os.startfile first (handles spaces/paths correctly), fall back
    to a properly-quoted subprocess call for bare command names."""
    try:
        os.startfile(path)
        return True
    except OSError:
        pass
    try:
        subprocess.Popen(f'"{path}"', shell=True)
        return True
    except Exception:
        return False


def open_app(app_name: str):
    """Try to open an app by friendly name. Returns (success: bool, message: str).
    Reloads settings.json fresh each call, so edits made in the Settings
    window take effect immediately without restarting the app."""
    settings = load_settings()
    apps = settings.get("apps", {})

    name = app_name.lower().strip()
    key = _find_key(name, apps)
    candidates = apps.get(key, [])

    for path in candidates:
        if os.path.sep in path and not os.path.exists(path):
            continue
        if _launch(path):
            return True, f"Opening {app_name}!"

    # last resort - let Windows try to resolve the raw name itself
    if _launch(app_name):
        return True, f"Trying to open {app_name}!"

    return False, f"I couldn't find {app_name} anywhere — check the path in Settings."