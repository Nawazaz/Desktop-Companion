# Desktop AI Companion

A floating, animated AI companion that lives on your desktop — chats with you using an LLM, remembers past conversations across sessions (RAG), opens apps on command, and runs Pomodoro-style focus timers. Built with PySide6 and Groq.

![demo](demo.gif)
<!-- Record a short screen capture of the companion running and drop it here as demo.gif -->

## Features

- **Floating, draggable character** — frameless, always-on-top, transparent window with a system tray icon
- **Mood-based expressions** — the character's face changes (idle, happy, thinking, sleepy, talking, focused) based on the conversation
- **LLM-powered chat** — conversational AI via [Groq](https://console.groq.com)
- **RAG-based long-term memory** — every conversation is stored in a local ChromaDB vector database, so the companion recalls relevant past conversations across sessions, not just within one chat
- **Tool use / app launching** — type `open chrome`, `open spotify`, etc. to launch apps directly; the app list is fully editable through the Settings window, including auto-discovering installed apps from your Start Menu
- **Pomodoro / countdown timers** — `start pomodoro` for a work+break cycle, `start timer 10` for a plain countdown, with a live countdown shown on the character
- **In-app Settings window** — customize the companion's name/personality and manage the app-launcher list without touching any code
- **Speech bubbles** — replies appear in a bubble above the character's head, not just in the terminal

## Setup

```bash
git clone https://github.com/<your-username>/desktop-companion.git
cd desktop-companion
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com).

Run it:
```bash
python main.py
```

## Building a standalone .exe

```bash
pyinstaller --noconfirm --windowed --onefile --add-data "assets;assets" --collect-all chromadb --collect-all onnxruntime --collect-all tokenizers --hidden-import=win32timezone main.py
```

Copy your `.env` file into the generated `dist/` folder alongside `main.exe` — the executable deliberately doesn't bundle your API key, so it needs to sit next to it.

## Tech stack

Python, PySide6 (Qt), Groq API, ChromaDB (RAG/vector memory), PyInstaller

## License

MIT (or your preferred license — add a LICENSE file)
