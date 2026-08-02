"""
paths.py — resolves two different kinds of directories, which matter once
the app is packaged into a PyInstaller .exe:

1. BUNDLE dir - read-only resources shipped inside the .exe (like the
   sprite PNGs). PyInstaller's --onefile mode extracts these to a TEMPORARY
   folder (sys._MEIPASS) each time the app runs, and deletes it on exit.

2. PERSISTENT dir - anything that needs to survive between runs (settings,
   the RAG memory database, the .env API key file). This must NOT use the
   temporary bundle folder - it needs to live next to the actual .exe file
   on disk, or user data would silently reset every time the app closes.

When running as a plain Python script (not frozen), both just resolve to
this file's own folder, so nothing changes for local development/testing.
"""
import sys
import os


def get_bundle_dir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_persistent_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))
