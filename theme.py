import os
import sys
import tkinter.font as guiFont

bg = "#0b0b14"
panel = "#15152b"
panel_light = "#22223f"
pink = "#ff2e88"
cyan = "#00e5ff"
muted = "#8a8aa8"
text = "#e6e6f0"
warn = "#ffb020"
good = "#39ff88"
bad = "#ff4d4d"

main_choices = ["Bahnschrift", "Segoe UI", "DejaVu Sans", "Arial"]
mono_choices = ["Consolas", "DejaVu Sans Mono", "Courier New"]
display_font = "Russo One"   # v0.17
font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")  # v0.15

fonts = {}

def loadBundledFonts(): # v0.17
    if sys.platform != "win32" or not os.path.isdir(font_dir):
        return
    try:
        import ctypes
        FR_PRIVATE = 0x10
        for name in os.listdir(font_dir):
            if name.lower().endswith((".ttf", ".otf")):
                ctypes.windll.gdi32.AddFontResourceExW(os.path.join(font_dir, name), FR_PRIVATE, 0)
    except (OSError, AttributeError):
        pass

def setupFonts(root):
    loadBundledFonts() # v0.17
    installed = set(guiFont.families(root))
    main = next((f for f in main_choices if f in installed), "TkDefaultFont")
    mono = next((f for f in mono_choices if f in installed), "TkFixedFont")
    fonts["body"] = (main, 11)
    fonts["small"] = (main, 9)
    fonts["mono"] = (mono, 11)
    fonts["monoBig"] = (mono, 20, "bold")
    if display_font in installed: # v0.17
        fonts["title"] = (display_font, 22, "italic")
        fonts["heading"] = (display_font, 14, "italic")
        fonts["bodyBold"] = (display_font, 10) 
    else:
        fonts["title"] = (main, 22, "bold")
        fonts["heading"] = (main, 14, "bold")
        fonts["bodyBold"] = (main, 11, "bold")