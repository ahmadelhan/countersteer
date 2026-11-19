import os
import tkinter as tk

import theme

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def loadCarImage(path, cache):
    if path in cache:
        return cache[path]
    image = None
    fullPath = os.path.join(BASE_DIR, path)
    if path and os.path.exists(fullPath):
        try:
            image = tk.PhotoImage(file = fullPath)
        except tk.TclError:
            image = None     
    cache[path] = image
    return image


def drawSilhouette(c, x, y):
    body = [0, 70, 6, 50, 60, 42, 105, 14, 195, 12, 245, 38, 300, 46, 306, 70]
    c.create_polygon([v + (x if i % 2 == 0 else y) for i, v in enumerate(body)],
                     fill = theme.panel_light, outline = theme.cyan, width = 2)
    window = [112, 20, 190, 18, 230, 40, 100, 42]
    c.create_polygon([v + (x if i % 2 == 0 else y) for i, v in enumerate(window)],
                     fill = theme.bg, outline = theme.cyan)
    for wheelX in (68, 240):
        c.create_oval(x + wheelX - 19, y + 52, x + wheelX + 19, y + 90,
                      fill = theme.bg, outline = theme.pink, width = 3)
    c.create_line(x + 20, y + 96, x + 290, y + 96, fill = theme.pink, width = 3)   # underglow


def drawStatBar(c, x, y, label, value, maximum, text, colour, barWidth = 300):
    c.create_text(x, y, text = label, anchor = "w", font = theme.fonts["small"], fill = theme.muted)
    left = x + 90
    c.create_rectangle(left, y - 6, left + barWidth, y + 6, fill = theme.panel_light, outline = "")
    c.create_rectangle(left, y - 6, left + barWidth * min(value, maximum) / maximum, y + 6,
                       fill = colour, outline = "")
    c.create_text(left + barWidth + 10, y, text = text, anchor = "w",
                  font = theme.fonts["mono"], fill = theme.text)