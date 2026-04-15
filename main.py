# -*- coding: utf-8 -*-
import sys, os

# VLC DLL
if sys.platform == 'win32':
    for _p in [r"C:\Program Files\VideoLAN\VLC",
               r"C:\Program Files (x86)\VideoLAN\VLC"]:
        if os.path.exists(os.path.join(_p, 'libvlc.dll')):
            os.environ['PYTHON_VLC_MODULE_PATH'] = _p
            os.environ['PATH'] = _p + os.pathsep + os.environ.get('PATH', '')
            os.add_dll_directory(_p)
            break

import vlc, json, random, hashlib, subprocess, shutil, time
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QDialog,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QFileDialog, QScrollArea, QMenu, QSpinBox, QDoubleSpinBox,
    QLineEdit, QCheckBox, QComboBox, QTabWidget, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPoint, QRectF, QThread, pyqtSignal, QByteArray, QEvent
from PyQt6.QtGui import (
    QPixmap, QColor, QPainter, QBrush, QPen, QLinearGradient,
    QCursor, QFont, QFontMetrics, QIcon, QImage,
    QKeySequence, QShortcut
)

# ── paths ─────────────────────────────────────────────────────────────────────
DATA   = Path.home() / '.glacial'
THUMBS = DATA / 'thumbs'
for _d in [DATA, THUMBS]: _d.mkdir(exist_ok=True)
LIB_F  = DATA / 'library.json'
SET_F  = DATA / 'settings.json'
POS_F  = DATA / 'positions.json'

VIDEO_EXT = {'.mp4','.mkv','.avi','.mov','.wmv','.flv','.webm','.m4v',
             '.mpg','.mpeg','.ts','.m2ts','.mts','.vob','.ogv','.3gp'}
AUDIO_EXT = {'.mp3','.flac','.aac','.ogg','.wav','.m4a','.opus','.wma',
             '.mka','.tta','.aiff','.ape'}
ALL_EXT = VIDEO_EXT | AUDIO_EXT

EQ_PRESETS = {
    "Flat":         [0]*10,
    "Rock":         [8,4,-5,-8,-3,4,8,11,11,11],
    "Pop":          [-1,4,7,8,5,0,-2,-2,-1,-1],
    "Jazz":         [0,0,0,2,4,4,3,2,2,2],
    "Classical":    [0,0,0,0,0,0,-4,-4,-4,-6],
    "Dance":        [9,7,2,0,0,-5,-7,-7,0,0],
    "Bass Boost":   [-8,9,9,5,1,-4,-8,-10,-11,-11],
    "Vocal":        [-5,-5,-5,0,4,4,0,-5,-5,-5],
    "Headphones":   [4,11,5,-3,-2,1,4,9,12,12],
}
SPEEDS  = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
ASPECTS = ["Default","4:3","16:9","16:10","2.35:1","2.39:1","1:1"]
URL_SCH = ('http://','https://','rtsp://','rtmp://','udp://','rtp://','mms://','ftp://')

# ── colors ────────────────────────────────────────────────────────────────────
BG    = '#08080a'
BG2   = '#0e0e11'
BG3   = '#141417'
CARD  = '#19191d'
CARDH = '#202025'
SEP   = 'rgba(255,255,255,0.04)'
BDR   = 'rgba(255,255,255,0.07)'
BDR2  = 'rgba(255,255,255,0.12)'
TEXT  = '#f0f0f2'
TEXT2 = 'rgba(232,232,236,0.48)'
TEXT3 = 'rgba(232,232,236,0.22)'
HL    = '#ffffff'
RED   = '#ff453a'
ICO   = '#9a9aa0'
FONT  = 'Segoe UI,sans-serif'
MONO  = 'Consolas,monospace'

# ── icon cache ────────────────────────────────────────────────────────────────
_ICACHE = {}
_SVG = {
    'play':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M8 5v14l11-7z"/></svg>',
    'pause':  '<svg viewBox="0 0 24 24"><path fill="$$" d="M6 19h4V5H6v14zm8 0h4V5h-4v14z"/></svg>',
    'prev':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M6 6h2v12H6zm3.5 6 8.5 6V6z"/></svg>',
    'next':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M6 18l8.5-6L6 6v12zm10.5-12v12h2V6h-2z"/></svg>',
    'vol3':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M3 9v6h4l5 5V4L7 9zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>',
    'vol2':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9z"/></svg>',
    'vol1':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M7 9v6h4l5 5V4l-5 5z"/></svg>',
    'vol0':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3 3 4.27l4.73 4.73H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4 9.91 6.09 12 8.18z"/></svg>',
    'full':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>',
    'unfull': '<svg viewBox="0 0 24 24"><path fill="$$" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>',
    'lib':    '<svg viewBox="0 0 24 24"><path fill="$$" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z"/></svg>',
    'add':    '<svg viewBox="0 0 24 24"><path fill="$$" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>',
    'folder': '<svg viewBox="0 0 24 24"><path fill="$$" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>',
    'eq':     '<svg viewBox="0 0 24 24"><path fill="$$" d="M10 20h4V4h-4v16zm-6 0h4v-8H4v8zM16 9v11h4V9h-4z"/></svg>',
    'sub':    '<svg viewBox="0 0 24 24"><path fill="$$" d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-9 3h2v2h-2zm0 4h2v2h-2zM8 7h2v2H8zm0 4h2v2H8zm-1 4H5v-2h2v2zm14 0H9v-2h12v2zm0-4h-2v-2h2v2zm0-4h-2V7h2v2z"/></svg>',
    'aud':    '<svg viewBox="0 0 24 24"><path fill="$$" d="M12 3v9.28A4 4 0 1 0 16 16V7h4V3h-8z"/></svg>',
    'url':    '<svg viewBox="0 0 24 24"><path fill="$$" d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7a5 5 0 0 0 0 10h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4a5 5 0 0 0 0-10z"/></svg>',
    'jump':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm.5 14.5H11V11l-2 .8-.5-1.5 3-1.3h1v7z"/></svg>',
    'info':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>',
    'shuf':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/></svg>',
    'rep':    '<svg viewBox="0 0 24 24"><path fill="$$" d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/></svg>',
    'rep1':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2v-4l-1 1V11l2-2v6h-1z"/></svg>',
    'asp':    '<svg viewBox="0 0 24 24"><path fill="$$" d="M19 12h-2v3h-3v2h5v-5zM7 9h3V7H5v5h2V9zm14-6H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H3V5h18v14z"/></svg>',
    'edit':   '<svg viewBox="0 0 24 24"><path fill="$$" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>',
    'spd':    '<svg viewBox="0 0 24 24"><path fill="$$" d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm4.2 14.2L11 13V7h1.5v5.2l4.5 2.7-1.3 1.8-.5-.7z"/></svg>',
    'min':    '<svg viewBox="0 0 24 24"><path fill="$$" d="M6 19h12v2H6z"/></svg>',
    'max':    '<svg viewBox="0 0 24 24"><path fill="$$" d="M3 3v18h18V3H3zm16 16H5V5h14v14z"/></svg>',
    'close':  '<svg viewBox="0 0 24 24"><path fill="$$" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
    'clock':  '<svg viewBox="0 0 24 24"><path fill="$$" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z"/></svg>',
}

def mk_svg(key, color=ICO):
    """Return a QSvgRenderer for the given key+color, cached."""
    k = (key, color)
    if k in _ICACHE: return _ICACHE[k]
    svg = _SVG.get(key, _SVG['info']).replace('$$', color)
    try:
        from PyQt6.QtSvg import QSvgRenderer
        r = QSvgRenderer(QByteArray(svg.encode()))
        _ICACHE[k] = r
        return r
    except Exception:
        _ICACHE[k] = None
        return None

# ── helpers ───────────────────────────────────────────────────────────────────
def fmt(ms):
    s = max(0,ms)//1000; h,r = divmod(s,3600); m,s = divmod(r,60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'

def fsize(path):
    try:
        b = Path(path).stat().st_size
        for u in ['B','KB','MB','GB']:
            if b<1024: return f'{b:.1f} {u}'
            b/=1024
        return f'{b:.1f} TB'
    except: return '--'

def is_url(s): return any(s.lower().startswith(p) for p in URL_SCH)
def thumb_for(p): return THUMBS/(hashlib.md5(p.encode()).hexdigest()+'.jpg')

def load_pos():
    try:
        if POS_F.exists(): return json.loads(POS_F.read_text(encoding='utf-8'))
    except: pass
    return {}

def save_pos(path, ms):
    if is_url(path) or ms < 3000: return
    try:
        pos = load_pos(); pos[path] = ms
        POS_F.write_text(json.dumps(pos), encoding='utf-8')
    except: pass

# ── style ─────────────────────────────────────────────────────────────────────
def mk_lbl(text='', sz=11, color=TEXT, bold=False, mono=False):
    l = QLabel(text)
    ff = MONO if mono else FONT
    fw = '600' if bold else '400'
    l.setStyleSheet(f'color:{color};font-size:{sz}px;font-weight:{fw};font-family:{ff};background:transparent;')
    return l

def mk_sep(vert=False):
    f = QFrame()
    if vert: f.setFrameShape(QFrame.Shape.VLine); f.setFixedWidth(1)
    else:    f.setFrameShape(QFrame.Shape.HLine); f.setFixedHeight(1)
    f.setStyleSheet(f'background:{SEP};border:none;')
    return f

def mk_btn(text, accent=False):
    b = QPushButton(text)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    b.setFixedHeight(32)
    if accent:
        b.setStyleSheet(f'QPushButton{{background:{HL};color:#0e0e10;border:none;border-radius:7px;'
                        f'font-size:12px;font-weight:600;padding:0 18px;font-family:{FONT};}}'
                        f'QPushButton:hover{{background:rgba(232,232,234,0.85);}}'
                        f'QPushButton:pressed{{background:rgba(232,232,234,0.65);}}')
    else:
        b.setStyleSheet(f'QPushButton{{background:{CARD};color:{TEXT2};border:1px solid {BDR};'
                        f'border-radius:7px;font-size:12px;padding:0 18px;font-family:{FONT};}}'
                        f'QPushButton:hover{{background:{CARDH};color:{TEXT};}}')
    return b

DLG_CSS = f"""
QDialog{{background:{BG3};border:1px solid {BDR2};border-radius:12px;}}
QWidget{{background:transparent;color:{TEXT};}}
QLabel{{color:{TEXT};font-size:12px;background:transparent;font-family:{FONT};}}
QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox{{
    background:{CARD};color:{TEXT};border:1px solid {BDR};border-radius:7px;
    padding:6px 10px;font-size:12px;font-family:{FONT};
}}
QLineEdit:focus,QSpinBox:focus,QDoubleSpinBox:focus{{border:1px solid {BDR2};}}
QComboBox::drop-down{{border:none;width:20px;}}
QComboBox QAbstractItemView{{background:{CARDH};color:{TEXT};border:1px solid {BDR};
    selection-background-color:rgba(255,255,255,0.08);outline:none;}}
QCheckBox{{color:{TEXT};font-size:12px;font-family:{FONT};spacing:8px;}}
QCheckBox::indicator{{width:15px;height:15px;border-radius:4px;border:1px solid {BDR};background:{CARD};}}
QCheckBox::indicator:checked{{background:{HL};border:1px solid {HL};}}
QSpinBox::up-button,QSpinBox::down-button,
QDoubleSpinBox::up-button,QDoubleSpinBox::down-button{{width:0;border:none;}}
"""
MENU_CSS = f"""
QMenu{{background:{BG3};border:1px solid {BDR2};border-radius:10px;padding:5px;
    color:{TEXT};font-size:12px;font-family:{FONT};}}
QMenu::item{{padding:7px 18px;border-radius:6px;}}
QMenu::item:selected{{background:rgba(255,255,255,0.07);}}
QMenu::separator{{height:1px;background:{SEP};margin:4px 8px;}}
"""

# ── thumbnail worker ──────────────────────────────────────────────────────────
class ThumbWorker(QThread):
    done = pyqtSignal(str, str)
    def __init__(self, path):
        super().__init__(); self.path = path
    def run(self):
        out = str(thumb_for(self.path))
        if Path(out).exists(): self.done.emit(self.path, out); return
        ff = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
        if ff:
            try:
                subprocess.run([ff,'-y','-ss','00:00:08','-i',self.path,'-frames:v','1',
                    '-vf','scale=200:112:force_original_aspect_ratio=decrease,pad=200:112:(ow-iw)/2:(oh-ih)/2:color=black',
                    '-q:v','2',out], capture_output=True, timeout=14)
                if Path(out).exists(): self.done.emit(self.path, out); return
            except: pass
        try:
            inst = vlc.Instance('--quiet')
            mp = inst.media_player_new()
            mp.set_media(inst.media_new(self.path))
            mp.play(); time.sleep(2.0)
            mp.set_position(0.12); time.sleep(0.5)
            mp.video_take_snapshot(0, out, 200, 112)
            time.sleep(0.6); mp.stop(); inst.release()
            if Path(out).exists(): self.done.emit(self.path, out)
        except: pass

# ── icon button ───────────────────────────────────────────────────────────────
class IBtn(QWidget):
    clicked = pyqtSignal()
    def __init__(self, key='', size=32, isz=16, color=ICO, radius=None):
        super().__init__()
        self._key=key; self._isz=isz; self._color=color
        self._active=False; self._act_color=HL
        self._hov=False; self._press=False
        self._r = radius if radius is not None else size//2
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    def set_active(self, v):
        if self._active!=v: self._active=v; self.update()
    def set_key(self, k):
        if self._key!=k: self._key=k; self.update()
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W,H=self.width(),self.height()
        if self._press: p.setBrush(QBrush(QColor(255,255,255,22)))
        elif self._hov: p.setBrush(QBrush(QColor(255,255,255,11)))
        else:           p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0,0,W,H,self._r,self._r)
        c = self._act_color if self._active else (TEXT if self._hov else self._color)
        renderer = mk_svg(self._key, c)
        if renderer and renderer.isValid():
            isz = self._isz
            renderer.render(p, QRectF((W-isz)/2, (H-isz)/2, isz, isz))
    def enterEvent(self,e): self._hov=True; self.update()
    def leaveEvent(self,e): self._hov=False; self._press=False; self.update()
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton: self._press=True; self.update()
    def mouseReleaseEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton and self._press:
            self._press=False; self.update()
            if self.rect().contains(e.position().toPoint()): self.clicked.emit()

# ── play button ───────────────────────────────────────────────────────────────
class PlayBtn(QWidget):
    clicked = pyqtSignal()
    def __init__(self):
        super().__init__()
        self._playing=False; self._hov=False; self._press=False
        self.setFixedSize(48,48)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    def set_playing(self, v):
        if self._playing!=v: self._playing=v; self.update()
    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W=self.width()
        if self._press:   fill=QColor(190,190,192)
        elif self._hov:   fill=QColor(255,255,255)
        else:             fill=QColor(225,225,228)
        p.setBrush(QBrush(fill)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0,0,W,W)
        k='pause' if self._playing else 'play'
        renderer=mk_svg(k,'#08080a')
        if renderer and renderer.isValid():
            isz=22; off=1 if k=='play' else 0
            renderer.render(p, QRectF((W-isz)/2+off, (W-isz)/2, isz, isz))
    def enterEvent(self,e): self._hov=True; self.update()
    def leaveEvent(self,e): self._hov=False; self._press=False; self.update()
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton: self._press=True; self.update()
    def mouseReleaseEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton and self._press:
            self._press=False; self.update()
            if self.rect().contains(e.position().toPoint()): self.clicked.emit()

# ── seek bar ──────────────────────────────────────────────────────────────────
class SeekBar(QWidget):
    seeked = pyqtSignal(float)
    def __init__(self):
        super().__init__()
        self.setFixedHeight(20)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._pos=0.0; self._buf=0.0; self._hov=-1.0; self._drag=False
        self.setMouseTracking(True)
    def set_pos(self,v):
        v=max(0.0,min(1.0,v))
        if abs(v-self._pos)>0.001: self._pos=v; self.update()
    def set_buf(self,v):
        v=max(0.0,min(1.0,v))
        if abs(v-self._buf)>0.002: self._buf=v; self.update()
    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W,cy=self.width(),self.height()//2
        active=self._hov>=0 or self._drag
        H=4 if active else 3
        p.setBrush(QBrush(QColor(255,255,255,20))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0,cy-H//2,W,H,H//2,H//2)
        bw=int(self._buf*W)
        if bw>0:
            p.setBrush(QBrush(QColor(255,255,255,42)))
            p.drawRoundedRect(0,cy-H//2,bw,H,H//2,H//2)
        pw=int(self._pos*W)
        if pw>0:
            p.setBrush(QBrush(QColor(240,240,242)))
            p.drawRoundedRect(0,cy-H//2,pw,H,H//2,H//2)
        if 0<self._hov<1:
            hx=int(self._hov*W)
            if hx>pw:
                p.setBrush(QBrush(QColor(255,255,255,25)))
                p.drawRoundedRect(pw,cy-H//2,hx-pw,H,H//2,H//2)
        if active:
            hx=int(self._pos*W)
            p.setBrush(QBrush(QColor(240,240,242))); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(hx-6,cy-6,12,12)
    def _emit(self,x): self.seeked.emit(max(0.0,min(1.0,x/max(1,self.width()))))
    def mousePressEvent(self,e): self._drag=True; self._emit(e.position().x())
    def mouseMoveEvent(self,e):
        self._hov=e.position().x()/max(1,self.width()); self.update()
        if self._drag: self._emit(e.position().x())
    def mouseReleaseEvent(self,e): self._drag=False
    def leaveEvent(self,e): self._hov=-1.0; self.update()

# ── volume bar ────────────────────────────────────────────────────────────────
class VolBar(QWidget):
    changed = pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.setFixedSize(80,20)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._v=80; self._hov=False; self._drag=False
        self.setMouseTracking(True)
    def set_vol(self,v):
        v=max(0,min(100,v))
        if v!=self._v: self._v=v; self.update()
    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W,cy=self.width(),self.height()//2
        active=self._hov or self._drag
        H=4 if active else 3; pw=int(self._v/100*W)
        p.setBrush(QBrush(QColor(255,255,255,16))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0,cy-H//2,W,H,H//2,H//2)
        if pw>0:
            p.setBrush(QBrush(QColor(255,255,255,200)))
            p.drawRoundedRect(0,cy-H//2,pw,H,H//2,H//2)
        if active:
            p.setBrush(QBrush(QColor(255,255,255))); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(pw-5,cy-5,10,10)
    def enterEvent(self,e): self._hov=True; self.update()
    def leaveEvent(self,e): self._hov=False; self.update()
    def _set(self,x):
        v=int(max(0.0,min(1.0,x/max(1,self.width())))*100)
        changed = v!=self._v
        self._v=v; self.update()
        if changed: self.changed.emit(v)
    def mousePressEvent(self,e):
        self._drag=True; self._set(e.position().x())
    def mouseMoveEvent(self,e):
        if self._drag: self._set(e.position().x())
    def mouseReleaseEvent(self,e):
        self._drag=False; self.update()
    def wheelEvent(self,e):
        d=5 if e.angleDelta().y()>0 else -5
        self._set(self._v/100*self.width()+d*self.width()/100)

# ── library card ──────────────────────────────────────────────────────────────
class LibCard(QWidget):
    play_req   = pyqtSignal(str)
    remove_req = pyqtSignal(str)
    thumb_req  = pyqtSignal(str)
    rename_req = pyqtSignal(str)
    def __init__(self, path, nick='', is_url=False, is_cur=False, pos_ms=0):
        super().__init__()
        self.path=path; self._nick=nick; self.is_url=is_url
        self._cur=is_cur; self._pos=pos_ms; self._hov=False
        self.setFixedHeight(56)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx)
        self._build()
        if not is_url:
            tp=thumb_for(path)
            if tp.exists(): self._set_px(str(tp))
            else: self.thumb_req.emit(path)
    def disp(self):
        if self._nick: return self._nick
        if self.is_url: return self.path
        return Path(self.path).stem
    def _build(self):
        lay=QHBoxLayout(self); lay.setContentsMargins(8,4,8,4); lay.setSpacing(10)
        self._thumb=QLabel(); self._thumb.setFixedSize(42,42)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ext='' if self.is_url else Path(self.path).suffix.lower()
        sym='\u266b' if ext in AUDIO_EXT else '\u25b6'
        self._thumb.setText('URL' if self.is_url else sym)
        self._thumb.setStyleSheet(f'QLabel{{background:rgba(255,255,255,0.03);border-radius:6px;color:{TEXT3};font-size:12px;}}')
        lay.addWidget(self._thumb)
        tc=QVBoxLayout(); tc.setSpacing(1); tc.setContentsMargins(0,0,0,0)
        self._nlbl=mk_lbl('',11,HL if self._cur else TEXT,bold=self._cur)
        self._slbl=mk_lbl('',9,TEXT3)
        tc.addWidget(self._nlbl); tc.addWidget(self._slbl)
        lay.addLayout(tc,1)
        self._rm=QPushButton('\u00d7'); self._rm.setFixedSize(20,20)
        self._rm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._rm.setStyleSheet(f'QPushButton{{background:transparent;border:none;border-radius:10px;color:{TEXT3};font-size:12px;}}'
                               f'QPushButton:hover{{background:rgba(255,69,58,0.15);color:{RED};}}')
        self._rm.hide(); self._rm.clicked.connect(lambda: self.remove_req.emit(self.path))
        lay.addWidget(self._rm); self._refresh()
    def _refresh(self):
        fm=QFontMetrics(self._nlbl.font())
        self._nlbl.setText(fm.elidedText(self.disp(), Qt.TextElideMode.ElideRight, 200))
        sub='Stream' if self.is_url else Path(self.path).suffix.upper().lstrip('.')
        if self._pos>0: sub+=f'  {fmt(self._pos)}'
        self._slbl.setText(sub)
    def update_pos(self,ms): self._pos=ms; self._refresh()
    def update_nick(self,nick): self._nick=nick; self._refresh()
    def set_thumb(self,tp): self._set_px(tp)
    def _set_px(self,tp):
        px=QPixmap(tp)
        if not px.isNull():
            px=px.scaled(42,42,Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                         Qt.TransformationMode.SmoothTransformation)
            x=(px.width()-42)//2; y=(px.height()-42)//2
            px=px.copy(x,y,42,42)
            self._thumb.setPixmap(px); self._thumb.setText('')
            self._thumb.setStyleSheet('border-radius:6px;background:#000;')
    def set_cur(self,v):
        self._cur=v
        c=HL if v else TEXT; fw='600' if v else '400'
        self._nlbl.setStyleSheet(f'color:{c};font-size:11px;font-weight:{fw};'
                                 f'font-family:{FONT};background:transparent;')
        self.update()
    def _ctx(self,pos):
        m=QMenu(self); m.setStyleSheet(MENU_CSS)
        m.addAction('Play').triggered.connect(lambda: self.play_req.emit(self.path))
        m.addAction('Rename / Nickname').triggered.connect(lambda: self.rename_req.emit(self.path))
        m.addSeparator()
        m.addAction('Remove').triggered.connect(lambda: self.remove_req.emit(self.path))
        m.exec(self.mapToGlobal(pos))
    def enterEvent(self,e): self._hov=True; self._rm.show(); self.update()
    def leaveEvent(self,e): self._hov=False; self._rm.hide(); self.update()
    def mouseDoubleClickEvent(self,e): self.play_req.emit(self.path)
    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r=self.rect().adjusted(2,1,-2,-1)
        if self._cur:
            p.setBrush(QBrush(QColor(255,255,255,10))); p.setPen(Qt.PenStyle.NoPen)
        elif self._hov:
            p.setBrush(QBrush(QColor(255,255,255,6))); p.setPen(Qt.PenStyle.NoPen)
        else: return
        p.drawRoundedRect(r,8,8)

# ── library ───────────────────────────────────────────────────────────────────
class Library(QWidget):
    play_req = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        self._files=[]; self._urls=[]; self._nicks={}
        self._wmap={}; self._workers={}; self._cur=''
        self._load(); self._build()
        self.setAcceptDrops(True)
    def _build(self):
        self.setObjectName('lib')
        self.setStyleSheet(f"""
            QWidget#lib{{background:{BG2};}}
            QWidget{{background:transparent;}}
            QTabBar::tab{{background:transparent;color:{TEXT3};padding:8px 14px;
                font-size:11px;font-family:{FONT};border:none;
                border-bottom:2px solid transparent;}}
            QTabBar::tab:selected{{color:{HL};border-bottom:2px solid {HL};font-weight:600;}}
            QTabBar::tab:hover{{color:{TEXT};}}
            QTabWidget::pane{{border:none;border-top:1px solid {SEP};}}
            QScrollBar:vertical{{background:transparent;width:3px;}}
            QScrollBar::handle:vertical{{background:rgba(255,255,255,0.15);border-radius:2px;min-height:20px;}}
            QScrollBar::handle:vertical:hover{{background:rgba(255,255,255,0.3);}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
            QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{{background:none;}}
        """)
        vl=QVBoxLayout(self); vl.setContentsMargins(0,0,0,0); vl.setSpacing(0)
        hdr=QWidget(); hdr.setFixedHeight(48)
        hl=QHBoxLayout(hdr); hl.setContentsMargins(14,0,8,0)
        hl.addWidget(mk_lbl('Queue',12,TEXT,bold=True)); hl.addStretch()
        for k,tip,cb in [('add','Add files',self._add_files),('folder','Add folder',self._add_folder)]:
            b=IBtn(k,28,15); b.setToolTip(tip); b.clicked.connect(cb); hl.addWidget(b)
        vl.addWidget(hdr); vl.addWidget(mk_sep())
        tabs=QTabWidget(); tabs.setDocumentMode(True); self._tabs=tabs
        self._fsc,self._flay,self._fhint=self._make_tab()
        self._fhint.setText('Drop media here\nor click + to add')
        tabs.addTab(self._fsc,'Files')
        self._usc,self._ulay,self._uhint=self._make_tab()
        self._uhint.setText('Played streams\nappear here')
        tabs.addTab(self._usc,'URLs')
        vl.addWidget(tabs,1)
        for p in self._files: self._add_fw(p)
        for u in self._urls:  self._add_uw(u)
        self._hints()
    def _make_tab(self):
        sc=QScrollArea(); sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setStyleSheet('background:transparent;border:none;')
        c=QWidget(); c.setStyleSheet('background:transparent;')
        vl=QVBoxLayout(c); vl.setContentsMargins(6,6,6,6); vl.setSpacing(1)
        hint=QLabel(); hint.setAlignment(Qt.AlignmentFlag.AlignCenter); hint.setWordWrap(True)
        hint.setStyleSheet(f'color:{TEXT3};font-size:11px;padding:28px 8px;'
                           f'font-family:{FONT};background:transparent;')
        vl.addWidget(hint); vl.addStretch(); sc.setWidget(c)
        return sc,vl,hint
    def _add_fw(self,path):
        nick=self._nicks.get(path,''); pos=load_pos().get(path,0)
        w=LibCard(path,nick,is_url=False,is_cur=(path==self._cur),pos_ms=pos)
        w.play_req.connect(self.play_req); w.remove_req.connect(self._rm_f)
        w.thumb_req.connect(self._start_thumb); w.rename_req.connect(self._rename)
        self._wmap[path]=w; self._flay.insertWidget(self._flay.count()-1,w)
    def _add_uw(self,url):
        nick=self._nicks.get(url,'')
        w=LibCard(url,nick,is_url=True,is_cur=(url==self._cur))
        w.play_req.connect(self.play_req); w.remove_req.connect(self._rm_u)
        w.rename_req.connect(self._rename)
        self._wmap[url]=w; self._ulay.insertWidget(self._ulay.count()-1,w)
    def _start_thumb(self,path):
        if path in self._workers: return
        w=ThumbWorker(path); w.done.connect(self._on_thumb)
        self._workers[path]=w; w.start()
    def _on_thumb(self,path,tp):
        if path in self._wmap: self._wmap[path].set_thumb(tp)
        self._workers.pop(path,None)
    def _rename(self,path):
        cur=self._nicks.get(path,'')
        name,ok=QInputDialog.getText(self,'Nickname','Enter nickname:',text=cur)
        if ok:
            self._nicks[path]=name
            if path in self._wmap: self._wmap[path].update_nick(name)
            self._save()
    def add_file(self,path):
        if path in self._files: return
        self._files.append(path); self._add_fw(path); self._hints(); self._save()
    def add_url(self,url):
        if url in self._urls: return
        self._urls.insert(0,url); self._add_uw(url)
        self._hints(); self._save(); self._tabs.setCurrentIndex(1)
    def _rm_f(self,p):
        if p in self._files: self._files.remove(p)
        if p in self._wmap: self._wmap.pop(p).deleteLater()
        self._hints(); self._save()
    def _rm_u(self,u):
        if u in self._urls: self._urls.remove(u)
        if u in self._wmap: self._wmap.pop(u).deleteLater()
        self._hints(); self._save()
    def set_cur(self,path):
        if self._cur in self._wmap: self._wmap[self._cur].set_cur(False)
        self._cur=path
        if path in self._wmap: self._wmap[path].set_cur(True)
    def upd_pos(self,path,ms):
        if path in self._wmap and not is_url(path): self._wmap[path].update_pos(ms)
    def get_files(self): return list(self._files)
    def _hints(self):
        self._fhint.setVisible(len(self._files)==0)
        self._uhint.setVisible(len(self._urls)==0)
    def _add_files(self):
        exts=' '.join(f'*{e}' for e in sorted(ALL_EXT))
        paths,_=QFileDialog.getOpenFileNames(self,'Add Media','',f'Media ({exts});;All (*)')
        for p in paths: self.add_file(p)
    def _add_folder(self):
        d=QFileDialog.getExistingDirectory(self,'Add Folder')
        if d:
            for f in sorted(Path(d).iterdir()):
                if f.suffix.lower() in ALL_EXT: self.add_file(str(f))
    def _load(self):
        try:
            if LIB_F.exists():
                data=json.loads(LIB_F.read_text(encoding='utf-8'))
                if isinstance(data,dict):
                    self._files=[p for p in data.get('files',[]) if Path(p).exists()]
                    self._urls=data.get('urls',[])
                    self._nicks=data.get('nicks',{})
                else:
                    self._files=[p for p in data if Path(p).exists()]
        except: pass
    def _save(self):
        try: LIB_F.write_text(json.dumps({'files':self._files,'urls':self._urls,'nicks':self._nicks}),encoding='utf-8')
        except: pass
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self,e):
        for u in e.mimeData().urls():
            p=u.toLocalFile()
            if Path(p).suffix.lower() in ALL_EXT: self.add_file(p)

# ── title bar ─────────────────────────────────────────────────────────────────
class TitleBar(QWidget):
    def __init__(self):
        super().__init__(); self.setFixedHeight(38); self._dp=None
        self.setObjectName('tb')
        self.setStyleSheet(f'QWidget#tb{{background:{BG};}}'
                           f'QWidget{{background:transparent;}}')
        lay=QHBoxLayout(self); lay.setContentsMargins(8,0,4,0); lay.setSpacing(2)
        self.lib_btn=IBtn('lib',32,17); self.lib_btn.setToolTip('Toggle queue  L')
        lay.addWidget(self.lib_btn); lay.addSpacing(6)
        t=QLabel('GLACIAL')
        t.setStyleSheet(f'color:rgba(255,255,255,0.28);font-size:10px;font-weight:700;letter-spacing:5px;'
                        f'font-family:{FONT};background:transparent;')
        lay.addWidget(t)
        self._file=mk_lbl('',10,TEXT3); self._file.setMaximumWidth(360)
        lay.addWidget(self._file); lay.addStretch()
        self.url_btn=IBtn('url',30,16); self.url_btn.setToolTip('Open URL  U')
        self.jump_btn=IBtn('jump',30,16); self.jump_btn.setToolTip('Jump  J')
        self.info_btn=IBtn('info',30,16); self.info_btn.setToolTip('Info  I')
        for b in [self.url_btn,self.jump_btn,self.info_btn]: lay.addWidget(b)
        lay.addSpacing(12)
        for key,tip,attr in [('min','Minimize','_min'),('max','Maximize','_max'),('close','Close','_cls')]:
            b=IBtn(key,size=32,isz=16,color=ICO,radius=0)
            b.setFixedSize(46,32); b.setToolTip(tip)
            setattr(self,attr,b); lay.addWidget(b)
    def set_file(self,name): self._file.setText(f'  \u00b7  {name}' if name else '')
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton:
            self._dp=e.globalPosition().toPoint()-self.window().frameGeometry().topLeft()
    def mouseMoveEvent(self,e):
        if self._dp and e.buttons()==Qt.MouseButton.LeftButton:
            self.window().move(e.globalPosition().toPoint()-self._dp)
    def mouseReleaseEvent(self,e): self._dp=None
    def mouseDoubleClickEvent(self,e):
        w=self.window(); w.showNormal() if w.isMaximized() else w.showMaximized()

# ── controls bar ──────────────────────────────────────────────────────────────
class Controls(QWidget):
    def __init__(self):
        super().__init__(); self.setFixedHeight(88)
        self.setObjectName('ctrl')
        self.setStyleSheet(f'QWidget#ctrl{{background:{BG};}}'
                           f'QWidget{{background:transparent;}}')
        vl=QVBoxLayout(self); vl.setContentsMargins(16,6,16,10); vl.setSpacing(6)
        sr=QHBoxLayout(); sr.setSpacing(8)
        self.t_cur=mk_lbl('0:00',9,TEXT3,mono=True); self.t_cur.setFixedWidth(42)
        self.t_cur.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        self.seek=SeekBar()
        self.t_tot=mk_lbl('0:00',9,TEXT3,mono=True); self.t_tot.setFixedWidth(42)
        self.t_tot.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        sr.addWidget(self.t_cur); sr.addWidget(self.seek,1); sr.addWidget(self.t_tot)
        vl.addLayout(sr)
        br=QHBoxLayout(); br.setSpacing(0)
        left=QHBoxLayout(); left.setSpacing(2)
        self.vic=IBtn('vol3',30,16); self.vic.setToolTip('Mute  M')
        self.vol=VolBar(); self.vol.setToolTip('Volume  Up/Down')
        left.addWidget(self.vic); left.addSpacing(2); left.addWidget(self.vol)
        lw=QWidget(); lw.setLayout(left); lw.setFixedWidth(112)
        br.addWidget(lw); br.addStretch(1)
        cen=QHBoxLayout(); cen.setSpacing(4)
        self.shuf=IBtn('shuf',30,16); self.shuf.setToolTip('Shuffle  S')
        self.prev=IBtn('prev',36,18); self.prev.setToolTip('Prev  Left')
        self.play=PlayBtn();          self.play.setToolTip('Play/Pause  Space')
        self.next=IBtn('next',36,18); self.next.setToolTip('Next  Right')
        self.rep=IBtn('rep',30,16);   self.rep.setToolTip('Repeat  R')
        cen.addWidget(self.shuf); cen.addSpacing(4)
        cen.addWidget(self.prev); cen.addWidget(self.play); cen.addWidget(self.next)
        cen.addSpacing(4); cen.addWidget(self.rep)
        br.addLayout(cen); br.addStretch(1)
        right=QHBoxLayout(); right.setSpacing(1)
        self.spd=mk_lbl('1x',9,TEXT3,mono=True); self.spd.setFixedWidth(26)
        self.spd.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spd.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        right.addWidget(self.spd); right.addSpacing(2)
        for k,tip,attr in [('eq','Equalizer  E','eq'),('sub','Subtitles','sub'),
                            ('aud','Audio track','aud'),('asp','Aspect ratio','asp'),
                            ('full','Fullscreen  F','ful')]:
            b=IBtn(k,30,16); b.setToolTip(tip); setattr(self,attr,b); right.addWidget(b)
        rw=QWidget(); rw.setLayout(right); rw.setFixedWidth(186)
        br.addWidget(rw)
        vl.addLayout(br)

# ── video surface ─────────────────────────────────────────────────────────────
class VideoSurface(QFrame):
    dbl=pyqtSignal(); dropped=pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setStyleSheet('background:#000000;'); self.setAcceptDrops(True)
        self._ov=QLabel(self); self._ov.setText('Drop a file or press O to open')
        self._ov.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ov.setStyleSheet(f'color:{TEXT3};font-size:12px;background:transparent;'
                               f'font-family:{MONO};')
        self._ov.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    def show_idle(self,v): self._ov.setVisible(v)
    def resizeEvent(self,e): self._ov.setGeometry(self.rect())
    def mouseDoubleClickEvent(self,e): self.dbl.emit()
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self,e):
        for u in e.mimeData().urls():
            p=u.toLocalFile()
            if Path(p).suffix.lower() in ALL_EXT: self.dropped.emit(p); return

# ── dialogs ───────────────────────────────────────────────────────────────────
class URLDialog(QDialog):
    opened=pyqtSignal(str)
    def __init__(self,prefill='',parent=None):
        super().__init__(parent); self.setWindowTitle('Open URL')
        self.setFixedSize(540,130); self.setModal(True); self.setStyleSheet(DLG_CSS)
        vl=QVBoxLayout(self); vl.setContentsMargins(22,18,22,18); vl.setSpacing(12)
        vl.addWidget(mk_lbl('URL or stream address:',11,TEXT2))
        self._u=QLineEdit(); self._u.setPlaceholderText('https://  rtsp://  rtmp://  udp://')
        self._u.setMinimumHeight(32)
        self._u.setText(prefill)
        if prefill: self._u.selectAll()
        vl.addWidget(self._u)
        row=QHBoxLayout(); row.addStretch()
        ok=mk_btn('Open',accent=True); ok.clicked.connect(self._go)
        self._u.returnPressed.connect(self._go)
        row.addWidget(ok); vl.addLayout(row)
    def _go(self):
        u=self._u.text().strip()
        if u: self.opened.emit(u); self.accept()

class JumpDialog(QDialog):
    jumped=pyqtSignal(int)
    def __init__(self,ms=0,parent=None):
        super().__init__(parent); self.setWindowTitle('Jump to Time')
        self.setFixedSize(290,125); self.setModal(True); self.setStyleSheet(DLG_CSS)
        vl=QVBoxLayout(self); vl.setContentsMargins(20,16,20,16); vl.setSpacing(10)
        vl.addWidget(mk_lbl('Jump to:',11,TEXT2))
        s=ms//1000; h,s=divmod(s,3600); m,s=divmod(s,60)
        row=QHBoxLayout(); row.setSpacing(6)
        self._h=QSpinBox(); self._h.setRange(0,99); self._h.setValue(h); self._h.setFixedWidth(52)
        self._m=QSpinBox(); self._m.setRange(0,59); self._m.setValue(m); self._m.setFixedWidth(52)
        self._s=QSpinBox(); self._s.setRange(0,59); self._s.setValue(s); self._s.setFixedWidth(52)
        for sp,lt in [(self._h,'h'),(self._m,'m'),(self._s,'s')]:
            row.addWidget(sp); row.addWidget(mk_lbl(lt,11,TEXT3))
        row.addStretch()
        ok=mk_btn('Jump',accent=True); ok.setFixedWidth(60)
        ok.clicked.connect(lambda:(
            self.jumped.emit((self._h.value()*3600+self._m.value()*60+self._s.value())*1000),
            self.accept()))
        row.addWidget(ok); vl.addLayout(row)

class EQDialog(QDialog):
    def __init__(self,mp,bands,parent=None):
        super().__init__(parent); self.mp=mp; self._bands=list(bands); self._sls=[]
        self.setWindowTitle('Equalizer'); self.setModal(False)
        self.setFixedSize(540,300); self.setStyleSheet(DLG_CSS); self._build()
    def _build(self):
        vl=QVBoxLayout(self); vl.setContentsMargins(20,16,20,16); vl.setSpacing(12)
        top=QHBoxLayout()
        self._on=QCheckBox('Enabled'); self._on.setChecked(True); self._on.toggled.connect(self._apply)
        top.addWidget(self._on); top.addStretch()
        top.addWidget(mk_lbl('Preset:',11,TEXT3)); top.addSpacing(6)
        self._pre=QComboBox(); self._pre.addItems(list(EQ_PRESETS.keys()))
        self._pre.setFixedWidth(130); self._pre.currentTextChanged.connect(self._load_pre)
        top.addWidget(self._pre); vl.addLayout(top)
        FREQS=['32','64','125','250','500','1K','2K','4K','8K','16K']
        br=QHBoxLayout(); br.setSpacing(5)
        for i,f in enumerate(FREQS):
            col=QVBoxLayout(); col.setSpacing(4); col.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vl2=mk_lbl(f'{self._bands[i]:+.0f}',9,TEXT3,mono=True)
            vl2.setFixedWidth(34); vl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sl=QSlider(Qt.Orientation.Vertical); sl.setRange(-20,20); sl.setValue(int(self._bands[i])); sl.setFixedHeight(130)
            sl.setStyleSheet(f'QSlider::groove:vertical{{width:3px;background:rgba(255,255,255,0.12);border-radius:2px;}}'
                             f'QSlider::sub-page:vertical{{background:{HL};border-radius:2px;}}'
                             f'QSlider::handle:vertical{{background:{HL};width:10px;height:10px;margin:0 -4px;border-radius:5px;}}')
            def _ch(v,idx=i,ll=vl2): self._bands[idx]=v; ll.setText(f'{v:+d}'); self._apply()
            sl.valueChanged.connect(_ch); self._sls.append(sl)
            fl=mk_lbl(f,9,TEXT3); fl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(vl2); col.addWidget(sl,0,Qt.AlignmentFlag.AlignHCenter); col.addWidget(fl)
            br.addLayout(col)
        vl.addLayout(br)
        bot=QHBoxLayout(); bot.addStretch()
        rst=mk_btn('Reset'); rst.clicked.connect(lambda: self._load_pre('Flat'))
        bot.addWidget(rst); vl.addLayout(bot)
    def _load_pre(self,name):
        for sl,v in zip(self._sls,EQ_PRESETS.get(name,[0]*10)):
            sl.blockSignals(True); sl.setValue(int(v)); sl.blockSignals(False)
        self._bands=list(EQ_PRESETS.get(name,[0]*10)); self._apply()
    def _apply(self):
        eq=vlc.libvlc_audio_equalizer_new()
        if self._on.isChecked():
            for i,v in enumerate(self._bands):
                vlc.libvlc_audio_equalizer_set_amp_at_index(eq,float(v),i)
        self.mp.set_equalizer(eq)
    def get_bands(self): return list(self._bands)

# ── main window ───────────────────────────────────────────────────────────────
class Glacial(QMainWindow):
    R_NONE=0; R_ALL=1; R_ONE=2
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Glacial')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(820,560); self.resize(1140,700)
        self.setAcceptDrops(True)
        print("  vlc init", flush=True)
        self._vlc=vlc.Instance('--quiet')
        print("  vlc instance done", flush=True)
        self.mp=self._vlc.media_player_new()
        print("  media player done", flush=True)
        self.current=''; self.playlist=[]; self.pl_idx=-1
        self._shuf=[]; self._do_shuf=False; self._repeat=self.R_NONE
        self._muted=False; self._vol=80; self._spd=SPEEDS.index(1.0)
        self._eq_bands=[0.0]*10; self._eq_dlg=None
        self._lib_vis=True; self._fs=False; self._resume=True
        self._last_save=0
        print("  load settings", flush=True)
        self._load_settings()
        print("  build UI", flush=True)
        self._build()
        print("  wire", flush=True)
        self._wire()
        print("  kb", flush=True)
        self._kb()
        print("  timer", flush=True)
        self._tmr=QTimer(); self._tmr.setInterval(500)
        self._tmr.timeout.connect(self._tick); self._tmr.start()
        print("  init done", flush=True)

    def _build(self):
        print("    build: root widget", flush=True)
        root=QWidget(); root.setObjectName('root')
        root.setStyleSheet(f'QWidget#root{{background:{BG};}}'
                           f'QWidget{{background:transparent;color:{TEXT};}}')
        self.setCentralWidget(root)
        vl=QVBoxLayout(root); vl.setContentsMargins(0,0,0,0); vl.setSpacing(0)
        print("    build: titlebar", flush=True)
        self.tb=TitleBar(); vl.addWidget(self.tb)
        print("    build: video surface", flush=True)
        body=QHBoxLayout(); body.setContentsMargins(0,0,0,0); body.setSpacing(0)
        self.video=VideoSurface(); body.addWidget(self.video,1)
        print("    build: library", flush=True)
        self.lib=Library(); body.addWidget(self.lib)
        bw=QWidget(); bw.setLayout(body); vl.addWidget(bw,1)
        print("    build: controls", flush=True)
        self.ctrl=Controls(); vl.addWidget(self.ctrl)
        print("    build: volume", flush=True)
        self.mp.audio_set_volume(self._vol)
        self.ctrl.vol.set_vol(self._vol)
        print("    build: done", flush=True)

    def _attach_vlc(self):
        """Attach VLC to video surface after window is shown."""
        try:
            wid = int(self.video.winId())
            if sys.platform == 'win32':    self.mp.set_hwnd(wid)
            elif sys.platform == 'darwin': self.mp.set_nsobject(wid)
            else:                          self.mp.set_xwindow(wid)
            print("VLC attached to window", flush=True)
        except Exception as e:
            print(f"VLC attach failed: {e}", flush=True)

    def _wire(self):
        tb=self.tb; c=self.ctrl
        tb._min.clicked.connect(self.showMinimized)
        tb._max.clicked.connect(lambda: self.showNormal() if self.isMaximized() else self.showMaximized())
        tb._cls.clicked.connect(self.close)
        tb.lib_btn.clicked.connect(self._tog_lib)
        tb.url_btn.clicked.connect(lambda: self._url_dlg())
        tb.jump_btn.clicked.connect(self._jump_dlg)
        tb.info_btn.clicked.connect(self._info_dlg)
        c.play.clicked.connect(self._play_pause)
        c.prev.clicked.connect(self._prev)
        c.next.clicked.connect(self._next)
        c.shuf.clicked.connect(self._tog_shuf)
        c.rep.clicked.connect(self._tog_rep)
        c.seek.seeked.connect(lambda v: self.mp.set_position(float(v)))
        c.vic.clicked.connect(self._tog_mute)
        c.vol.changed.connect(self._set_vol)
        c.eq.clicked.connect(self._show_eq)
        c.sub.clicked.connect(self._sub_menu)
        c.aud.clicked.connect(self._aud_menu)
        c.asp.clicked.connect(self._asp_menu)
        c.ful.clicked.connect(self._tog_fs)
        c.spd.mousePressEvent=lambda e: self._spd_menu()
        self.video.dbl.connect(self._tog_fs)
        self.video.dropped.connect(self._open_file)
        self.lib.play_req.connect(self._open_any)

    def _kb(self):
        def sh(k,fn): QShortcut(QKeySequence(k),self).activated.connect(fn)
        sh('Space',self._play_pause)
        sh('Left', lambda: self.mp.set_time(max(0,self.mp.get_time()-5000)))
        sh('Right',lambda: self.mp.set_time(self.mp.get_time()+5000))
        sh('Shift+Left', lambda: self.mp.set_time(max(0,self.mp.get_time()-30000)))
        sh('Shift+Right',lambda: self.mp.set_time(self.mp.get_time()+30000))
        sh('Up',   lambda: self._set_vol(min(100,self._vol+5)))
        sh('Down', lambda: self._set_vol(max(0,self._vol-5)))
        sh('M',    self._tog_mute)
        sh('F',    self._tog_fs)
        sh('Escape',self._exit_fs)
        sh('O',    self._file_dlg)
        sh('Ctrl+O',self._file_dlg)
        sh('U',    lambda: self._url_dlg())
        sh('J',    self._jump_dlg)
        sh('I',    self._info_dlg)
        sh('L',    self._tog_lib)
        sh('S',    self._tog_shuf)
        sh('R',    self._tog_rep)
        sh('[',    self._spd_dn)
        sh(']',    self._spd_up)
        sh('E',    self._show_eq)
        sh('Ctrl+V',self._paste)

    def _open_any(self,path):
        if is_url(path): self._open_stream(path)
        else:            self._open_file(path)

    def _open_file(self,path):
        self.current=path
        self.mp.set_media(self._vlc.media_new(path))
        self.mp.play()
        self.video.show_idle(False)
        self.tb.set_file(Path(path).stem)
        self.ctrl.play.set_playing(True)
        self.lib.add_file(path); self.lib.set_cur(path)
        if path not in self.playlist: self.playlist.append(path)
        self.pl_idx=self.playlist.index(path)
        self._shuf=list(self.playlist); random.shuffle(self._shuf)
        self.ctrl.seek.set_pos(0); self.ctrl.t_cur.setText('0:00')
        if self._resume:
            saved=load_pos().get(path,0)
            if saved>3000: QTimer.singleShot(600,lambda: self.mp.set_time(saved))

    def _open_stream(self,url):
        url=url.strip(); self.current=url
        try:    media=self._vlc.media_new_location(url)
        except: media=self._vlc.media_new(url)
        self.mp.set_media(media); self.mp.play()
        self.video.show_idle(False)
        self.tb.set_file(url[:60]+('...' if len(url)>60 else ''))
        self.ctrl.play.set_playing(True)
        self.lib.add_url(url); self.lib.set_cur(url)

    def _file_dlg(self):
        exts=' '.join(f'*{e}' for e in sorted(ALL_EXT))
        p,_=QFileDialog.getOpenFileName(self,'Open Media','',f'Media ({exts});;All (*)')
        if p: self._open_file(p)

    def _url_dlg(self,prefill=''):
        d=URLDialog(prefill,self); d.opened.connect(self._open_stream); d.exec()

    def _paste(self):
        text=QApplication.clipboard().text().strip()
        if not text: return
        if is_url(text): self._open_stream(text)
        elif Path(text).exists() and Path(text).suffix.lower() in ALL_EXT: self._open_file(text)
        else: self._url_dlg(text)

    def _play_pause(self):
        if not self.current: self._file_dlg(); return
        if self.mp.is_playing(): self.mp.pause(); self.ctrl.play.set_playing(False)
        else:                    self.mp.play();  self.ctrl.play.set_playing(True)

    def _prev(self):
        if not self.playlist: return
        lst=self._shuf if self._do_shuf else self.playlist
        try: idx=lst.index(self.current)
        except: idx=0
        self._open_any(lst[max(0,idx-1)])

    def _next(self):
        if not self.playlist: return
        lst=self._shuf if self._do_shuf else self.playlist
        try: idx=lst.index(self.current)
        except: idx=-1
        self._open_any(lst[(idx+1)%len(lst)])

    def _set_vol(self,v):
        self._vol=v; self.mp.audio_set_volume(v); self.ctrl.vol.set_vol(v)
        k='vol0' if v==0 else 'vol1' if v<35 else 'vol2' if v<70 else 'vol3'
        self.ctrl.vic.set_key(k)

    def _tog_mute(self):
        self._muted=not self._muted; self.mp.audio_set_mute(self._muted)
        self.ctrl.vic.set_key('vol0' if self._muted else 'vol3')

    def _tog_shuf(self):
        self._do_shuf=not self._do_shuf; self.ctrl.shuf.set_active(self._do_shuf)
        if self._do_shuf: self._shuf=list(self.playlist); random.shuffle(self._shuf)

    def _tog_rep(self):
        self._repeat=(self._repeat+1)%3
        self.ctrl.rep.set_key('rep1' if self._repeat==self.R_ONE else 'rep')
        self.ctrl.rep.set_active(self._repeat!=self.R_NONE)

    def _spd_menu(self):
        m=QMenu(self); m.setStyleSheet(MENU_CSS)
        cur=SPEEDS[self._spd]
        for s in SPEEDS:
            a=m.addAction(f"{'> ' if s==cur else '  '}{s}x"); a.setData(s)
        c=m.exec(self.ctrl.spd.mapToGlobal(QPoint(0,-len(SPEEDS)*30)))
        if c: self._spd=SPEEDS.index(c.data()); self._apply_spd()

    def _spd_up(self):
        if self._spd<len(SPEEDS)-1: self._spd+=1; self._apply_spd()
    def _spd_dn(self):
        if self._spd>0: self._spd-=1; self._apply_spd()
    def _apply_spd(self):
        s=SPEEDS[self._spd]; self.mp.set_rate(s)
        self.ctrl.spd.setText(f'{s}x')
        c=HL if s!=1.0 else TEXT3
        self.ctrl.spd.setStyleSheet(f'color:{c};font-size:10px;background:transparent;font-family:{MONO};')

    def _show_eq(self):
        if self._eq_dlg and self._eq_dlg.isVisible(): self._eq_dlg.raise_(); return
        self._eq_dlg=EQDialog(self.mp,self._eq_bands,self); self._eq_dlg.show()

    def _sub_menu(self):
        m=QMenu(self); m.setStyleSheet(MENU_CSS)
        m.addAction('Disable').setData(-1)
        tracks=self.mp.video_get_spu_description() or []
        if tracks: m.addSeparator()
        for tid,tn in tracks:
            n=tn.decode() if isinstance(tn,bytes) else str(tn); m.addAction(n).setData(tid)
        m.addSeparator(); m.addAction('Load file...').setData('load')
        m.addAction('Delay...').setData('sdel')
        c=m.exec(self.ctrl.sub.mapToGlobal(QPoint(0,-150)))
        if not c: return
        d=c.data()
        if d=='load':
            p,_=QFileDialog.getOpenFileName(self,'Load Subtitle','','Subtitles (*.srt *.ass *.ssa *.sub *.vtt);;All (*)')
            if p: self.mp.add_slave(vlc.MediaSlaveType.subtitle,p,True)
        elif d=='sdel': self._delay_dlg('subtitle')
        elif d is not None: self.mp.video_set_spu(int(d))

    def _aud_menu(self):
        m=QMenu(self); m.setStyleSheet(MENU_CSS)
        for tid,tn in (self.mp.audio_get_track_description() or []):
            n=tn.decode() if isinstance(tn,bytes) else str(tn); m.addAction(n).setData(tid)
        m.addSeparator(); m.addAction('Delay...').setData('adel')
        c=m.exec(self.ctrl.aud.mapToGlobal(QPoint(0,-150)))
        if not c: return
        d=c.data()
        if d=='adel': self._delay_dlg('audio')
        elif d is not None: self.mp.audio_set_track(int(d))

    def _asp_menu(self):
        m=QMenu(self); m.setStyleSheet(MENU_CSS)
        cur=self.mp.video_get_aspect_ratio() or ''
        for r in ASPECTS:
            mrk='> ' if (r=='Default' and not cur) or r==cur else '  '
            m.addAction(f'{mrk}{r}').setData(r)
        c=m.exec(self.ctrl.asp.mapToGlobal(QPoint(0,-len(ASPECTS)*30)))
        if c: self.mp.video_set_aspect_ratio('' if c.data()=='Default' else c.data())

    def _delay_dlg(self,kind):
        d=QDialog(self); d.setWindowTitle(f'{kind.title()} Delay')
        d.setFixedSize(270,112); d.setModal(True); d.setStyleSheet(DLG_CSS)
        vl=QVBoxLayout(d); vl.setContentsMargins(20,16,20,16); vl.setSpacing(10)
        vl.addWidget(mk_lbl(f'{kind.title()} delay (seconds):',11,TEXT2))
        sp=QDoubleSpinBox(); sp.setRange(-10,10); sp.setSingleStep(0.05); sp.setDecimals(3)
        fn=self.mp.audio_get_delay if kind=='audio' else self.mp.video_get_spu_delay
        sp.setValue(fn()/1_000_000); vl.addWidget(sp)
        row=QHBoxLayout(); row.addStretch()
        ok=mk_btn('Apply',accent=True); ok.setFixedWidth(70)
        sfn=self.mp.audio_set_delay if kind=='audio' else self.mp.video_set_spu_delay
        ok.clicked.connect(lambda:(sfn(int(sp.value()*1_000_000)),d.accept()))
        row.addWidget(ok); vl.addLayout(row); d.exec()

    def _info_dlg(self):
        if not self.current: return
        # close any existing info dialog
        if hasattr(self,'_info_d') and self._info_d and self._info_d.isVisible():
            self._info_d.close()
        d=QDialog(self); d.setWindowTitle('Media Info')
        d.setFixedSize(420,250); d.setModal(False); d.setStyleSheet(DLG_CSS)
        self._info_d=d
        vl=QVBoxLayout(d); vl.setContentsMargins(22,18,22,18); vl.setSpacing(8)
        labels={}
        for k in ['File','Duration','Size','Video','FPS','Rate','State']:
            row=QHBoxLayout()
            kl=mk_lbl(k,11,TEXT3); kl.setFixedWidth(72)
            val=mk_lbl('',11,TEXT)
            labels[k]=val
            row.addWidget(kl); row.addWidget(val); vl.addLayout(row)
        vl.addStretch()
        ok=mk_btn('Close'); ok.clicked.connect(d.close)
        vl.addWidget(ok,0,Qt.AlignmentFlag.AlignRight)

        def refresh():
            if not d.isVisible(): tmr.stop(); return
            p=self.current
            if not p: return
            labels['File'].setText(Path(p).name if not is_url(p) else p[:50])
            labels['Duration'].setText(fmt(max(0,self.mp.get_length())))
            labels['Size'].setText(fsize(p))
            w,h=self.mp.video_get_width(),self.mp.video_get_height()
            labels['Video'].setText(f'{w}\u00d7{h}' if w>0 else '\u2014')
            fps=self.mp.get_fps()
            labels['FPS'].setText(f'{fps:.3f}' if fps>0 else '\u2014')
            labels['Rate'].setText(f'{SPEEDS[self._spd]}x')
            st=self.mp.get_state()
            sn={vlc.State.Playing:'Playing',vlc.State.Paused:'Paused',
                vlc.State.Stopped:'Stopped',vlc.State.Ended:'Ended',
                vlc.State.Opening:'Opening',vlc.State.Buffering:'Buffering'}
            labels['State'].setText(sn.get(st,str(st)))

        tmr=QTimer(d); tmr.setInterval(500); tmr.timeout.connect(refresh)
        refresh(); tmr.start()
        d.show()

    def _jump_dlg(self):
        d=JumpDialog(self.mp.get_time(),self); d.jumped.connect(self.mp.set_time); d.exec()

    def _tog_fs(self):
        if self._fs: self._exit_fs()
        else: self._enter_fs()

    def _enter_fs(self):
        self._fs=True
        self.tb.hide(); self.lib.hide(); self.ctrl.hide()
        self.centralWidget().setStyleSheet('QWidget#root{background:#000000;}'
                                           'QWidget{background:transparent;}')
        self.showFullScreen(); self.ctrl.ful.set_key('unfull')

    def _exit_fs(self):
        if not self._fs: return
        self._fs=False; self.showNormal()
        self.centralWidget().setStyleSheet(f'QWidget#root{{background:{BG};}}'
                                           f'QWidget{{background:transparent;color:{TEXT};}}')
        self.tb.show()
        if self._lib_vis: self.lib.show()
        self.ctrl.show(); self.ctrl.ful.set_key('full')

    def _tog_lib(self):
        self._lib_vis=not self._lib_vis; self.lib.setVisible(self._lib_vis)
        self.tb.lib_btn.set_active(not self._lib_vis)

    def _tick(self):
        pos=self.mp.get_position(); ms=self.mp.get_time()
        if pos>=0:
            self.ctrl.seek.set_pos(pos)
            self.ctrl.seek.set_buf(min(1.0,pos+0.06))
        self.ctrl.t_cur.setText(fmt(max(0,ms)))
        self.ctrl.t_tot.setText(fmt(max(0,self.mp.get_length())))
        if self.current and not is_url(self.current) and ms>3000:
            now=time.monotonic()
            if now-self._last_save>5:
                self._last_save=now; save_pos(self.current,ms)
                self.lib.upd_pos(self.current,ms)
        state=self.mp.get_state()
        if state==vlc.State.Ended:
            self.ctrl.play.set_playing(False)
            if   self._repeat==self.R_ONE: self._open_any(self.current)
            elif self._repeat==self.R_ALL: self._next()
            elif self.pl_idx<len(self.playlist)-1: self._next()
        elif state==vlc.State.Playing:   self.ctrl.play.set_playing(True)
        elif state in(vlc.State.Paused,vlc.State.Stopped): self.ctrl.play.set_playing(False)

    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self,e):
        for u in e.mimeData().urls():
            p=u.toLocalFile()
            if Path(p).suffix.lower() in ALL_EXT: self._open_file(p); return

    def _load_settings(self):
        try:
            if SET_F.exists():
                s=json.loads(SET_F.read_text(encoding='utf-8'))
                self._vol=s.get('vol',80); self._eq_bands=s.get('eq',[0.0]*10)
                self._spd=s.get('spd',SPEEDS.index(1.0)); self._resume=s.get('resume',True)
        except: pass

    def _save_settings(self):
        try: SET_F.write_text(json.dumps({'vol':self._vol,'eq':self._eq_bands,
                                         'spd':self._spd,'resume':self._resume}),encoding='utf-8')
        except: pass

    def showEvent(self, e):
        print("showEvent fired", flush=True)
        super().showEvent(e)

    def closeEvent(self,e):
        if self.current and not is_url(self.current):
            ms=self.mp.get_time()
            if ms>3000: save_pos(self.current,ms)
        self._save_settings(); self.mp.stop(); self._vlc.release(); super().closeEvent(e)


# ── entry ─────────────────────────────────────────────────────────────────────
APP_CSS = f"""
* {{ font-family: Segoe UI, sans-serif; }}
QMainWindow {{ background: {BG}; }}
QToolTip {{ background:#141417; color:{TEXT}; border:1px solid {BDR2};
            border-radius:6px; padding:4px 8px; font-size:11px; }}
QScrollBar:vertical {{ background:transparent; width:3px; }}
QScrollBar::handle:vertical {{ background:rgba(255,255,255,0.15); border-radius:2px; min-height:20px; }}
QScrollBar::handle:vertical:hover {{ background:rgba(255,255,255,0.30); }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background:none; }}
"""

if __name__ == '__main__':
    import traceback
    try:
        print("step 1: QApplication", flush=True)
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        _app = QApplication(sys.argv)
        _app.setApplicationName('Glacial')
        _app.setStyleSheet(APP_CSS)
        print("step 2: creating window", flush=True)
        _win = Glacial()
        print("step 3: showing window", flush=True)
        screen = QApplication.primaryScreen().geometry()
        _win.move(
            screen.x() + (screen.width() - 1140) // 2,
            screen.y() + (screen.height() - 700) // 2
        )
        print("step 3a: calling show()", flush=True)
        _win.setVisible(True)
        print("step 3b: show() returned", flush=True)
        _win.raise_()
        _win.activateWindow()
        QTimer.singleShot(200, _win._attach_vlc)
        print(f"step 4: isVisible={_win.isVisible()} geo={_win.geometry()}", flush=True)
        print(f"step 5: entering event loop", flush=True)
        if sys.platform == 'win32':
            try:
                import ctypes
                _hwnd = int(_win.winId())
                # Remove caption (native title bar) but keep thick frame for resize
                GWL_STYLE = -16
                WS_CAPTION = 0x00C00000
                WS_THICKFRAME = 0x00040000
                _style = ctypes.windll.user32.GetWindowLongW(_hwnd, GWL_STYLE)
                _style = (_style & ~WS_CAPTION) | WS_THICKFRAME
                ctypes.windll.user32.SetWindowLongW(_hwnd, GWL_STYLE, _style)
                # Force redraw with new style
                import ctypes.wintypes
                SWP_FRAMECHANGED = 0x0020
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOZORDER = 0x0004
                ctypes.windll.user32.SetWindowPos(_hwnd, 0, 0, 0, 0, 0,
                    SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER)
            except: pass
        if len(sys.argv) > 1:
            p = sys.argv[1]
            if Path(p).exists(): _win._open_file(p)
        print("step 5: event loop", flush=True)
        _app.exec()
        print("step 6: event loop ended", flush=True)
    except Exception as e:
        print(f"CRASH: {e}", flush=True)
        traceback.print_exc()
        input("press enter to close")
