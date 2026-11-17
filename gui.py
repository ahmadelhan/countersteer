import os
import tkinter as tk
from tkinter import ttk, messagebox

import theme
from data import createStartingTeam, makeCar, signingFee, wageFor, car_catalogue
from models import Driver, Team, Car
from minigame import DriftRunWindow
from exceptions import (
    NoTyresLeft,
    CarDamaged,
    InsufficientFunds,
    SquadFull,
    MinimumSquad,
    DuplicateDriver,
    NoRunsRecorded,
    MaxTune
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sort_options = ["Best score", "Average score", "Skill", "Condition"]

def centreOver (window, master):
    window.update_idletasks()
    x = master.winfo_rootx() + (master.winfo_width() - window.winfo_reqwidth()) // 2
    y = master.winfo_rooty() + (master.winfo_height() - window.winfo_reqheight()) // 2
    window.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    
def makeButton(parent, text, command, colour = theme.panel_light, width = None):
    button = tk.Button(parent, text = text, command = command, font = theme.fonts["bodyBold"],
                       bg = colour, fg = "white", activebackground = theme.cyan,
                       activeforeground = theme.bg, relief = "flat", bd = 0, padx = 10, pady = 6,
                       cursor = "hand2")
    if width:
        button.config(width = width)
    return button

class Countersteer:
    
    def __init__(self, root):
        self.root = root
        self.team = createStartingTeam()
        self.current = 0
        self.runningDriver = None
        self.images = {}
        
        root.title("Countersteer")
        root.geometry("960x680")
        root.configure(bg = theme.bg)
        root.resizable(False, False)
        
        self.setupStyles()
        self.buildMenu()
        self.buildHeader()
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill = "both", expand = True, padx = 12, pady = (0, 6))
        self.buildGarageTab()
        self.buildShopTab()
        self.buildLeaderboardTab()
        self.statusLabel = tk.Label(root, text = "Welcome to the paddock.", anchor = "w",
                                    font = theme.fonts["small"], fg = theme.muted, bg = theme.bg)
        self.statusLabel.pack(fill = "x", padx = 14, pady = (0, 8))

        self.refresh()
    
    def setupStyles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background = theme.bg, borderwidth = 0)
        style.configure("TNotebook.Tab", background = theme.panel, foreground = theme.muted,
                        font = theme.fonts["bodyBold"], padding = (18, 8), borderwidth = 0)
        style.map("TNotebook.Tab",
                  background =[("selected", theme.pink)],
                  foreground = [("selected", "white")])
        style.configure("Treeview", background = theme.panel, fieldbackground = theme.panel,
                        foreground = theme.text, font = theme.fonts["body"],
                        borderwidth = 0)
        style.map("Treeview", background = [("selected", theme.pink)])
        style.configure("Treeview.Heading", background = theme.panel_light,
                        foreground = theme.cyan, font = theme.fonts["bodyBold"],
                        relief = "flat")
        style.configure("TCombobox", fieldbackground = theme.panel_light,
                        background = theme.panel_light, foreground = theme.text,
                        arrowcolor = theme.cyan)
        style.map("TCombobox",
                  fieldbackground = [("readonly", theme.panel_light)],
                  foreground = [("readonly", theme.text)],
                  selectbackground = [("readonly", theme.panel_light)],
                  selectforeground = [("readonly", theme.text)])
        self.root.option_add("*TCombobox*Listbox.background", theme.panel)
        self.root.option_add("*TCombobox*Listbox.foreground", theme.text)
        self.root.option_add("*TCombobox*Listbox.selectBackground", theme.pink)
        
    def buildMenu(self):
            menuBar = tk.Menu(self.root)
            self.root.config(menu = menuBar)
    
            teamMenu = tk.Menu(menuBar, tearoff = 0)
            menuBar.add_cascade(label = "Team", menu = teamMenu)
            teamMenu.add_command(label = "New sign ons...", command = self.openSignDialog)
            teamMenu.add_command(label = "Release current driver", command = self.releaseCurrent)
            teamMenu.add_separator()
            teamMenu.add_command(label = "Reset", command = self.resetTeam)
            teamMenu.add_separator()
            teamMenu.add_command(label = "Exit", command = self.root.destroy)
    
            helpMenu = tk.Menu(menuBar, tearoff=0)
            menuBar.add_cascade(label = "Help", menu = helpMenu)
            helpMenu.add_command(label = "Manual", command = self.showHelp)

    def buildHeader(self):
        header = tk.Frame(self.root, bg = theme.bg)
        header.pack(fill = "x", padx = 14, pady = (10, 8))
        tk.Label(header, text="Countersteer", font = theme.fonts["title"],
                 fg = theme.pink, bg = theme.bg).pack(side = "left")
        right = tk.Frame(header, bg = theme.bg)
        right.pack(side ="right")
        tk.Label(right, text=self.team.getName().upper(), font = theme.fonts["small"],
                 fg = theme.muted, bg = theme.bg).pack(anchor = "e")
        self.budgetLabel = tk.Label(right, text = "", font = theme.fonts["monoBig"],
                                    fg=theme.cyan, bg=theme.bg)
        self.budgetLabel.pack(anchor = "e")


    def makePanel(self, parent):
        return tk.Frame(parent, bg = theme.panel, padx = 14, pady = 12)
    
    def makeNavBar(self, parent):
        bar = tk.Frame(parent, bg = theme.bg)
        for text, command in [("<< First", self.firstCmd), ("< Prev", self.prevCmd),
                              ("Next >", self.nextCmd), ("Last >>", self.lastCmd)]:
            makeButton(bar, text, command, width=8).pack(side = "left", padx = 3)
        label = tk.Label(bar, text = "", font = theme.fonts["body"], fg = theme.muted, bg = theme.bg)
        label.pack(side = "left", padx = 12)
        return bar, label
    
    def buildGarageTab(self):
        tab = tk.Frame(self.notebook, bg = theme.bg)
        self.notebook.add(tab, text = "GARAGE")

        top = tk.Frame(tab, bg=theme.bg)
        top.pack(fill = "both", expand = True, pady = 10)
    
        driverPanel = self.makePanel(top)
        driverPanel.pack(side = "left", fill = "y", padx = (0, 10))
        tk.Label(driverPanel, text = "DRIVER", font = theme.fonts["heading"],
                 fg = theme.pink, bg = theme.panel).grid(row = 0, column = 0, columnspan = 2,
                                                          sticky ="w", pady = (0, 8))
        self.driverFields = {}
        fields = ["Name", "Skill", "Wage / round", "Runs", "Last run", "Average", "Best"]
        for row, field in enumerate(fields, start = 1):
            tk.Label(driverPanel, text = field, font = theme.fonts["body"], fg = theme.muted,
                     bg = theme.panel, width = 12, anchor = "w").grid(row = row, column = 0, sticky = "w", pady = 3)
            value = tk.Label(driverPanel, text = "", font = theme.fonts["bodyBold"], fg=theme.text,
                            bg = theme.panel, width = 16, anchor = "w")
            value.grid(row = row, column = 1, sticky = "w", pady = 3)
            self.driverFields[field] = value
    
        makeButton(driverPanel, "Check average score", self.checkAverage).grid(
            row = 10, column = 0, columnspan = 2, sticky = "we", pady = (16, 4))
        makeButton(driverPanel, "Check best score", self.checkBest).grid(
            row = 11, column = 0, columnspan = 2, sticky = "we", pady = 4)
    
        self.garageCarCanvas = tk.Canvas(top, width = 520, height = 330, bg = theme.panel,
                                        highlightthickness = 0)
        self.garageCarCanvas.pack(side = "left", fill = "both", expand = True)
    
        bottom = tk.Frame(tab, bg = theme.bg)
        bottom.pack(fill = "x", pady = (0, 10))
        nav, self.garagePosLabel = self.makeNavBar(bottom)
        nav.pack(side = "left")
        makeButton(bottom, "START QUALIFYING RUN", self.startRun,
                    colour=theme.pink).pack(side = "right", ipadx = 10, ipady = 4)
        
    def buildShopTab(self):
        tab = tk.Frame(self.notebook, bg = theme.bg)
        self.notebook.add(tab, text = "SHOP")

        top = tk.Frame(tab, bg = theme.bg)
        top.pack(fill = "both", expand = True, pady = 10)

        shopPanel = self.makePanel(top)
        shopPanel.pack(side = "left", fill = "y", padx = (0, 10))
        tk.Label(shopPanel, text = "WORKSHOP", font = theme.fonts["heading"],
                 fg=theme.pink, bg=theme.panel).pack(anchor = "w")
        self.shopDriverLabel = tk.Label(shopPanel, text = "", font = theme.fonts["body"],
                                        fg = theme.text, bg = theme.panel, justify = "left")
        self.shopDriverLabel.pack(anchor = "w", pady = (4, 12))

        self.tyreButton = makeButton(shopPanel, "", self.buyTyres, width = 26)
        self.tyreButton.pack(fill = "x", pady = 4)
        self.repairButton = makeButton(shopPanel, "", self.repairCar, width = 26)
        self.repairButton.pack(fill = "x", pady = 4)
        self.upgradeButton = makeButton(shopPanel, "", self.upgradeCar, width = 26)
        self.upgradeButton.pack(fill = "x", pady = 4)

        tk.Label(shopPanel, text = "ROSTER", font = theme.fonts["heading"],
                 fg = theme.pink, bg=theme.panel).pack(anchor = "w", pady = (22, 4))
        makeButton(shopPanel, "Sign new driver...", self.openSignDialog,
                   colour=theme.pink).pack(fill = "x", pady = 4)
        makeButton(shopPanel, "Release current driver", self.releaseCurrent).pack(fill = "x", pady = 4)

        self.shopCarCanvas = tk.Canvas(top, width = 520, height = 330, bg = theme.panel,
                                       highlightthickness = 0)
        self.shopCarCanvas.pack(side = "left", fill = "both", expand = True)

        bottom = tk.Frame(tab, bg = theme.bg)
        bottom.pack(fill = "x", pady = (0, 10))
        nav, self.shopPosLabel = self.makeNavBar(bottom)
        nav.pack(side = "left")

    def buildLeaderboardTab(self):
        tab = tk.Frame(self.notebook, bg = theme.bg)
        self.notebook.add(tab, text = "LEADERBOARD")

        controls = tk.Frame(tab, bg = theme.bg)
        controls.pack(fill = "x", pady = 10)
        tk.Label(controls, text = "Sort by", font = theme.fonts["body"], fg = theme.muted,
                 bg=theme.bg).pack(side = "left")
        self.sortVar = tk.StringVar(value = sort_options[0])
        sortBox = ttk.Combobox(controls, textvariable = self.sortVar, values = sort_options,
                               state = "readonly", width = 16)
        sortBox.pack(side = "left", padx=8)
        sortBox.bind("<<ComboboxSelected>>", lambda event: self.refreshLeaderboard())
        self.readyOnlyVar = tk.IntVar(value = 0)
        tk.Checkbutton(controls, text = "Only drivers ready to run", variable = self.readyOnlyVar,
                       command = self.refreshLeaderboard, font = theme.fonts["body"],
                       fg = theme.text, bg = theme.bg, selectcolor = theme.panel,
                       activebackground = theme.bg, activeforeground=theme.cyan).pack(side = "left", padx = 12)
        makeButton(controls, "Show top driver", self.showTopDriver,
                   colour = theme.pink).pack(side = "right")

        columns = ("rank", "driver", "car", "skill", "runs", "best", "average", "condition", "tyres", "status")
        headings = ("#", "Driver", "Car", "Skill", "Runs", "Best", "Avg", "Cond.", "Tyres", "Status")
        widths = (40, 140, 180, 60, 60, 60, 60, 70, 60, 110)
        self.table = ttk.Treeview(tab, columns=columns, show = "headings", height = 12)
        for column, heading, width in zip(columns, headings, widths):
            self.table.heading(column, text = heading)
            anchor = "w" if column in ("driver", "car", "status") else "center"
            self.table.column(column, width = width, anchor = anchor)
        self.table.pack(fill = "both", expand = True)
        self.table.bind("<Double-1>", self.selectFromTable)

        self.readyLabel = tk.Label(tab, text = "", font = theme.fonts["body"], fg=theme.muted,
                                   bg=theme.bg, anchor = "w")
        self.readyLabel.pack(fill = "x", pady = 8)

    def currentDriver(self):
        return self.team.getDriver(self.current)

    def setStatus(self, message):
        self.statusLabel.config(text = message)

    def refresh(self):
        self.budgetLabel.config(text = f"€{self.team.getBudget():,}")
        self.refreshGarage()
        self.refreshShop()
        self.refreshLeaderboard()

    def refreshGarage(self):
        driver = self.currentDriver()
        scores = driver.getRunScores()
        fields = self.driverFields
        fields["Name"].config(text = driver.getName())
        fields["Skill"].config(text = f"{driver.getSkill()} / 100")
        fields["Wage / round"].config(text = f"€{driver.getWage():,}")
        fields["Runs"].config(text = str(driver.getRunsCompleted()))
        fields["Last run"].config(text = str(scores[-1]) if scores else "--")
        try:
            fields["Average"].config(text = str(driver.getAverageScore()))
            fields["Best"].config(text = str(driver.getBestScore()))
        except NoRunsRecorded:
            fields["Average"].config(text = "--")
            fields["Best"].config(text = "--")
        position = f"Driver {self.current + 1} of {self.team.getSize()}"
        self.garagePosLabel.config(text = position)
        self.drawCarCard(self.garageCarCanvas, driver)
        
    def refreshShop(self):
        driver = self.currentDriver()
        car = driver.getCar()
        self.shopDriverLabel.config(
            text=f"{driver.getName()}\n{car.getModel()}\n"
                 f"Condition {car.getCondition()}%  |  Tyres {car.getTyresets()}  |  Tune {car.getTuneLevel()}")
        self.tyreButton.config(text=f"Buy tyre set  (€{Team.tyre_price:,})")
        repairCost = car.getRepairCost()
        self.repairButton.config(text=f"Repair car  (€{repairCost:,})" if repairCost
                                 else "Repair car  (no damage)")
        if car.getTuneLevel() >= Car.max_tune:
            self.upgradeButton.config(text="Upgrade tune  (MAX)")
        else:
            self.upgradeButton.config(
                text=f"Upgrade tune to {car.getTuneLevel() + 1}  (€{car.getUpgradeCost():,})")
        self.shopPosLabel.config(text=f"Driver {self.current + 1} of {self.team.getSize()}")
        self.drawCarCard(self.shopCarCanvas, driver)
        
    def refreshLeaderboard(self):
        self.table.delete(*self.table.get_children())
        drivers = self.team.getSortedDrivers(self.sortVar.get())
        if self.readyOnlyVar.get() == 1:
            drivers = [d for d in drivers if d.getCar().isReady()]
        for rank, driver in enumerate(drivers, start=1):
            car = driver.getCar()
            try:
                best = driver.getBestScore()
                average = driver.getAverageScore()
            except NoRunsRecorded:
                best = average = "--"
            status = "Ready" if car.isReady() else "Needs Shop"
            self.table.insert("", "end", iid=driver.getName(), values=(
                rank, driver.getName(), car.getModel(), driver.getSkill(),
                driver.getRunsCompleted(), best, average,
                f"{car.getCondition()}%", car.getTyresets(), status))
        ready = len(self.team.getDriversReady())
        self.readyLabel.config(
            text=f"Ready to run: {ready} of {self.team.getSize()} drivers   "
                 f"(double-click a driver to open them in the garage)")

    def loadCarImage(self, path): # IMAGE PATH - FOR FUTURE SPRITE USE
        if path in self.images:
            return self.images[path]
        image = None
        fullPath = os.path.join(BASE_DIR, path)
        if path and os.path.exists(fullPath):
            try:
                image = tk.PhotoImage(file=fullPath)
            except tk.TclError:
                image = None
        self.images[path] = image
        return image
    
    def drawCarCard(self, canvas, driver):
        car = driver.getCar()
        c = canvas
        c.delete("all")
        c.create_text(20, 24, text=car.getModel().upper(), anchor = "w",
                      font = theme.fonts["heading"], fill = theme.cyan)
        c.create_text(20, 46, text=f"Driven by {driver.getName()}", anchor = "w",
                      font = theme.fonts["small"], fill = theme.muted)

        image = self.loadCarImage(car.getImagePath())
        if image is not None:
            c.create_image(260, 120, image=image)
        else:
            self.drawSilhouette(c, 110, 70)

        stats = [
            ("POWER", car.getHorsepower(), 400, f"{car.getHorsepower()} hp", theme.pink),
            ("ANGLE", car.getSteeringAngle(), 70, f"{car.getSteeringAngle()}°", theme.pink),
            ("TUNE", car.getTuneLevel(), Car.max_tune, f"{car.getTuneLevel()} / {Car.max_tune}", theme.cyan),
            ("CONDITION", car.getCondition(), 100, f"{car.getCondition()}%", self.conditionColour(car)),
        ]
        y = 200
        for label, value, maximum, text, colour in stats:
            c.create_text(20, y, text=label, anchor="w", font=theme.fonts["small"], fill=theme.muted)
            c.create_rectangle(110, y - 6, 410, y + 6, fill=theme.panel_light, outline="")
            c.create_rectangle(110, y - 6, 110 + 300 * value / maximum, y + 6, fill=colour, outline="")
            c.create_text(420, y, text=text, anchor="w", font=theme.fonts["mono"], fill=theme.text)
            y += 26
        tyres = car.getTyresets()
        c.create_text(20, y, text="TYRES", anchor="w", font=theme.fonts["small"], fill=theme.muted)
        c.create_text(110, y, text=("● " * tyres) if tyres else "NONE LEFT", anchor="w",
                      font=theme.fonts["bodyBold"], fill=theme.cyan if tyres else theme.bad)
        
    def conditionColour(self, car):
        if car.getCondition() < Car.min_run_condition:
            return theme.bad
        if car.getCondition() < 60:
            return theme.warn
        return theme.good
    
    def drawSilhouette(self, c, x, y):
        body = [0, 70, 6, 50, 60, 42, 105, 14, 195, 12, 245, 38, 300, 46, 306, 70]
        c.create_polygon([v + (x if i % 2 == 0 else y) for i, v in enumerate(body)],
                         fill=theme.panel_light, outline=theme.cyan, width = 2)
        window = [112, 20, 190, 18, 230, 40, 100, 42]
        c.create_polygon([v + (x if i % 2 == 0 else y) for i, v in enumerate(window)],
                         fill = theme.bg, outline = theme.cyan)
        for wheelX in (68, 240):
            c.create_oval(x + wheelX - 19, y + 52, x + wheelX + 19, y + 90,
                          fill = theme.bg, outline = theme.pink, width = 3)
        c.create_line(x + 20, y + 96, x + 290, y + 96, fill = theme.pink, width = 3)  
   
    def firstCmd(self):
        self.current = 0
        self.refresh()

    def prevCmd(self):
        if self.current > 0:
            self.current -= 1
            self.refresh()

    def nextCmd(self):
        if self.current < self.team.getSize() - 1:
            self.current += 1
            self.refresh()

    def lastCmd(self):
        self.current = self.team.getSize() - 1
        self.refresh()

    def selectFromTable(self, event):
        selected = self.table.focus()
        for index, driver in enumerate(self.team.getDrivers()):
            if driver.getName() == selected:
                self.current = index
                self.refresh()
                self.notebook.select(0)
                return
            
    def checkAverage(self):
        driver = self.currentDriver()
        try:
            average = driver.getAverageScore()
            messagebox.showinfo("Average score",
                                f"{driver.getName()} averages {average} "
                                f"over {driver.getRunsCompleted()} run(s).")
        except NoRunsRecorded as error:
            messagebox.showerror("No runs recorded", str(error))

    def checkBest(self):
        driver = self.currentDriver()
        try:
            messagebox.showinfo("Best score",
                                f"{driver.getName()}'s best run is {driver.getBestScore()}.")
        except NoRunsRecorded as error:
            messagebox.showerror("No runs recorded", str(error))

    def startRun(self):
        driver = self.currentDriver()
        try:
            driver.getCar().checkCarCondition()
        except NoTyresLeft as error:
            messagebox.showerror("No tyres left", str(error))
            return
        except CarDamaged as error:
            messagebox.showerror("Car's totaled", str(error))
            return
        self.runningDriver = driver
        DriftRunWindow(self.root, driver, self.finishRun)

    def finishRun(self, score, spins):
        driver = self.runningDriver
        self.runningDriver = None
        try:
            driver.completeRun(score, spins)
        except ValueError as error:
            messagebox.showerror("Invalid score", str(error))
            return
        except NoTyresLeft as error:
            messagebox.showerror("No tyres left", str(error))
            return
        message = f"{driver.getName()} scored {score}."
        if spins:
            message += f" {spins} spin(s). Poor performance."
        self.setStatus(message)
        self.refresh()

    def buyTyres(self):
        driver = self.currentDriver()
        try:
            self.team.buyTyres(driver)
            self.setStatus(f"Bought tyre set for {driver.getName()}.")
        except InsufficientFunds as error:
            messagebox.showerror("Not enough money", str(error))
        self.refresh()

    def repairCar(self):
        driver = self.currentDriver()
        try:
            cost = self.team.repairCar(driver)
            if cost == 0:
                messagebox.showinfo("Repair", f"{driver.getCar().getModel()} isn't damaged.")
            else:
                self.setStatus(f"{driver.getCar().getModel()} repaired for €{cost:,}.")
        except InsufficientFunds as error:
            messagebox.showerror("Not enough money", str(error))
        self.refresh()

    def upgradeCar(self):
        driver = self.currentDriver()
        try:
            cost = self.team.upgradeCar(driver)
            self.setStatus(f"Upgraded {driver.getCar().getModel()} to tune "
                           f"{driver.getCar().getTuneLevel()} for €{cost:,}.")
        except MaxTune as error:
            messagebox.showerror("Max tune", str(error))
        except InsufficientFunds as error:
            messagebox.showerror("Not enough money", str(error))
        self.refresh()
        
    def openSignDialog(self):
        SignDriverDialog(self.root, self)

    def attemptSign(self, name, skillText, model):
        try:
            skill = int(skillText)
        except ValueError:
            messagebox.showerror("Skill issue", "Skill value must be a whole number from 1 to 100.")
            return False
        try:
            driver = Driver(name, skill, wageFor(skill), makeCar(model))
            fee = signingFee(skill)
            if not messagebox.askyesno("Confirm signing",
                                       f"Sign {driver.getName()} for €{fee:,}?\n"
                                       f"Wage: €{driver.getWage():,} per round"):
                return False
            self.team.signDriver(driver, fee)
        except ValueError as error:
            messagebox.showerror("Invalid driver", str(error))
            return False
        except SquadFull as error:
            messagebox.showerror("Squad full", str(error))
            return False
        except DuplicateDriver as error:
            messagebox.showerror("Duplicate driver", str(error))
            return False
        except InsufficientFunds as error:
            messagebox.showerror("Not enough money", str(error))
            return False
        self.current = self.team.getSize() - 1      # jump to the new driver
        self.setStatus(f"Signed {driver.getName()} for €{fee:,}.")
        self.refresh()
        return True

    def releaseCurrent(self):
        driver = self.currentDriver()
        if not messagebox.askyesno("Release driver", f"Release {driver.getName()}?"):
            return
        try:
            self.team.releaseDriver(self.current)
        except MinimumSquad as error:
            messagebox.showerror("Can't release", str(error))
            return
        if self.current >= self.team.getSize():
            self.current = self.team.getSize() - 1
        self.setStatus(f"Released {driver.getName()}.")
        self.refresh()

    def resetTeam(self):
        if messagebox.askyesno("Reset team",
                               "Reset the budget, all scores and all cars?"):
            self.team.resetAll()
            self.setStatus("Team reset.")
            self.refresh()

    def showTopDriver(self):
        try:
            top = self.team.getTopDriver()
            messagebox.showinfo("Top driver",
                                f"{top.getName()} leads with a best run of {top.getBestScore()}.")
        except NoRunsRecorded as error:
            messagebox.showerror("No runs recorded", str(error))

    def showHelp(self):
        messagebox.showinfo(
            "How to Play",
            "GARAGE: browse your drivers and start a qualy run.\n\n"
            "QUALIFYING RUN: press SPACE when the pink marker is in the skillcheck. "
            "Three sections: entry, angle, exit. Missing any skillcheck spins the car, causing mechanical damage.\n\n"
            "SHOP: buy tyres, repair damage and upgrade tune. Better tuning and skill "
            "make the skillcheck easier.\n\n"
            f"A car needs tyres and be at least {Car.min_run_condition}% condition to run.")


class SignDriverDialog(tk.Toplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("Sign new driver")
        self.configure(bg = theme.bg, padx = 20, pady = 16)
        self.resizable(False, False)

        tk.Label(self, text="SIGN NEW DRIVER", font=theme.fonts["heading"],
                 fg = theme.pink, bg  =theme.bg).grid(row = 0, column = 0, columnspan = 2, sticky = "w", pady = (0, 10))

        tk.Label(self, text = "Name", font=theme.fonts["body"], fg = theme.muted,
                 bg = theme.bg).grid(row = 1, column = 0, sticky = "w", pady = 4)
        self.nameEntry = tk.Entry(self, font=theme.fonts["body"], bg = theme.panel_light,
                                  fg = theme.text, insertbackground = theme.text, relief = "flat", width = 24)
        self.nameEntry.grid(row = 1, column = 1, pady = 4)

        tk.Label(self, text = "Skill (1-100)", font=theme.fonts["body"], fg=theme.muted,
                 bg = theme.bg).grid(row = 2, column = 0, sticky = "w", pady = 4)
        self.skillEntry = tk.Entry(self, font = theme.fonts["body"], bg = theme.panel_light,
                                   fg = theme.text, insertbackground = theme.text, relief = "flat", width = 24)
        self.skillEntry.grid(row = 2, column = 1, pady = 4)

        tk.Label(self, text="Car", font=theme.fonts["body"], fg=theme.muted,
                 bg=theme.bg).grid(row=3, column=0, sticky="w", pady=4)
        self.carVar = tk.StringVar(value=list(car_catalogue)[0])
        ttk.Combobox(self, textvariable=self.carVar, values=list(car_catalogue),
                     state="readonly", width=22).grid(row=3, column=1, pady=4)

        tk.Label(self, text="Fee = skill x €150   |   Wage = skill x €10 per round",
                 font=theme.fonts["small"], fg=theme.muted, bg=theme.bg).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 10))

        makeButton(self, "Sign driver", self.sign, colour=theme.pink).grid(
            row=5, column=0, columnspan=2, sticky="we")

        centreOver(self, master)
        self.transient(master)
        self.grab_set()
        self.nameEntry.focus_set()

    def sign(self):
        if self.app.attemptSign(self.nameEntry.get(), self.skillEntry.get(), self.carVar.get()):
            self.grab_release()
            self.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    theme.setupFonts(window)
    Countersteer(window)
    window.mainloop()
