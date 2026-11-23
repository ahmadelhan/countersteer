# v0.20 NEW FILE - loading screens (boot + after team select)
import os
import random
import time
import tkinter as tk

import theme
import carcard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

width = 960
height = 680
horizon = 430
frame_ms = 30
spin_ms = 120           # car turns one frame every 120 ms, timed by the clock
bar_left = 260
bar_right = 700
bar_y = 560
showcase_size = "garage"

flavour = ["WARMING TYRES", "CHECKING BOOST", "SETTING CAMBER", "BLEEDING BRAKES",
           "FUELLING UP", "SCOUTING THE PASS"]

tips = [
    "An aggressive line scores more but shrinks the target. Save it for when you need it.",
    "Fresh tyres widen the target, but they use up an extra tyre set.",
    "Pressure only works in battles: nail your run and the lead car cracks.",
    "A spin costs condition. Below 30% the car can't run.",
    "Wages are paid at the start of every round. Run out of money and it's game over.",
    "Tune upgrades raise a driver's rating and widen their target.",
    "When two of your drivers meet, you decide who goes through.",
    "Rivals get stronger every round. Upgrade early.",
    "Press M at any time to mute. The player under your budget can pause or skip.",
]


class LoadingScreen(tk.Frame):
    """Runs a list of (label, function) tasks one per frame while a car spins.
    heading = None draws the game logo, otherwise (kicker, title, subtitle) text."""

    def __init__(self, master, showcaseFolder, tasks, onDone, heading = None, caption = ""):
        super().__init__(master, bg = theme.bg)
        self.__tasks = list(tasks)
        self.__total = max(1, len(self.__tasks))
        self.__done = 0
        self.__shown = 0.0              # bar position drawn, eases towards the real one
        self.__onDone = onDone
        self.__finished = False
        self.__frame = 0
        self.__afterId = None
        self.__images = {}
        self.__carFrames = None
        self.__carIndex = carcard.start_frame
        self.__spinStart = None         # clock time the car started turning
        self.__showcase = showcaseFolder
        self.__keyBinding = None

        self.__canvas = tk.Canvas(self, width = width, height = height, bg = theme.bg,
                                  highlightthickness = 0)
        self.__canvas.pack(fill = "both", expand = True)

        # the showcase car loads first so it's on screen straight away
        self.__tasks.insert(0, ("Nightline garage", self.__loadShowcase))
        self.__total += 1

        self.__drawScenery()
        if heading is None:
            self.__drawLogo()
        else:
            self.__drawHeading(*heading)
        self.__drawBar(caption)

        root = master.winfo_toplevel()
        self.__keyBinding = root.bind("<Key>", self.__keyPressed, add = "+")
        self.__canvas.bind("<Button-1>", lambda e: self.__skip())
        self.bind("<Destroy>", lambda e: self.__stop())
        self.__tick()

    # images
    def __loadImage(self, name):
        path = os.path.join(BASE_DIR, "images", name)
        if not os.path.exists(path):
            return None
        try:
            image = tk.PhotoImage(file = path)
        except tk.TclError:
            return None
        self.__images[name] = image
        return image

    def __loadShowcase(self):
        self.__carFrames = carcard.loadFrames(self.__showcase, showcase_size)
        c = self.__canvas
        if self.__carFrames is None:
            carcard.drawSilhouette(c, width // 2 - 153, horizon - 92)
        else:
            c.create_image(width // 2, horizon - 62, image = self.__carFrames[self.__carIndex],
                           tags = "car")
        c.tag_raise("car")

    # drawing
    def __drawScenery(self):
        c = self.__canvas
        rng = random.Random(11)
        for _ in range(150):          # stars over the whole screen
            x, y = rng.randint(0, width), rng.randint(0, height)
            size = rng.choice([1, 1, 2])
            c.create_oval(x, y, x + size, y + size, fill = theme.muted, outline = "")

    def __drawLogo(self):
        c = self.__canvas
        title = self.__loadImage("title.png")
        glow = self.__loadImage("title_glow.png")
        subtitle = self.__loadImage("subtitle.png")
        if title is not None and glow is not None:
            c.create_image(width // 2 + 5, 105 + 5, image = glow)
            c.create_image(width // 2, 105, image = title)
        else:
            family = theme.fonts["title"][0]
            c.create_text(width // 2 + 3, 108, text = "COUNTERSTEER", font = (family, 54, "bold"),
                          fill = theme.cyan)
            c.create_text(width // 2, 105, text = "COUNTERSTEER", font = (family, 54, "bold"),
                          fill = theme.pink)
        if subtitle is not None:
            c.create_image(width // 2, 180, image = subtitle)
        else:
            c.create_text(width // 2, 175, text = "a drift team manager",
                          font = theme.fonts["heading"], fill = theme.text)

    def __drawHeading(self, kicker, title, subtitle):
        c = self.__canvas
        family = theme.fonts["title"][0]
        c.create_text(width // 2, 70, text = kicker, font = theme.fonts["bodyBold"], fill = theme.cyan)
        c.create_text(width // 2 + 3, 123, text = title.upper(), font = (family, 38, "bold"),
                      fill = theme.cyan)
        c.create_text(width // 2, 120, text = title.upper(), font = (family, 38, "bold"),
                      fill = theme.pink)
        c.create_text(width // 2, 172, text = subtitle, font = theme.fonts["body"], fill = theme.muted)

    def __drawBar(self, caption):
        c = self.__canvas
        if caption:
            c.create_text(width // 2, horizon + 48, text = caption, font = theme.fonts["heading"],
                          fill = theme.cyan)
        icon = self.__loadImage("icon_48.png")
        if icon is not None:
            c.create_image(bar_left - 34, bar_y - 6, image = icon)
        c.create_text(bar_left, bar_y - 16, text = "", anchor = "w", font = theme.fonts["small"],
                      fill = theme.text, tags = "status")
        c.create_text(bar_right, bar_y - 16, text = "0%", anchor = "e", font = theme.fonts["mono"],
                      fill = theme.cyan, tags = "percent")
        c.create_rectangle(bar_left, bar_y - 3, bar_right, bar_y + 3, fill = theme.panel_light,
                           outline = "")
        c.create_rectangle(bar_left, bar_y - 3, bar_left, bar_y + 3, fill = theme.pink,
                           outline = "", tags = "fill")
        c.create_rectangle(bar_left - 2, bar_y - 5, bar_left + 2, bar_y + 5, fill = "white",
                           outline = "", tags = "tip")
        c.create_text(width // 2, bar_y + 46, text = "TIP  " + random.choice(tips),
                      font = theme.fonts["small"], fill = theme.muted, width = 620)

    # the loop
    def __runTask(self):
        label, task = self.__tasks[self.__done]
        self.__canvas.itemconfig("status", text = f"{flavour[self.__done % len(flavour)]}"
                                                  f"   ·   {label}")
        task()
        self.__done += 1

    def __tick(self):
        try:
            if self.__done < self.__total:
                self.__runTask()
            self.__animate()
        except tk.TclError:      # window closed mid-load
            return
        self.__frame += 1
        self.__afterId = self.after(frame_ms, self.__tick)   # keeps spinning until a key is pressed

    def __isReady(self):
        return self.__done >= self.__total and self.__shown > 0.995

    def __animate(self):
        c = self.__canvas
        target = self.__done / self.__total
        self.__shown += (target - self.__shown) * 0.25
        x = bar_left + (bar_right - bar_left) * self.__shown
        c.coords("fill", bar_left, bar_y - 3, x, bar_y + 3)
        c.coords("tip", x - 2, bar_y - 5, x + 2, bar_y + 5)
        c.itemconfig("percent", text = f"{round(self.__shown * 100)}%")
        if self.__isReady():
            on = (self.__frame // 12) % 2 == 0
            c.itemconfig("status", text = "READY   ·   PRESS ANY KEY",
                         fill = theme.cyan if on else theme.muted)
        if self.__carFrames is not None:
            # frame comes from the clock, so the turn stays the same speed even when loading stalls a frame
            if self.__spinStart is None:
                self.__spinStart = time.monotonic()
            steps = int((time.monotonic() - self.__spinStart) * 1000 / spin_ms)
            index = (carcard.start_frame + steps) % len(self.__carFrames)
            if index != self.__carIndex:
                self.__carIndex = index
                c.itemconfig("car", image = self.__carFrames[index])

    def __keyPressed(self, event):
        if event.keysym.lower() == "m":     # M is mute, not continue
            return
        self.__skip()

    def __skip(self):
        if self.__isReady():                # only once everything has loaded
            self.__finish()

    def __finish(self):
        if self.__finished:
            return
        self.__finished = True
        self.__stop()
        self.__onDone()

    def __stop(self):
        if self.__afterId is not None:
            try:
                self.after_cancel(self.__afterId)
            except tk.TclError:
                pass
            self.__afterId = None
        if self.__keyBinding is not None:     # same fix as the menu: release the key
            try:
                self.winfo_toplevel().unbind("<Key>", self.__keyBinding)
            except tk.TclError:
                pass
            self.__keyBinding = None


# task lists
def bootTasks(catalogue):
    """Draft-size turntable frames for every car (the draft screen shows them all)."""
    tasks = []
    for model, (_, _, folder) in catalogue.items():
        tasks.append((model, lambda f = folder: carcard.loadFrames(f, "draft")))
    return tasks


def teamTasks(team):
    """Garage-size frames for the cars your team actually runs."""
    tasks = []
    seen = []
    for driver in team.getDrivers():
        folder = driver.getCar().getImagePath()
        if folder not in seen:
            seen.append(folder)
            tasks.append((driver.getCar().getModel(),
                          lambda f = folder: carcard.loadFrames(f, "garage")))
    return tasks