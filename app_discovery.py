"""
app_discovery.py — scans the Windows Start Menu for installed apps (.lnk
shortcuts) so the user can pick from a list instead of typing exact paths.

Requires pywin32 (pip install pywin32) to resolve shortcut targets - if
it's not installed, discover_installed_apps() just returns an empty list
rather than erroring, so the rest of the app still works fine without it.
"""
import os
import glob

START_MENU_DIRS = [
    os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), r"Microsoft\Windows\Start Menu\Programs"),
    os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
]


def discover_installed_apps():
    """Returns a sorted list of (display_name, target_path) tuples found by
    scanning Start Menu shortcuts (.lnk files) and resolving their real
    target .exe path."""
    try:
        import win32com.client
    except ImportError:
        return []

    shell = win32com.client.Dispatch("WScript.Shell")
    found = {}

    for base_dir in START_MENU_DIRS:
        if not base_dir or not os.path.isdir(base_dir):
            continue
        pattern = os.path.join(base_dir, "**", "*.lnk")
        for lnk_path in glob.glob(pattern, recursive=True):
            try:
                shortcut = shell.CreateShortCut(lnk_path)
                target = shortcut.Targetpath
                if target and target.lower().endswith(".exe") and os.path.exists(target):
                    name = os.path.splitext(os.path.basename(lnk_path))[0]
                    found[name.lower()] = (name, target)
            except Exception:
                continue  # skip any shortcut that fails to resolve

    return sorted(found.values(), key=lambda x: x[0].lower())
