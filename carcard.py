import os
import tkinter as tk

import theme

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# v0.14 FULL FILE REWORK
# PREVIOUS VERSIONS DEPRECATED

# v0.14 turntable settings
car_style = "real"      # toggleable choice - future implementation - now default
frame_count = 24 
auto_spin = False       # v0.14   
start_frame = 3       
spin_ms = 110          
drag_step = 12        
resume_ms = 1500        
_frameCache = {}    

# v0.14

def loadFrames(folder, size):
    key = (folder, size, car_style)
    if key in _frameCache:
        return _frameCache[key]
    frames = []
    for number in range(1, frame_count + 1):
        path = os.path.join(BASE_DIR, folder, f"{car_style}_{size}_{number:02d}.png")
        if not os.path.exists(path):
            frames = None
            break
        try:
            frames.append(tk.PhotoImage(file = path))
        except tk.TclError:   # no image exception    
            frames = None
            break
    _frameCache[key] = frames
    return frames


class Turntable:
    def __init__(self, canvas, size):
        self.__canvas = canvas
        self.__size = size             
        self.__frames = None
        self.__folder = None
        self.__item = None              
        self.__index = start_frame
        self.__afterId = None
        self.__dragX = None
        canvas.bind("<ButtonPress-1>", self.__dragStart)
        canvas.bind("<B1-Motion>", self.__drag)
        canvas.bind("<ButtonRelease-1>", self.__dragEnd)
        canvas.bind("<Destroy>", lambda e: self.__stop())

    def show(self, folder, x, y):
        frames = loadFrames(folder, self.__size)
        if frames is None:
            self.__item = None
            return False
        if folder != self.__folder:
            self.__folder = folder
            self.__index = start_frame
        self.__frames = frames
        self.__item = self.__canvas.create_image(x, y, image = frames[self.__index])
        if auto_spin and self.__afterId is None and self.__dragX is None:
            self.__afterId = self.__canvas.after(spin_ms, self.__tick)
        return True

    def __showFrame(self):
        if self.__item is not None:
            self.__canvas.itemconfig(self.__item, image = self.__frames[self.__index])

    def __tick(self):
        self.__afterId = None
        if self.__item is None:
            return
        self.__index = (self.__index + 1) % len(self.__frames)
        self.__showFrame()
        self.__afterId = self.__canvas.after(spin_ms, self.__tick)

    def __stop(self):
        if self.__afterId is not None:
            try:
                self.__canvas.after_cancel(self.__afterId)
            except tk.TclError:
                pass
            self.__afterId = None

    def __dragStart(self, event):
        if self.__item is None:
            return
        self.__stop()
        self.__dragX = event.x

    def __drag(self, event):
        if self.__dragX is None:
            return
        steps = (event.x - self.__dragX) // drag_step
        if steps != 0:
            self.__index = (self.__index - steps) % len(self.__frames)
            self.__dragX += steps * drag_step
            self.__showFrame()

    def __dragEnd(self, event):
        if self.__dragX is None:
            return
        self.__dragX = None
        if auto_spin:
            self.__afterId = self.__canvas.after(resume_ms, self.__tick)


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