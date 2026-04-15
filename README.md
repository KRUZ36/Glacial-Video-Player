# Glacial

A clean, minimal video player built with VLC and Python. No bloat, no ads.
![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## What it does

- Plays basically any video/audio format (mp4, mkv, avi, flac, mp3, you name it)
- Stream URLs (http, rtsp, rtmp, udp)
- Queue/library with thumbnails
- Remembers where you left off
- 10-band equalizer with presets
- Subtitle support (srt, ass, vtt)
- Multiple audio tracks
- Keyboard shortcuts for everything
- Dark UI that doesn't burn your eyes at 3am

## Install

You need Python and VLC installed. That's it.

```
pip install PyQt6 python-vlc PyQt6-QSvgWidgets
```
IMPORTANT!!! USE x64 VLC ONLY!!!!!
Make sure [VLC](https://www.videolan.org/vlc/) is installed in the default location.

## Run

```
python main.py
```

Or open a file directly:

```
python main.py "C:\path\to\video.mp4"
```

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| Left/Right | Seek 5s |
| Shift+Left/Right | Seek 30s |
| Up/Down | Volume |
| M | Mute |
| F | Fullscreen |
| Escape | Exit fullscreen |
| O | Open file |
| U | Open URL |
| L | Toggle queue |
| S | Shuffle |
| R | Repeat |
| [ / ] | Speed down/up |
| E | Equalizer |
| I | Media info |
| J | Jump to time |
| Ctrl+V | Paste URL/path |

## "Can I get an exe?"

No exe provided. Use AI to package it if you want, I'm too lazy. Just download Python like a real OG.

## License

MIT — do whatever you want with it. Give me some credit if you feel like it so I can get a job please this took forever and crashed my computer twice since Sam Altman decided to raise Ram prices and im stuck on 8Gb's after microslop decides to steal half of it to track me.