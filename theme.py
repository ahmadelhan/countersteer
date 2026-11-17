import tkinter.font as guiFont

bg = "#0b0b14"          
panel = "#15152b"
panel_light = "#22223f"
pink = "#ff2e88"
cyan = "#00e5ff"
muted = "#8a8aa8"
warn = "#ffb020"
good = "#39ff88"
bad = "#ff4d4d"
text = "#e6e6f0"

main_choices = ["Bahnschrift", "Segoe UI", "DejaVu Sans", "Arial"]
mono_choices = ["Consolas", "DejaVu Sans Mono", "Courier New"]

fonts = {}

def setupFonts(root):
    installed = set(guiFont.families(root))
    main = next((f for f in main_choices if f in installed), "TkDefaultFont")
    mono = next((f for f in mono_choices if f in installed), "TkFixedFont")
    fonts["title"] = (main, 22, "bold")
    fonts["heading"] = (main, 14, "bold")
    fonts["body"] = (main, 11)
    fonts["bodyBold"] = (main, 11, "bold")
    fonts["small"] = (main, 9)
    fonts["mono"] = (mono, 11)
    fonts["monoBig"] = (mono, 20, "bold")