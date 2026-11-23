import os
import random
import tkinter as tk
import tkinter.font as guiFont

import theme
import animate # v0.19
import sound # v0.19

width = 960
height = 680
horizon = 360               
vanish_x = width // 2     
frame_ms = 30              
road_speed = 0.035         
grid_lines = 12            

kanji_choices = ["Yu Gothic UI", "Yu Gothic", "Meiryo", "MS Gothic",
                 "Noto Sans CJK JP", "Noto Sans JP"]

guide_text = (
    "GARAGE\n"
    "Browse your drivers with First / Prev / Next / Last and start a qualifying run.\n\n"
    "QUALIFYING RUN\n"
    "Press SPACE when the pink marker is inside the cyan zone. There are three "
    "sections: entry, angle and exit. Miss badly, or don't press, and you spin, "
    "which damages the car.\n\n"
    "STRATEGY\n" # v0.20
    "Before every run pick a line (Safe, Balanced or Aggressive) and used or fresh "
    "tyres. In battles you can also pressure the lead car.\n\n"
    "SHOP\n"
    "Buy tyres, repair damage and upgrade tune. Better tune and skill make the "
    "cyan zone wider.\n\n"
    "A car needs tyres and at least 30% condition to run."
)

class MainMenu(tk.Frame):

    def __init__(self, master, onStart, onExit):
        super().__init__(master, bg = theme.bg)
        self.__onStart = onStart
        self.__onExit = onExit
        self.__options = [("START", self.__start), ("GUIDE", self.__openGuide),
                          ("EXIT", self.__exit)]
        self.__selected = 0
        self.__shownSelected = None # v0.19 the option currently drawn big
        self.__phase = 0.0          
        self.__frame = 0
        self.__afterId = None
        self.__guideOpen = False
        self.__images = {}         
        self.__glowIsImage = False

        family = theme.fonts["title"][0]
        self.__bigFont = (family, 54, "bold")
        self.__subFont = (family, 13, "bold")
        self.__optionFont = (family, 20, "bold")
        self.__smallFont = theme.fonts["small"]
        self.__kanjiFont = (self.__pickKanjiFont(master), 110, "bold")

        self.__canvas = tk.Canvas(self, width = width, height = height,
                                  bg = theme.bg, highlightthickness = 0)
        self.__canvas.pack(fill = "both", expand = True)

        self.__drawScenery()
        self.__drawTitle()
        self.__drawOptions()

        # v0.15
        self.__bindings = [
            ("<Up>", master.bind("<Up>", lambda e: self.__moveSelection(-1))),
            ("<Down>", master.bind("<Down>", lambda e: self.__moveSelection(1))),
            ("<Return>", master.bind("<Return>", lambda e: self.__activate())),
            ("<Escape>", master.bind("<Escape>", lambda e: self.__closeGuide())),
        ]
        self.bind("<Destroy>", lambda e: (self.__stop(), self.__unbindKeys())) # v0.15 also release the keys

        self.__animate()

    def __pickKanjiFont(self, root):
        installed = set(guiFont.families(root))
        for family in kanji_choices:
            if family in installed:
                return family
        return theme.fonts["title"][0]

    def __loadImage(self, name):
        """Load images/<name> once. Returns None if the file is missing or broken,
        so the menu falls back to plain text instead of crashing."""
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", name)
        if not os.path.exists(path):
            return None
        try:
            image = tk.PhotoImage(file = path)
        except tk.TclError:
            return None
        self.__images[name] = image
        return image
    
    def __drawScenery(self):
        c = self.__canvas

        rng = random.Random(7)
        for _ in range(70):
            x, y = rng.randint(0, width), rng.randint(0, horizon - 120)
            size = rng.choice([1, 1, 2])
            c.create_oval(x, y, x + size, y + size, fill = theme.muted, outline = "")

        kanji = self.__loadImage("kanji.png")
        if kanji is not None:
            c.create_image(width - 90, 210, image = kanji)
        else:
            c.create_text(width - 85, 215, text = "峠", font = self.__kanjiFont,
                          fill = theme.panel_light)

        sunR = 120
        c.create_oval(vanish_x - sunR, horizon - sunR - 40, vanish_x + sunR, horizon + sunR - 40,
                      fill = theme.pink, outline = "", tags = "sun")

        back = [0, horizon, 90, 270, 190, 300, 300, 230, 420, 295, 540, 250,
                650, 290, 760, 220, 880, 285, width, 250, width, horizon]
        c.create_polygon(back, fill = theme.panel, outline = theme.panel_light, width = 2)
        front = [0, horizon, 60, 320, 160, 335, 250, 300, 340, 345, 620, 345,
                 700, 305, 800, 330, 900, 295, width, 325, width, horizon]
        c.create_polygon(front, fill = theme.bg, outline = theme.cyan, width = 2)

        c.create_rectangle(0, horizon, width, height, fill = theme.bg, outline = "", tags = "ground")
        c.create_line(0, horizon, width, horizon, fill = theme.pink, width = 2)

        for i in range(-10, 11):
            c.create_line(vanish_x, horizon, vanish_x + i * 160, height,
                          fill = theme.panel_light)

        c.create_line(vanish_x - 6, horizon, vanish_x - 330, height, fill = theme.cyan, width = 3)
        c.create_line(vanish_x + 6, horizon, vanish_x + 330, height, fill = theme.cyan, width = 3)

    def __drawTitle(self):
        c = self.__canvas
        title = self.__loadImage("title.png")
        glow = self.__loadImage("title_glow.png")
        subtitle = self.__loadImage("subtitle.png")
        if title is not None and glow is not None:
            c.create_image(width // 2 + 5, 90 + 5, image = glow, tags = "titleGlow")
            c.create_image(width // 2, 90, image = title)
            self.__glowIsImage = True
        else:
            c.create_text(width // 2 + 3, 93, text = "COUNTERSTEER", font = self.__bigFont,
                          fill = theme.cyan, tags = "titleGlow")
            c.create_text(width // 2, 90, text = "COUNTERSTEER", font = self.__bigFont,
                          fill = theme.pink)
        if subtitle is not None:
            c.create_image(width // 2, 172, image = subtitle)
        else:
            c.create_text(width // 2, 150, text = "D R I F T   T E A M   M A N A G E R",
                          font = self.__subFont, fill = theme.text)

    def __drawOptions(self):
        c = self.__canvas
        top = 440
        c.create_rectangle(width // 2 - 150, top - 20, width // 2 + 150, top + 170,
                           fill = theme.bg, outline = theme.pink, width = 2)
        for index, (label, action) in enumerate(self.__options):
            y = top + 25 + index * 55
            tag = f"option{index}"
            c.create_text(width // 2, y, text = label, font = self.__optionFont,
                          fill = theme.muted, tags = (tag, "option"))
            c.tag_bind(tag, "<Enter>", lambda e, i=index: self.__select(i))
            c.tag_bind(tag, "<Button-1>", lambda e, i=index: self.__choose(i)) # v0.19 click sound
        c.create_text(width // 2, height - 18,
                      text = "↑ ↓  select     ENTER  confirm     M  mute", font = self.__smallFont,  # v0.19
                      fill = theme.muted)
        self.__highlightSelected()

    def __animate(self):
        self.__phase = (self.__phase + road_speed) % 1.0
        self.__frame += 1
        self.__drawMoving()
        self.__afterId = self.after(frame_ms, self.__animate)

    def __depthToY(self, depth):
        return horizon + (height - horizon) * depth * depth

    def __drawMoving(self):
        c = self.__canvas
        c.delete("road")
        c.delete("stripes")

        for i in range(grid_lines):
            depth = (i + self.__phase) / grid_lines
            y = self.__depthToY(depth)
            colour = theme.panel_light if depth < 0.5 else "#3b2a6b"
            c.create_line(0, y, width, y, fill = colour, tags = "road")

        for i in range(6):
            start = (i + self.__phase) / 6
            end = start + 0.07
            if end > 1:
                continue
            c.create_line(vanish_x, self.__depthToY(start), vanish_x, self.__depthToY(end),
                          fill = theme.pink, width = 1 + 7 * start, tags = "road")
            
        sunR = 120
        sunTop = horizon - 40 - sunR
        for i in range(5):
            offset = (i * 14 + self.__frame * 0.5) % 70
            thickness = 1 + offset / 12
            y = sunTop + 30 + offset
            c.create_rectangle(vanish_x - sunR, y, vanish_x + sunR, y + thickness,
                               fill = theme.bg, outline = "", tags = "stripes")

        c.tag_raise("stripes", "sun")
        c.tag_raise("road", "ground")

        if self.__frame % 40 == 0:
            on = (self.__frame // 40) % 2 == 0
            if self.__glowIsImage:
                c.itemconfig("titleGlow", state = "normal" if on else "hidden")
            else:
                c.itemconfig("titleGlow", fill = theme.cyan if on else theme.panel_light)

    def __stop(self):
        if self.__afterId is not None:
            try:
                self.after_cancel(self.__afterId)
            except tk.TclError:
                pass
            self.__afterId = None
            
    def __select(self, index):
        if self.__guideOpen or index == self.__selected:
            return
        self.__selected = index
        sound.playSfx("hover") # v0.19
        self.__highlightSelected()

    def __moveSelection(self, step):
        if self.__guideOpen:
            return
        self.__selected = (self.__selected + step) % len(self.__options)
        sound.playSfx("hover") # v0.19
        self.__highlightSelected()

    def __choose(self, index): # v0.19
        sound.playSfx("click")
        self.__options[index][1]()

    def __highlightSelected(self): # v0.19 
        c = self.__canvas
        family, size, weight = self.__optionFont
        for index in range(len(self.__options)):
            colour = theme.cyan if index == self.__selected else theme.muted
            c.itemconfig(f"option{index}", fill = colour)
        targetY = 440 + 25 + self.__selected * 55
        if not c.find_withtag("chevron"):          
            c.create_text(width // 2 - 100, targetY, text = "▶", font = self.__optionFont,
                          fill = theme.pink, tags = ("chevron", "chevronLeft"))
            c.create_text(width // 2 + 100, targetY, text = "◀", font = self.__optionFont,
                          fill = theme.pink, tags = ("chevron", "chevronRight"))
            c.itemconfig(f"option{self.__selected}", font = (family, size + 3, weight))
            self.__shownSelected = self.__selected
            return
        startY = c.coords("chevronLeft")[1]
        old, new = self.__shownSelected, self.__selected
        self.__shownSelected = new

        def step(t):
            y = startY + (targetY - startY) * t
            c.coords("chevronLeft", width // 2 - 100, y)
            c.coords("chevronRight", width // 2 + 100, y)
            c.itemconfig(f"option{new}", font = (family, round(size + 3 * t), weight))
            if old is not None and old != new:
                c.itemconfig(f"option{old}", font = (family, round(size + 3 * (1 - t)), weight))

        animate.animate(c, "chevron", 130, step)

    def __activate(self):
        if self.__guideOpen:
            self.__closeGuide()
            return
        self.__choose(self.__selected) # v0.19 click sound

    def __start(self):
        self.__stop()
        self.__unbindKeys()
        self.__onStart()

    def __exit(self):
        self.__stop()
        self.__onExit()

    def __openGuide(self):
        if self.__guideOpen:
            return
        self.__guideOpen = True
        c = self.__canvas
        c.create_rectangle(140, 110, width - 140, height - 90, fill = theme.panel,
                           outline = theme.pink, width = 2, tags = "guide")
        c.create_text(width // 2, 150, text = "GUIDE", font = self.__optionFont,
                      fill = theme.pink, tags = "guide")
        c.create_text(width // 2, 340, text = guide_text, font = theme.fonts["body"],
                      fill = theme.text, width = width - 340, justify = "left", tags = "guide")
        c.create_text(width // 2, height - 120, text = "ESC / ENTER / click to go back",
                      font = self.__smallFont, fill = theme.cyan, tags = "guide")
        c.tag_bind("guide", "<Button-1>", lambda e: self.__closeGuide())

    def __closeGuide(self):
        if self.__guideOpen:
            self.__canvas.delete("guide")
            self.__guideOpen = False

    def __unbindKeys(self): # v0.15

        try:
            root = self.winfo_toplevel()
            for key, bindingId in self.__bindings:
                root.unbind(key, bindingId)
        except tk.TclError:     # window gone
            pass
        self.__bindings = []