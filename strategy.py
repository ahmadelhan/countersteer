# v0.20
import tkinter as tk
from tkinter import messagebox

import theme
import animate
import sound
from models import Strategy
from exceptions import NoTyresLeft

line_text = {
    "Safe":       "Wider target, slower marker, less damage if you spin.  Score -2.",
    "Balanced":   "No changes. What you see is what you get.",
    "Aggressive": "Narrow target, faster marker, more damage if you spin.  Score +5.",
}

_last = {"line": "Balanced", "fresh": False, "pressure": False} 


class ChoiceRow(tk.Frame):
    """A row of toggle buttons where one is selected."""

    def __init__(self, parent, options, selected, onChange):
        super().__init__(parent, bg = theme.bg)
        self.__options = options
        self.__selected = selected
        self.__onChange = onChange
        self.__buttons = []
        for index, label in enumerate(options):
            button = tk.Button(self, text = label.upper(), font = theme.fonts["bodyBold"],
                               relief = "flat", bd = 0, padx = 14, pady = 6, cursor = "hand2",
                               command = lambda i = index: self.select(i))
            button.pack(side = "left", padx = (0, 6))
            button.bind("<Enter>", lambda e, i = index: self.__hover(i, True))
            button.bind("<Leave>", lambda e, i = index: self.__hover(i, False))
            self.__buttons.append(button)
        self.__paint()

    def __base(self, index):
        return theme.pink if index == self.__selected else theme.panel_light

    def __paint(self):
        for index, button in enumerate(self.__buttons):
            colour = self.__base(index)
            button.config(bg = colour, activebackground = animate.lighter(colour),
                          fg = "white" if index == self.__selected else theme.text,
                          activeforeground = "white")

    def __hover(self, index, over):
        button = self.__buttons[index]
        target = animate.lighter(self.__base(index)) if over else self.__base(index)
        if over:
            sound.playSfx("hover")
        animate.fadeColour(button, "bg", button.cget("bg"), target)

    def select(self, index):
        if index != self.__selected:
            sound.playSfx("click")
        self.__selected = index
        self.__paint()
        self.__onChange()

    def getSelected(self):
        return self.__options[self.__selected]


class StrategyDialog(tk.Toplevel):

    def __init__(self, master, driver, onGo, rival = None):
        super().__init__(master)
        self.__driver = driver
        self.__onGo = onGo
        self.__rival = rival
        car = driver.getCar()
        self.title("Strategy")
        self.configure(bg = theme.bg, padx = 24, pady = 18)
        self.resizable(False, False)

        tk.Label(self, text = "RACE STRATEGY", font = theme.fonts["heading"], fg = theme.pink,
                 bg = theme.bg).pack(anchor = "w")
        info = f"{driver.getName()}  ·  {car.getModel()}  ·  {car.getTyresets()} tyre set(s)"
        if rival is not None:
            info += f"\nChasing {rival.getName()}  (rating {rival.getRating()})"
        tk.Label(self, text = info, font = theme.fonts["body"], fg = theme.muted, bg = theme.bg,
                 justify = "left").pack(anchor = "w", pady = (2, 12))

        line = Strategy.line_order.index(_last["line"])
        self.__line = self.__section("LINE", Strategy.line_order, line)
        self.__lineInfo = self.__note()

        fresh = 1 if _last["fresh"] and car.getTyresets() >= Strategy.fresh_tyre_sets else 0
        self.__tyres = self.__section("TYRES", ["Used", "Fresh"], fresh)
        self.__tyreInfo = self.__note()

        self.__pressure = None
        if rival is not None:
            self.__pressure = self.__section("PRESSURE", ["Off", "On"], 1 if _last["pressure"] else 0)
            self.__note(f"On: timing {Strategy.pressure_timing}+ knocks "
                        f"{Strategy.pressure_rival_loss} off {rival.getName()}'s score. "
                        f"Under {Strategy.pressure_timing} costs you {Strategy.pressure_own_loss}.")

        self.__preview = tk.Label(self, text = "", font = theme.fonts["mono"], fg = theme.cyan,
                                  bg = theme.panel, padx = 10, pady = 6, anchor = "w")
        self.__preview.pack(fill = "x", pady = (14, 12))

        buttons = tk.Frame(self, bg = theme.bg)
        buttons.pack(fill = "x")
        animate.styleButton(tk.Button(buttons, text = "CANCEL", command = self.__cancel,
                                      font = theme.fonts["bodyBold"], bg = theme.panel_light,
                                      fg = "white", relief = "flat", bd = 0, padx = 16, pady = 8,
                                      cursor = "hand2"), theme.panel_light).pack(side = "left")
        animate.styleButton(tk.Button(buttons, text = "GO  ▶", command = self.__go,
                                      font = theme.fonts["bodyBold"], bg = theme.pink,
                                      fg = "white", relief = "flat", bd = 0, padx = 22, pady = 8,
                                      cursor = "hand2"), theme.pink).pack(side = "right")

        self.bind("<Return>", lambda e: self.__go())
        self.bind("<Escape>", lambda e: self.__cancel())
        self.protocol("WM_DELETE_WINDOW", self.__cancel)
        self.__update()

        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_reqwidth()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.transient(master)
        self.grab_set()
        self.focus_force()

    def __section(self, title, options, selected):
        tk.Label(self, text = title, font = theme.fonts["bodyBold"], fg = theme.cyan,
                 bg = theme.bg).pack(anchor = "w")
        row = ChoiceRow(self, options, selected, self.__update)
        row.pack(anchor = "w", pady = (4, 2))
        return row

    def __note(self, text = ""):
        label = tk.Label(self, text = text, font = theme.fonts["small"], fg = theme.muted,
                         bg = theme.bg, justify = "left", wraplength = 430)
        label.pack(anchor = "w", pady = (0, 10))
        return label

    def __strategy(self):
        pressure = self.__pressure is not None and self.__pressure.getSelected() == "On"
        return Strategy(self.__line.getSelected(), self.__tyres.getSelected() == "Fresh", pressure)

    def __update(self):
        strategy = self.__strategy()
        car = self.__driver.getCar()
        self.__lineInfo.config(text = line_text[strategy.getLine()])
        needed = strategy.getTyreSets()
        if strategy.hasFreshTyres() and car.getTyresets() < needed:
            self.__tyreInfo.config(text = f"Fresh tyres use {needed} sets. You only have "
                                          f"{car.getTyresets()}.", fg = theme.warn)
        else:
            self.__tyreInfo.config(text = f"Fresh: wider target, uses {Strategy.fresh_tyre_sets} "
                                          f"tyre sets instead of 1.", fg = theme.muted)
        base = self.__driver.sweetSpotWidth()
        bonus = strategy.getBonus()
        self.__preview.config(
            text = f"TARGET ±{base} → ±{strategy.applyWidth(base)}px   "
                   f"SPEED ×{strategy.getSpeedFactor()}   SCORE {bonus:+d}")

    def __go(self):
        strategy = self.__strategy()
        try:
            strategy.checkTyres(self.__driver.getCar())
        except NoTyresLeft as error:
            messagebox.showerror("Not enough tyres", str(error), parent = self)
            return
        _last["line"] = strategy.getLine()
        _last["fresh"] = strategy.hasFreshTyres()
        _last["pressure"] = strategy.hasPressure()
        self.grab_release()
        self.destroy()
        self.__onGo(strategy)

    def __cancel(self):
        self.grab_release()
        self.destroy()