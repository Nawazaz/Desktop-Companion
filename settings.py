"""
settings.py — a single JSON file (settings.json) that stores everything the
user can customize: the companion's name/personality, and the list of apps
it knows how to open. Both app_launcher.py and llm_brain.py read from this,
so editing it (through the Settings window, or by hand) changes behavior
without touching any other code.
"""
import os
import json
from paths import get_persistent_dir

SETTINGS_PATH = os.path.join(get_persistent_dir(), "settings.json")

DEFAULT_SETTINGS = {
    "companion_name": "Companion",
    "personality": "",  # extra instructions appended to the system prompt
    "apps": {
        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "calc": ["calc.exe"],
        "explorer": ["explorer.exe"],
        "file explorer": ["explorer.exe"],
        "files": ["explorer.exe"],
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "brave": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
        "epic games": [
            r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
        ],
        "riot games": [r"C:\Riot Games\Riot Client\RiotClientServices.exe"],
        "vs code": ["code"],
        "spotify": ["spotify"],
        "word": ["winword"],
        "excel": ["excel"],
        "cmd": ["cmd.exe"],
        "paint": ["mspaint.exe"],
    },
}


def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # fill in any missing keys with defaults (e.g. after an app update)
        for key, value in DEFAULT_SETTINGS.items():
            data.setdefault(key, value)
        return data
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
