import os
import random
import sys
import tkinter as tk

SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")

effects = {                 
    "hover":   "hover.wav",         
    "click":   "click.wav",         
    "perfect": "perfect.wav",       # no sfx found yet
}
menu_music = "music_menu.mp3"      
game_music = [f"music_game_{n}.mp3" for n in range(1, 6)]  
music_volume = 250          # 0-1000
effects_volume = 800        # 0-1000
effect_channels = 4        
check_ms = 1000             

_muted = False
_currentMusic = None
_queue = []
_lastTrack = None
_root = None
_nextChannel = 0
_enabled = sys.platform == "win32"


def _mci(command):
    if not _enabled:
        return False
    try:
        import ctypes
        return ctypes.windll.winmm.mciSendStringW(command, None, 0, 0) == 0
    except (OSError, AttributeError):
        return False


def _status(alias):
    if not _enabled:
        return ""
    try:
        import ctypes
        answer = ctypes.create_unicode_buffer(64)
        ctypes.windll.winmm.mciSendStringW(f"status {alias} mode", answer, 64, 0)
        return answer.value
    except (OSError, AttributeError):
        return ""


def _path(fileName):
    path = os.path.join(SOUND_DIR, fileName)
    return path if os.path.exists(path) else None


def start(root):
    global _root
    _root = root
    _check()


def _check():
    if _root is None:
        return
    if not _muted and _currentMusic == "game" and _status("music") == "stopped":
        _playNextGameTrack()
    try:
        _root.after(check_ms, _check)
    except tk.TclError:             # window closed
        pass


# effects
def playSfx(name):
    global _nextChannel
    if _muted or not _enabled or name not in effects:
        return
    path = _path(effects[name])
    if path is None:
        return
    alias = f"sfx{_nextChannel}"
    _nextChannel = (_nextChannel + 1) % effect_channels
    _mci(f"close {alias}")
    if _mci(f'open "{path}" type mpegvideo alias {alias}'):
        _mci(f"setaudio {alias} volume to {effects_volume}")
        _mci(f"play {alias}")


# music
def playMusic(name):
    global _currentMusic
    if name == _currentMusic:
        return
    _currentMusic = name
    _startMusic()


def _startMusic():
    _mci("close music")
    if _muted or _currentMusic is None:
        return
    if _currentMusic == "menu":
        _open(menu_music, loop = True)
    elif _currentMusic == "game":
        _playNextGameTrack()


def _open(fileName, loop):
    path = _path(fileName)
    if path is not None and _mci(f'open "{path}" type mpegvideo alias music'):
        _mci(f"setaudio music volume to {music_volume}")
        _mci("play music repeat" if loop else "play music")
        return True
    return False


def _playNextGameTrack():
    global _queue, _lastTrack
    available = [track for track in game_music if _path(track) is not None]
    if not available:
        return
    if not _queue:
        _queue = available[:]
        random.shuffle(_queue)
        if len(_queue) > 1 and _queue[0] == _lastTrack:
            _queue.append(_queue.pop(0))
    _lastTrack = _queue.pop(0)
    _mci("close music")
    _open(_lastTrack, loop = False)


def stopMusic():
    global _currentMusic
    _currentMusic = None
    _mci("close music")


#  mute
def isMuted():
    return _muted


def setMuted(muted):
    global _muted
    _muted = muted
    if muted:
        _mci("close music")
        for channel in range(effect_channels):
            _mci(f"close sfx{channel}")
    else:
        _startMusic()          


def toggleMute():
    setMuted(not _muted)
    return _muted


def closeAll():
    global _root
    _root = None
    _mci("close all")