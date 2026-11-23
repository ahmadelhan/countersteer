import math # v0.20 track view
import random
import tkinter as tk

import theme
import animate # v0.20

bar_left = 20
bar_width = 520
sections = ["ENTRY", "ANGLE", "EXIT"]
spin_zone = 3
tick_ms = 15
marker_speed = 7

# v0.20 track view
track_width = bar_left * 2 + bar_width
track_height = 240
anim_ms = 30
road_width = 40
max_drift = 0.55
start_gap = 0.07
smoke_life = 22
car_length = 24
car_breadth = 12
gap_change = {"perfect": -0.02, "clean": -0.01, "sloppy": 0.015, "spin": 0.04}
# v0.20

def scoreSection(markerX, sweetSpot, halfwidth):
    distance = abs(markerX - sweetSpot)
    if distance <= halfwidth:
        return round(100 - (distance / halfwidth) * 25), False
    if distance <= halfwidth * spin_zone:
        over = distance - halfwidth
        zone = halfwidth * (spin_zone - 1)
        return round(60 * (1 - over / zone)), False
    return 0, True


# v0.20 
def buildTrack():
    points = []
    left, right, top, bottom = 125, 435, 118, 226
    centreX, radiusX, radiusY = (left + right) / 2, (right - left) / 2, 80
    for i in range(12):
        points.append((left, bottom - (bottom - top) * i / 12))
    for i in range(61):
        angle = math.pi - math.pi * i / 60
        points.append((centreX + radiusX * math.cos(angle), top - radiusY * math.sin(angle)))
    for i in range(1, 13):
        points.append((right, top + (bottom - top) * i / 12))
    lengths = [0.0]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        lengths.append(lengths[-1] + math.hypot(x2 - x1, y2 - y1))
    return points, lengths


track_points, track_lengths = buildTrack()


def trackPosition(progress):
    progress = max(0.0, min(1.0, progress))
    target = progress * track_lengths[-1]
    for i in range(1, len(track_lengths)):
        if track_lengths[i] >= target:
            (x1, y1), (x2, y2) = track_points[i - 1], track_points[i]
            span = track_lengths[i] - track_lengths[i - 1]
            t = 0 if span == 0 else (target - track_lengths[i - 1]) / span
            return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, math.atan2(y2 - y1, x2 - x1)
    (x1, y1), (x2, y2) = track_points[-2], track_points[-1]
    return x2, y2, math.atan2(y2 - y1, x2 - x1)


def smoothStep(low, high, value):
    t = max(0.0, min(1.0, (value - low) / (high - low)))
    return t * t * (3 - 2 * t)


def driftAngle(progress):
    return max_drift * smoothStep(0.10, 0.28, progress) * (1 - smoothStep(0.78, 0.95, progress))


class TrackCar:

    def __init__(self, canvas, colour, tag):
        self.__canvas = canvas
        self.__colour = colour
        self.__tag = tag
        self.progress = 0.0
        self.wobble = 0.0
        self.wide = 0.0
        self.spin = None
        self.__frame = 0

    def position(self):
        x, y, heading = trackPosition(self.progress)
        x += math.sin(heading) * self.wide
        y -= math.cos(heading) * self.wide
        body = heading + driftAngle(self.progress) + self.wobble * math.sin(self.__frame * 0.7)
        if self.spin is not None:
            body += 2 * math.pi * animate.ease(min(1.0, self.spin / 28))
        return x, y, body

    def update(self):
        self.__frame += 1
        self.wobble *= 0.93
        self.wide *= 0.94
        if self.spin is not None:
            self.spin += 1
            if self.spin > 28:
                self.spin = None

    def isSliding(self):
        return driftAngle(self.progress) > 0.15 or self.spin is not None or self.wobble > 0.1

    def rear(self):
        x, y, body = self.position()
        return x - math.cos(body) * car_length / 2, y - math.sin(body) * car_length / 2

    def draw(self):
        c = self.__canvas
        c.delete(self.__tag)
        x, y, body = self.position()
        cos, sin = math.cos(body), math.sin(body)

        def corner(forward, side):
            return x + forward * cos - side * sin, y + forward * sin + side * cos

        half, breadth = car_length / 2, car_breadth / 2
        outline = [corner(half, breadth), corner(half, -breadth),
                   corner(-half, -breadth), corner(-half, breadth)]
        c.create_polygon(*[v for p in outline for v in p], fill = self.__colour,
                         outline = "white", width = 1, tags = self.__tag)
        c.create_line(*corner(3, -breadth + 1), *corner(3, breadth - 1), fill = theme.bg,
                      width = 3, tags = self.__tag)                       # windscreen
        c.create_line(*corner(-half + 2, -breadth), *corner(-half + 2, breadth),
                      fill = theme.bg, width = 2, tags = self.__tag)      # spoiler
        for side in (-breadth + 2, breadth - 2):                           # headlights
            c.create_oval(*corner(half - 1, side - 1), *corner(half + 1, side + 1),
                          fill = "#fff6c0", outline = "", tags = self.__tag)
# v0.20


class DriftRunWindow(tk.Toplevel):
    def __init__(self, master, driver, onFinish, strategy = None, rival = None, rivalScore = None,
                 title = "Qualifying run"): # v0.20 strategy, rival, title
        super().__init__(master)
        self.__driver = driver
        self.__onFinish = onFinish
        self.__strategy = strategy # v0.20
        self.__halfwidth = driver.sweetSpotWidth()
        self.__speed = marker_speed # v0.20
        if strategy is not None: # v0.20
            self.__halfwidth = strategy.applyWidth(self.__halfwidth)
            self.__speed = marker_speed * strategy.getSpeedFactor()
        self.__section = 0
        self.__scores = []
        self.__spins = 0
        self.__markerX = bar_left
        self.__sweetSpot = 0
        self.__waitingForPress = False
        self.__afterId = None
        # v0.20 track view
        self.__animId = None
        self.__limit = 0.0                  
        self.__smoke = []                   # [item, frames old]
        self.__popups = []                  # [item, frames old]
        self.__rival = rival
        self.__gap = start_gap
        self.__gapTarget = start_gap
        self.__rivalWobbleAt = None
        self.__rivalWobble = 0.0
        if rival is not None and rivalScore is not None:
            self.__planRivalMistake(rivalScore)
        # v0.20

        self.title(title) # v0.20 
        self.configure(bg = theme.bg)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.__abandon)

        tk.Label(self, text = f"{driver.getName()} | {driver.getCar().getModel()}",
                 font = theme.fonts["heading"], fg = theme.cyan, bg = theme.bg) .pack(pady = (12, 0))
        details = [] # v0.20
        if strategy is not None:
            details.append(strategy.describe().upper())
        if rival is not None:
            details.append(f"CHASING {rival.getName().upper()}")
        if details:
            tk.Label(self, text = "   ·   ".join(details), font = theme.fonts["small"],
                     fg = theme.muted, bg = theme.bg).pack()

        self.__track = tk.Canvas(self, width = track_width, height = track_height, # v0.20
                                 bg = theme.bg, highlightthickness = 0)
        self.__track.pack(padx = 10, pady = (6, 0))
        self.__drawTrack()
        self.__player = TrackCar(self.__track, theme.pink, "playerCar")
        self.__lead = TrackCar(self.__track, theme.cyan, "leadCar") if rival is not None else None

        self.__sectionLabel = tk.Label(self, text = "", font = theme.fonts["title"],
                                       fg = theme.pink, bg = theme.bg)
        self.__sectionLabel.pack()

        self.__canvas = tk.Canvas(self, width = bar_left * 2 + bar_width , height = 110,
                                  bg = theme.bg, highlightthickness = 0)
        self.__canvas.pack(padx = 10)

        self.__resultLabel = tk.Label(self, text = "Press SPACE to skillcheck",
                                      font = theme.fonts["body"], fg = theme.muted, bg = theme.bg)
        self.__resultLabel.pack(pady = 4)

        self.__hitButton = tk.Button(self, text = "Press SPACE", font = theme.fonts["heading"],
                                     bg = theme.pink, fg = "white", activebackground = theme.cyan,
                                     relief = "flat", width = 16, command = self.__press)
        self.__hitButton.pack(pady = (4, 14))

        self.bind("<space>", lambda e: self.__press())
        self.__centreOver(master)
        self.transient(master)
        self.grab_set()
        self.focus_force()
        self.__afterId = self.after(600, self.__startSection)
        self.__animate() # v0.20

    def __centreOver(self, master):
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_reqwidth()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0 )}")

    # v0.20 track view
    def __drawTrack(self):
        c = self.__track
        rng = random.Random(5)
        for _ in range(140):      # trees and rocks off the road
            x, y = rng.randint(0, track_width), rng.randint(0, track_height)
            nearest = min(math.hypot(x - px, y - py) for px, py in track_points[::3])
            if nearest > road_width:
                size = rng.choice([2, 3, 4])
                c.create_oval(x, y, x + size, y + size, fill = theme.panel, outline = "")
        flat = [v for point in track_points for v in point]
        c.create_line(*self.__offsetLine(road_width / 2 + 10), fill = theme.muted,
                      width = 1, dash = (2, 4))                                   # guardrail
        c.create_line(*flat, fill = theme.cyan, width = road_width + 4,
                      capstyle = "butt", joinstyle = "round")                     # edges
        c.create_line(*flat, fill = theme.panel_light, width = road_width,
                      capstyle = "butt", joinstyle = "round")                     # tarmac
        c.create_line(*flat, fill = "#3b3b60", width = 2, dash = (8, 10))         # centre line
        apex = self.__offsetLine(-road_width / 2 + 3, 0.40, 0.62)                 # kerbs
        c.create_line(*apex, fill = theme.pink, width = 5)
        c.create_line(*apex, fill = "white", width = 5, dash = (6, 6))
        for point in (1 / 3, 2 / 3):                                              # section lines
            x, y, heading = trackPosition(point)
            dx, dy = math.sin(heading) * road_width / 2, -math.cos(heading) * road_width / 2
            c.create_line(x - dx, y - dy, x + dx, y + dy, fill = theme.muted, width = 2)
        for x in (track_points[0][0], track_points[-1][0]):                       # start / finish
            for row in range(2):
                for col in range(6):
                    if (row + col) % 2 == 0:
                        left = x - road_width / 2 + col * road_width / 6
                        c.create_rectangle(left, 212 + row * 5, left + road_width / 6, 217 + row * 5,
                                           fill = "white", outline = "")
        for index, (name, point) in enumerate(zip(sections, (1 / 6, 1 / 2, 5 / 6))):
            x, y, heading = trackPosition(point)
            out = -(road_width / 2 + 28)      # inside the hairpin
            c.create_text(x + math.sin(heading) * out, y - math.cos(heading) * out, text = name,
                          font = theme.fonts["small"], fill = theme.muted, tags = f"label{index}")
        if self.__rival is not None:
            c.create_rectangle(12, 12, 22, 22, fill = theme.pink, outline = "")
            c.create_text(28, 17, text = "YOU", anchor = "w", font = theme.fonts["small"],
                          fill = theme.text)
            c.create_rectangle(12, 30, 22, 40, fill = theme.cyan, outline = "")
            c.create_text(28, 35, text = f"{self.__rival.getName()}  (lead)", anchor = "w",
                          font = theme.fonts["small"], fill = theme.text)

    def __offsetLine(self, offset, start = 0.0, end = 1.0):
        points = []
        steps = 60
        for i in range(steps + 1):
            x, y, heading = trackPosition(start + (end - start) * i / steps)
            points += [x + math.sin(heading) * offset, y - math.cos(heading) * offset]
        return points

    def __planRivalMistake(self, rivalScore):
        if rivalScore >= 88:
            return
        section = random.randrange(len(sections))
        self.__rivalWobbleAt = (section + 0.45) / len(sections)
        self.__rivalWobble = 0.25 if rivalScore >= 75 else 0.5

    def __puff(self, car):
        x, y = car.rear()
        item = self.__track.create_oval(x - 3, y - 3, x + 3, y + 3, fill = "#5a5a78", outline = "")
        self.__smoke.append([item, 0])

    def __popup(self, text, colour):
        x, y, _ = self.__player.position()
        item = self.__track.create_text(x, y - 18, text = text, font = theme.fonts["bodyBold"],
                                        fill = colour)
        self.__popups.append([item, 0])

    def __animate(self):
        try:
            self.__moveCars()
            self.__drawEffects()
        except tk.TclError:      # window closed
            return
        self.__animId = self.after(anim_ms, self.__animate)

    def __moveCars(self):
        step = self.__speed / bar_width / len(sections) * (anim_ms / tick_ms)
        player = self.__player
        player.progress = min(self.__limit, player.progress + step)
        player.update()
        if self.__lead is not None:
            self.__gap += (self.__gapTarget - self.__gap) * 0.05
            lead = self.__lead
            lead.progress = min(1.0, player.progress + self.__gap)
            if self.__rivalWobbleAt is not None and lead.progress >= self.__rivalWobbleAt:
                lead.wobble = self.__rivalWobble
                lead.wide = 10 * self.__rivalWobble
                self.__rivalWobbleAt = None
            lead.update()

    def __drawEffects(self):
        c = self.__track
        cars = [self.__player] + ([self.__lead] if self.__lead is not None else [])
        for car in cars:
            if car.isSliding() and car.progress < 1.0:
                self.__puff(car)
        for puff in self.__smoke[:]:
            item, age = puff
            puff[1] += 1
            if age >= smoke_life:
                c.delete(item)
                self.__smoke.remove(puff)
                continue
            x1, y1, x2, y2 = c.coords(item)
            c.coords(item, x1 - 0.25, y1 - 0.25, x2 + 0.25, y2 + 0.25)
            c.itemconfig(item, fill = animate.blend("#5a5a78", theme.bg, age / smoke_life))
        for popup in self.__popups[:]:
            item, age = popup
            popup[1] += 1
            if age > 30:
                c.delete(item)
                self.__popups.remove(popup)
            else:
                c.move(item, 0, -0.6)
        for car in cars:
            car.draw()
        c.tag_raise("playerCar")
        for item, _ in self.__popups:
            c.tag_raise(item)

    def __reactCar(self, result):
        player = self.__player
        if result == "spin":
            player.spin = 0
            player.wide = 14
        elif result == "sloppy":
            player.wobble = 0.35
            player.wide = 8
        self.__gapTarget = max(0.035, min(0.2, self.__gapTarget + gap_change[result]))
        colours = {"perfect": theme.cyan, "clean": theme.good, "sloppy": theme.warn,
                   "spin": theme.bad}
        self.__popup({"perfect": "PERFECT!", "clean": "CLEAN", "sloppy": "SLOPPY",
                      "spin": "SPUN!"}[result], colours[result])
    # v0.20

    def __drawBar(self):
        c = self.__canvas
        c.delete("all")
        c.create_rectangle(bar_left, 40, bar_left + bar_width, 70,
                           fill = theme.panel, outline = theme.panel_light)
        outer = self.__halfwidth * spin_zone

        c.create_rectangle(self.__sweetSpot - outer, 40, self.__sweetSpot + outer, 70,
                           fill = theme.panel_light, outline = "")
        c.create_rectangle(self.__sweetSpot - self.__halfwidth, 40,
                           self.__sweetSpot + self.__halfwidth, 70,
                           fill = theme.cyan, outline = "")
        c.create_line(self.__sweetSpot, 36, self.__sweetSpot, 74, fill = "white", width = 2)

        for i, name in enumerate(sections):
            text = f"{name}: {self.__scores[i]}" if i < len(self.__scores) else f"{name}: --"
            c.create_text(bar_left + 90 + i * 170, 15, text = text,
                          fill = theme.text, font = theme.fonts["mono"])
        self.__marker = c.create_rectangle(self.__markerX - 3, 30, self.__markerX + 3, 80,
                                           fill = theme.pink, outline = "white")

    def __startSection(self):
        self.__afterId = None
        self.__sectionLabel.config(text = sections[self.__section])
        for index in range(len(sections)): # v0.20
            self.__track.itemconfig(f"label{index}",
                                    fill = theme.cyan if index == self.__section else theme.muted)
        self.__limit = (self.__section + 1) / len(sections) # v0.20
        low = bar_left + self.__halfwidth + 60
        high = bar_left + bar_width - self.__halfwidth - 20
        self.__sweetSpot = random.randint(low, high)
        self.__markerX = bar_left
        self.__waitingForPress = True
        self.__drawBar()
        self.__tick()

    def __tick(self):
        if not self.__waitingForPress:
            return
        self.__markerX += self.__speed # v0.20 was marker_speed
        if self.__markerX > bar_left + bar_width:
            self.__endSection(0, True, "TOO LATE - RAN OUT OF ROAD") # v0.20
            return
        self.__canvas.coords(self.__marker, self.__markerX - 3, 30, self.__markerX + 3, 80)
        self.__afterId = self.after(tick_ms, self.__tick)

    def __press(self):
        if not self.__waitingForPress:
            return
        score, spun = scoreSection(self.__markerX, self.__sweetSpot, self.__halfwidth)
        if spun: # v0.20 real messages
            message = "SPUN OUT! The car takes damage."
        elif score >= 90:
            message = "PERFECT! Right on the line."
        elif score >= 75:
            message = "CLEAN. Good angle."
        else:
            message = "SLOPPY. Lost the angle."
        self.__endSection(score, spun, message)

    def __endSection(self, score, spun, message):
        self.__waitingForPress = False
        if self.__afterId is not None:
            self.after_cancel(self.__afterId)
            self.__afterId = None
        self.__scores.append(score)
        if spun:
            self.__spins += 1
        if spun: # v0.20
            self.__reactCar("spin")
        elif score >= 90:
            self.__reactCar("perfect")
        elif score >= 75:
            self.__reactCar("clean")
        else:
            self.__reactCar("sloppy")
        colour = theme.bad if spun else theme.cyan if score >= 90 else theme.good if score >= 75 else theme.warn # v0.20
        self.__resultLabel.config(text = message, fg = colour) # v0.20
        self.__drawBar()
        self.__section += 1
        if self.__section < len(sections):
            self.__afterId = self.after(900, self.__startSection)
        else:
            self.__limit = 1.0 # v0.20 drive out
            self.__afterId = self.after(1300, self.__finish) # v0.20 was 900

    def __stopAnimation(self): # v0.20
        if self.__animId is not None:
            try:
                self.after_cancel(self.__animId)
            except tk.TclError:
                pass
            self.__animId = None

    def __finish(self):
        total = round(sum(self.__scores) / len(self.__scores))
        self.__stopAnimation() # v0.20
        self.grab_release()
        self.destroy()
        self.__onFinish(total, self.__spins)

    def __abandon(self):
        self.__waitingForPress = False
        if self.__afterId is not None:
            self.after_cancel(self.__afterId)
        self.__stopAnimation() # v0.20
        self.grab_release()
        self.destroy()