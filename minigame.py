import random
import tkinter as tk

import theme

bar_left = 20
bar_width = 520
sections = ["ENTRY", "ANGLE", "EXIT"]
spin_zone = 3
tick_ms = 15
marker_speed = 7

def scoreSection(markerX, sweetSpot, halfwidth):
    distance = abs(markerX - sweetSpot)
    if distance <= halfwidth:
        return round(100 - (distance / halfwidth) * 25), False
    if distance <= halfwidth * spin_zone:
        over = distance - halfwidth
        zone = halfwidth * (spin_zone - 1)
        return round(60 * (1 - over / zone)), False
    return 0, True

class DriftRunWindow(tk.Toplevel):
    def __init__(self, master, driver, onFinish):
        super().__init__(master)
        self.__driver = driver
        self.__onFinish = onFinish
        self.__halfwidth = driver.sweetSpotWidth()
        self.__section = 0
        self.__scores = []
        self.__spins = 0
        self.__markerX = bar_left
        self.__sweetSpot = 0
        self.__waitingForPress = False
        self.__afterId = None
        
        self.title("Qualifying run")
        self.configure(bg = theme.bg)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.__abandon)
        
        tk.Label(self, text = f"{driver.getName()} | {driver.getCar().getModel()}",
                 font = theme.fonts["heading"], fg = theme.cyan, bg = theme.bg) .pack(pady = (12, 0))
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
        
    def __centreOver(self, master):
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_reqwidth()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0 )}")
        
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
        self.__markerX += marker_speed
        if self.__markerX > bar_left + bar_width:
            self.__endSection(0, True, "PLACEHOLDER - RACE LINE LOST")
            return
        self.__canvas.coords(self.__marker, self.__markerX - 3, 30, self.__markerX + 3, 80)
        self.__afterId = self.after(tick_ms, self.__tick)
            
    def __press(self):
        if not self.__waitingForPress:
            return
        score, spun = scoreSection(self.__markerX, self.__sweetSpot, self.__halfwidth)
        if spun:
            message = "PLACEHOLDER - SPINOUT"
        elif score >= 90:
            message = f"PLACEHOLDER - PERFECT"
        elif score >= 75:
            message = f"PLACEHOLDER - CLEAN"
        else:
            message = f"PLACEHOLDER - BAD"
        self.__endSection(score, spun, message)
            
    def __endSection(self, score, spun, message):
        self.__waitingForPress = False
        if self.__afterId is not None:
            self.after_cancel(self.__afterId)
            self.__afterId = None
        self.__scores.append(score)
        if spun:
            self.__spins += 1
        self.__resultLabel.config(text = message, fg = theme.bad if spun else theme.good)
        self.__drawBar()
        self.__section += 1
        if self.__section < len(sections):
            self.__afterId = self.after(900, self.__startSection)
        else:
            self.__afterId = self.after(900, self.__finish)
            
    def __finish(self):
        total = round(sum(self.__scores) / len(self.__scores))
        self.grab_release()
        self.destroy()
        self.__onFinish(total, self.__spins)
        
    def __abandon(self):
        self.__waitingForPress = False
        if self.__afterId is not None:
            self.after_cancel(self.__afterId)
        self.grab_release()
        self.destroy()