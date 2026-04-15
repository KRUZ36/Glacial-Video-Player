# Glacial — Setup Guide

A clean, glass-aesthetic media player built on libVLC + PyQt6.

---

## Prerequisites

1. **Python 3.10+** — https://python.org
2. **VLC Media Player (64-bit)** — https://videolan.org
   - Must be the full VLC install, not the Windows Store version
   - Make sure it's 64-bit if your Python is 64-bit

---

## Install

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt
```

---

## Run

```bash
python main.py

# Or open a file directly:
python main.py "C:\path\to\video.mp4"
```

---

## Controls

| Action | Shortcut |
|--------|----------|
| Play / Pause | `Space` |
| Seek back 5s | `←` |
| Seek forward 5s | `→` |
| Volume up | `↑` |
| Volume down | `↓` |
| Fullscreen | `F` |
| Exit fullscreen | `Esc` |
| Open file | `O` |
| Toggle library | Click 📚 in title bar |

---

## Features

- **Library panel** — persists between sessions (`~/.glacial_library.json`)
- **Drag & drop** — onto the video area or library panel
- **Frameless window** — drag the title bar to move
- **All VLC formats** — mp4, mkv, avi, mov, mp3, flac, and everything else VLC supports
- **Shuffle & repeat** controls
- **Keyboard shortcuts** throughout

---

## Package as .exe (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Glacial main.py
# Output in dist/Glacial.exe
```

---

## Troubleshooting

**VLC not found:**
Make sure VLC is installed at `C:\Program Files\VideoLAN\VLC\` (default path).
python-vlc looks there automatically on Windows.

**Black screen / no video:**
Try running `python main.py` from a terminal to see error output.
Make sure your VLC and Python are both 64-bit.

**PyQt6 SVG error:**
Install the SVG module: `pip install PyQt6-Qt6 PyQt6-sip`
If SVG icons fail, the player still works — icons just won't render.
