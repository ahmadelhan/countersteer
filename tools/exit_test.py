# v0.20 diagnostic: finds which part of the game makes Tk crash on exit.
# Run from the project folder:   python tools/exit_test.py
# Each test opens the game briefly and closes it by itself.
# If a "Fatal Error" box pops up, click OK and the next test carries on.
import os
import subprocess
import sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SETUP = '''
import sys, os
sys.path.insert(0, os.getcwd())
import tkinter as tk
import theme, sound, gui
USE_ICON, USE_FONTS, USE_SOUND, SCREEN = {icon}, {fonts}, {sound}, "{screen}"
if not USE_SOUND:
    sound._enabled = False
if USE_ICON:
    gui.setAppId()
window = tk.Tk()
if USE_ICON:
    gui.setWindowIcon(window)
gui.centreWindow(window)
window.configure(bg = theme.bg)
if USE_FONTS:
    theme.setupFonts(window)
else:
    theme.fonts.update(body = ("Arial", 11), small = ("Arial", 9), mono = ("Courier New", 11),
                       monoBig = ("Courier New", 20, "bold"), title = ("Arial", 22, "bold"),
                       heading = ("Arial", 14, "bold"), bodyBold = ("Arial", 11, "bold"))
sound.start(window)

def closeWhenOnMenu():
    import menu
    if any(isinstance(w, menu.MainMenu) for w in window.winfo_children()):
        window.after(800, lambda: gui.quitGame(window))
    else:
        window.after(200, closeWhenOnMenu)

if SCREEN == "blank":
    window.after(1500, lambda: gui.quitGame(window))
elif SCREEN == "menu":
    gui.showMainMenu(window)
    window.after(500, closeWhenOnMenu)
elif SCREEN == "loading":
    gui.showBootLoading(window)
    window.after(500, closeWhenOnMenu)
window.mainloop()
print("CLEAN EXIT")
'''

tests = [
    ("1  blank window",              dict(icon = False, fonts = False, sound = False, screen = "blank")),
    ("2  blank + icon",              dict(icon = True,  fonts = False, sound = False, screen = "blank")),
    ("3  blank + fonts",             dict(icon = False, fonts = True,  sound = False, screen = "blank")),
    ("4  blank + sound",             dict(icon = False, fonts = False, sound = True,  screen = "blank")),
    ("5  menu only, nothing extra",  dict(icon = False, fonts = False, sound = False, screen = "menu")),
    ("6  loading -> menu, nothing",  dict(icon = False, fonts = False, sound = False, screen = "loading")),
    ("7  loading -> menu, all on",   dict(icon = True,  fonts = True,  sound = True,  screen = "loading")),
    ("8  all on except icon",        dict(icon = False, fonts = True,  sound = True,  screen = "loading")),
    ("9  all on except fonts",       dict(icon = True,  fonts = False, sound = True,  screen = "loading")),
    ("10 all on except sound",       dict(icon = True,  fonts = True,  sound = False, screen = "loading")),
]

print(f"Python {sys.version.split()[0]}")
results = []
for name, options in tests:
    print(f"running {name} ...", flush = True)
    try:
        run = subprocess.run([sys.executable, "-c", SETUP.format(**options)], cwd = PROJECT,
                             capture_output = True, text = True, timeout = 60)
        ok = run.returncode == 0 and "CLEAN EXIT" in run.stdout
        detail = "" if ok else (run.stderr.strip().splitlines() or [f"exit code {run.returncode}"])[-1]
    except subprocess.TimeoutExpired:
        ok, detail = False, "timed out"
    results.append((name, ok, detail))

print("\nRESULTS (copy this back):")
for name, ok, detail in results:
    print(f"  {name:32} {'ok' if ok else 'CRASH'}  {detail}")