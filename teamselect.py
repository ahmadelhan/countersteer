import tkinter as tk
from tkinter import messagebox

import theme
import carcard
import animate # v0.19
from models import Draft
from exceptions import (
    DuplicateDriver,
    SquadFull,
    InsufficientFunds,
    DraftIncomplete,
    InvalidTeamName
)


card_width = 380    
card_height = 300


def button(parent, text, command, colour = theme.panel_light, fg = "white"):
    return animate.styleButton(tk.Button(parent, text = text, command = command, font = theme.fonts["bodyBold"],
                     bg = colour, fg = fg, activebackground = theme.cyan,
                     activeforeground = theme.bg, relief = "flat", bd = 0,
                     padx = 16, pady = 8, cursor = "hand2"), colour) # v0.19 hover glow + click pulse


def heading(parent, text, size = 26, colour = theme.pink, bg = theme.bg):
    family = theme.fonts["title"][0]
    return tk.Label(parent, text = text, font = (family, size, "bold"), fg = colour, bg = bg)

class TeamSelectScreen(tk.Frame):

    def __init__(self, master, presetTeam, draftBudget, onPreset, onCreate, onBack):
        super().__init__(master, bg = theme.bg)
        self.__presetTeam = presetTeam

        heading(self, "CHOOSE TEAM").pack(pady = (34, 2))
        tk.Label(self, text = "Sign NLR or form new team.",
                 font = theme.fonts["body"], fg = theme.muted, bg = theme.bg).pack()

        cards = tk.Frame(self, bg = theme.bg)
        cards.pack(pady = 30)

        # preset card
        preset = self.__makeCard(cards, "PRESET TEAM")
        preset.pack(side = "left", padx = 16)
        heading(preset, presetTeam.getName(), size = 18, colour = theme.text,
                bg = theme.panel).pack(anchor = "w", pady = (4, 2))
        tk.Label(preset, text = f"Budget  €{presetTeam.getBudget():,}", font = theme.fonts["mono"],
                 fg = theme.cyan, bg = theme.panel).pack(anchor = "w", pady = (0, 14))
        for driver in presetTeam.getDrivers():
            row = tk.Frame(preset, bg = theme.panel)
            row.pack(fill = "x", pady = 3)
            tk.Label(row, text = driver.getName(), font = theme.fonts["bodyBold"], fg = theme.text,
                     bg = theme.panel).pack(side = "left")
            tk.Label(row, text = f"{driver.getSkill()}  ·  {driver.getCar().getModel()}",
                     font = theme.fonts["small"], fg = theme.muted,
                     bg = theme.panel).pack(side = "right")
        tk.Label(preset, text = "A balanced team.", font = theme.fonts["small"],
                 fg = theme.muted, bg = theme.panel).pack(anchor = "w", pady = (14, 0))
        button(preset, "RACE WITH THIS TEAM", lambda: onPreset(self.__presetTeam),
               colour = theme.pink).pack(side = "bottom", fill = "x")

        # create card
        create = self.__makeCard(cards, "NEW TEAM DRAFT")
        create.pack(side = "left", padx = 16)
        heading(create, "Team Drafting", size = 18, colour = theme.text,
                bg = theme.panel).pack(anchor = "w", pady = (4, 2))
        tk.Label(create, text = f"Draft budget  €{draftBudget:,}", font = theme.fonts["mono"],
                 fg = theme.cyan, bg = theme.panel).pack(anchor = "w", pady = (0, 14))
        for line in ["Name team",
                     f"Draft {Draft.team_size} drivers",
                     "Every driver has a signing fee",
                     "Remaining cash becomes season budget"]:
            tk.Label(create, text = f"▸  {line}", font = theme.fonts["body"], fg = theme.text,
                     bg = theme.panel).pack(anchor = "w", pady = 3)
        tk.Label(create, text = "One star, or three solid drivers?", font = theme.fonts["small"],
                 fg = theme.muted, bg = theme.panel).pack(anchor = "w", pady = (14, 0))
        button(create, "BUILD NEW TEAM", onCreate, colour = theme.cyan,
               fg = theme.bg).pack(side = "bottom", fill = "x")

        bottom = tk.Frame(self, bg = theme.bg)
        bottom.pack(side = "bottom", fill = "x", padx = 24, pady = 20)
        button(bottom, "◀  BACK", onBack).pack(side = "left")

    def __makeCard(self, parent, tag):
        card = tk.Frame(parent, bg = theme.panel, width = 400, height = 400,
                        padx = 22, pady = 18, highlightthickness = 2,
                        highlightbackground = theme.panel_light)
        card.pack_propagate(False)
        tk.Label(card, text = tag, font = theme.fonts["small"], fg = theme.cyan,
                 bg = theme.panel).pack(anchor = "w")
        return card


class DraftScreen(tk.Frame):

    def __init__(self, master, draft, onDone, onBack):
        super().__init__(master, bg = theme.bg)
        self.__draft = draft
        self.__onDone = onDone
        self.__selected = 0
        self.__rows = []           

        # top bar
        top = tk.Frame(self, bg = theme.bg)
        top.pack(fill = "x", padx = 20, pady = (16, 6))
        heading(top, "BUILD NEW TEAM", size = 22).pack(side = "left")
        money = tk.Frame(top, bg = theme.bg)
        money.pack(side = "right")
        tk.Label(money, text = "LEFT TO SPEND", font = theme.fonts["small"], fg = theme.muted,
                 bg = theme.bg).pack(anchor = "e")
        self.__budgetLabel = tk.Label(money, text = "", font = theme.fonts["monoBig"],
                                      fg = theme.cyan, bg = theme.bg)
        self.__budgetLabel.pack(anchor = "e")

        # team name
        nameRow = tk.Frame(self, bg = theme.bg)
        nameRow.pack(fill = "x", padx = 20, pady = (0, 10))
        tk.Label(nameRow, text = "TEAM NAME", font = theme.fonts["bodyBold"], fg = theme.pink,
                 bg = theme.bg).pack(side = "left")
        self.__nameEntry = tk.Entry(nameRow, font = theme.fonts["body"], bg = theme.panel_light,
                                    fg = theme.text, insertbackground = theme.text,
                                    relief = "flat", width = 30)
        self.__nameEntry.pack(side = "left", padx = 12, ipady = 4)
        tk.Label(nameRow, text = f"max {Draft.max_name_length} characters",
                 font = theme.fonts["small"], fg = theme.muted, bg = theme.bg).pack(side = "left")

        # middle - pool list & car profile
        middle = tk.Frame(self, bg = theme.bg)
        middle.pack(fill = "x", padx = 20)

        right = tk.Frame(middle, bg = theme.bg)
        right.pack(side = "right", fill = "y", padx = (14, 0))
        self.__card = tk.Canvas(right, width = card_width, height = card_height, bg = theme.panel,
                                highlightthickness = 0, cursor = "hand2")
        self.__card.pack()
        self.__turntable = carcard.Turntable(self.__card, "draft")  # v0.15
        buttons = tk.Frame(right, bg = theme.bg)
        buttons.pack(fill = "x", pady = 8)
        button(buttons, "DRAFT DRIVER", self.__draftSelected,
               colour = theme.pink).pack(side = "left", expand = True, fill = "x", padx = (0, 4))
        button(buttons, "REMOVE", self.__removeSelected).pack(side = "left", expand = True,
                                                             fill = "x", padx = (4, 0))

        poolPanel = tk.Frame(middle, bg = theme.panel, padx = 10, pady = 8)
        poolPanel.pack(side = "left", fill = "both", expand = True)
        self.__buildPoolList(poolPanel)

        # slots
        slotsRow = tk.Frame(self, bg = theme.bg)
        slotsRow.pack(fill = "x", padx = 20, pady = (4, 0))
        tk.Label(slotsRow, text = "YOUR DRIVERS", font = theme.fonts["bodyBold"], fg = theme.pink,
                 bg = theme.bg).pack(anchor = "w", pady = (0, 4))
        slots = tk.Frame(slotsRow, bg = theme.bg)
        slots.pack(fill = "x")
        self.__slotLabels = []
        for i in range(Draft.team_size):
            label = tk.Label(slots, text = "", font = theme.fonts["body"], bg = theme.panel,
                             width = 30, height = 2, justify = "center")
            label.pack(side = "left", expand = True, fill = "x", padx = (0 if i == 0 else 6, 0))
            self.__slotLabels.append(label)

        # bottom bar
        bottom = tk.Frame(self, bg = theme.bg)
        bottom.pack(side = "bottom", fill = "x", padx = 20, pady = 14)
        button(bottom, "◀  BACK", onBack).pack(side = "left")
        button(bottom, "START SEASON  ▶", self.__startSeason, colour = theme.pink).pack(side = "right")

        self.__refresh()
        self.__nameEntry.focus_set()

    def __buildPoolList(self, parent):
        columns = [("", 2), ("DRIVER", 15), ("SKILL", 5), ("CAR", 19), ("FEE", 8)]
        header = tk.Frame(parent, bg = theme.panel)
        header.pack(fill = "x", pady = (0, 4))
        for text, width in columns:
            tk.Label(header, text = text, width = width, anchor = "w", font = theme.fonts["body"],
                     fg = theme.cyan, bg = theme.panel).pack(side = "left")

        for index in range(self.__draft.getPoolSize()):
            driver = self.__draft.getDriver(index)
            row = tk.Frame(parent, bg = theme.panel, cursor = "hand2")
            row.pack(fill = "x", pady = 1)
            values = ["", driver.getName(), str(driver.getSkill()), driver.getCar().getModel(),
                      f"€{self.__draft.getFee(index):,}"]
            labels = []
            for (text, width), value in zip(columns, values):
                label = tk.Label(row, text = value, width = width, anchor = "w",
                                 font = theme.fonts["body"], bg = theme.panel, fg = theme.text)
                label.pack(side = "left", ipady = 3)
                labels.append(label)

            for widget in [row] + labels:
                widget.bind("<Button-1>", lambda e, i = index: self.__select(i))
                widget.bind("<Double-Button-1>", lambda e, i = index: self.__toggle(i))
            self.__rows.append({"frame": row, "labels": labels})

    def __styleRows(self):
        for index, row in enumerate(self.__rows):
            picked = self.__draft.isPicked(index)
            selected = index == self.__selected
            bg = theme.panel_light if selected else theme.panel
            row["frame"].config(bg = bg)
            for column, label in enumerate(row["labels"]):
                fg = theme.text
                if column == 1 and picked:
                    fg = theme.cyan
                elif column == 1 and selected:
                    fg = theme.pink
                label.config(bg = bg, fg = fg)
            row["labels"][0].config(text = "X" if picked else "", fg = theme.cyan)

    def __refresh(self):
        self.__budgetLabel.config(text = f"€{self.__draft.getBudgetLeft():,}")
        self.__styleRows()
        self.__drawCard()
        picked = self.__draft.getPicked()
        for i, label in enumerate(self.__slotLabels):
            if i < len(picked):
                d = picked[i]
                label.config(text = f"{d.getName()}\nskill {d.getSkill()}  ·  {d.getCar().getModel()}",
                             fg = theme.cyan)
            else:
                label.config(text = "EMPTY SLOT", fg = theme.muted)

    def __drawCard(self):
        index = self.__selected
        driver = self.__draft.getDriver(index)
        car = driver.getCar()
        c = self.__card
        c.delete("all")
        c.create_text(18, 22, text = driver.getName().upper(), anchor = "w",
                      font = theme.fonts["heading"], fill = theme.pink)
        c.create_text(18, 44, anchor = "w", font = theme.fonts["small"], fill = theme.muted,
                      text = f"Fee €{self.__draft.getFee(index):,}   ·   "
                             f"Wage €{driver.getWage():,} per round")
        if self.__draft.isPicked(index):
            c.create_text(card_width - 16, 22, text = "DRAFTED", anchor = "e",
                          font = theme.fonts["bodyBold"], fill = theme.cyan)

        # v0.15 spinning car
        if not self.__turntable.show(car.getImagePath(), card_width // 2, 130):
            carcard.drawSilhouette(c, (card_width - 306) // 2, 80)

        c.create_text(card_width // 2, 214, text = car.getModel().upper(), font = theme.fonts["heading"],
                      fill = theme.cyan)
        carcard.drawStatBar(c, 18, 240, "SKILL", driver.getSkill(), 100,
                            str(driver.getSkill()), theme.pink, barWidth = 190)
        carcard.drawStatBar(c, 18, 262, "POWER", car.getHorsepower(), 400,
                            f"{car.getHorsepower()} hp", theme.cyan, barWidth = 190)
        carcard.drawStatBar(c, 18, 284, "ANGLE", car.getSteeringAngle(), 70,
                            f"{car.getSteeringAngle()}°", theme.cyan, barWidth = 190)

    def __select(self, index):
        self.__selected = index
        self.__refresh()

    def __toggle(self, index):
        self.__selected = index
        if self.__draft.isPicked(index):
            self.__removeSelected()
        else:
            self.__draftSelected()

    def __draftSelected(self):
        try:
            self.__draft.pick(self.__selected)
        except DuplicateDriver as error:
            messagebox.showerror("Already drafted", str(error))
        except SquadFull as error:
            messagebox.showerror("Team full", str(error))
        except InsufficientFunds as error:
            messagebox.showerror("Not enough money", str(error))
        self.__refresh()

    def __removeSelected(self):
        if not self.__draft.isPicked(self.__selected):
            messagebox.showinfo("Remove", f"{self.__draft.getDriver(self.__selected).getName()} "
                                          "isn't on your team.")
            return
        self.__draft.unpick(self.__selected)
        self.__refresh()

    def __startSeason(self):
        try:
            team = self.__draft.buildTeam(self.__nameEntry.get())
        except InvalidTeamName as error:
            messagebox.showerror("Team name", str(error))
            self.__nameEntry.focus_set()
            return
        except DraftIncomplete as error:
            messagebox.showerror("Draft incomplete", str(error))
            return
        self.__onDone(team)