import tkinter as tk
from tkinter import ttk, messagebox

import theme
from models import Season, Round
from minigame import DriftRunWindow
from exceptions import NoTyresLeft, CarDamaged, Bankrupt

result_names = {1: "Winner", 2: "Runner-up", 3: "Semi-final", 5: "Quarter-final"}


def resultText(position, qualified):
    if not qualified:
        return "Did not start"
    return result_names.get(position, f"P{position} in qualifying")


def button(parent, text, command, colour = theme.pink, fg = "white"):
    return tk.Button(parent, text = text, command = command, font = theme.fonts["bodyBold"],
                     bg = colour, fg = fg, activebackground = theme.cyan,
                     activeforeground = theme.bg, relief = "flat", bd = 0,
                     padx = 16, pady = 8, cursor = "hand2")

class EventTab(tk.Frame):
    box_width = 170
    box_height = 46

    def __init__(self, parent, app):
        super().__init__(parent, bg = theme.bg)
        self.__app = app                
        self.__log = []               

        # round + stage 
        top = tk.Frame(self, bg = theme.bg)
        top.pack(fill = "x", pady = (10, 6))
        family = theme.fonts["title"][0]
        self.__roundLabel = tk.Label(top, text = "", font = (family, 18, "bold"),
                                     fg = theme.pink, bg = theme.bg)
        self.__roundLabel.pack(side = "left")
        self.__stageLabel = tk.Label(top, text = "", font = theme.fonts["bodyBold"],
                                     fg = theme.cyan, bg = theme.bg)
        self.__stageLabel.pack(side = "left", padx = 14)
        self.__wageLabel = tk.Label(top, text = "", font = theme.fonts["small"],
                                    fg = theme.muted, bg = theme.bg)
        self.__wageLabel.pack(side = "right")

        # qualifying table | bracket 
        middle = tk.Frame(self, bg = theme.bg)
        middle.pack(fill = "both", expand = True)

        left = tk.Frame(middle, bg = theme.panel, padx = 8, pady = 6)
        left.pack(side = "left", fill = "y")
        tk.Label(left, text = "QUALIFYING", font = theme.fonts["bodyBold"], fg = theme.pink,
                 bg = theme.panel).pack(anchor = "w")
        self.__table = ttk.Treeview(left, columns = ("pos", "driver", "score"),
                                    show = "headings", height = 13)
        for column, heading, width, anchor in [("pos", "#", 34, "center"),
                                               ("driver", "Driver", 170, "w"),
                                               ("score", "Score", 60, "center")]:
            self.__table.heading(column, text = heading)
            self.__table.column(column, width = width, anchor = anchor)
        self.__table.tag_configure("mine", foreground = theme.cyan)
        self.__table.tag_configure("out", foreground = theme.muted)
        self.__table.pack(fill = "y", expand = True, pady = (4, 0))

        right = tk.Frame(middle, bg = theme.bg)
        right.pack(side = "left", fill = "both", expand = True, padx = (10, 0))
        self.__bracket = tk.Canvas(right, width = 590, height = 300, bg = theme.panel,
                                   highlightthickness = 0)
        self.__bracket.pack(fill = "both", expand = True)

        # main button + log 
        bottom = tk.Frame(self, bg = theme.bg)
        bottom.pack(fill = "x", pady = (8, 6))
        self.__actionButton = button(bottom, "", self.__action)
        self.__actionButton.pack(side = "right", ipadx = 6)
        self.__logLabel = tk.Label(bottom, text = "", font = theme.fonts["small"], fg = theme.text,
                                   bg = theme.bg, justify = "left", anchor = "w")
        self.__logLabel.pack(side = "left", fill = "x", expand = True)

    def __season(self):
        return self.__app.season

    def __addLog(self, message):
        self.__log = (self.__log + [message])[-3:]

    def __autoBattles(self):
        current = self.__season().getCurrentRound()
        battle = current.getNextBattle()
        while battle is not None and len(current.needsTeamRun(battle)) == 0:
            self.__logBattle(battle, current.completeBattle(battle))
            battle = current.getNextBattle()

    def __logBattle(self, battle, winner):
        loser = battle.getLoser()
        def score(driver):
            value = battle.getScore(driver)
            return "forfeit" if value is None else str(value)
        self.__addLog(f"{battle.getStage()}: {winner.getName()} ({score(winner)}) beat "
                      f"{loser.getName()} ({score(loser)})")

    def refresh(self):
        season = self.__season()
        current = season.getCurrentRound()
        number = min(season.getRoundsDone() + 1, Season.total_rounds)
        if season.isOver():
            self.__roundLabel.config(text = "SEASON COMPLETE")
        else:
            self.__roundLabel.config(text = f"ROUND {number} OF {Season.total_rounds}")
        self.__wageLabel.config(text = f"Wages: €{season.getWageBill():,} per round")
        self.__actionButton.config(text = self.__actionText())
        self.__logLabel.config(text = "\n".join(self.__log))
        self.__refreshTable(current)
        self.__drawBracket(current)

    def __actionText(self):
        season = self.__season()
        current = season.getCurrentRound()
        if current is None:
            if season.isOver():
                self.__stageLabel.config(text = "")
                return "SEE FINAL STANDINGS"
            self.__stageLabel.config(text = "Paddock")
            return f"START ROUND {season.getRoundsDone() + 1}  (pay wages)"
        queue = current.getQualifyingQueue()
        if len(queue) > 0:
            self.__stageLabel.config(text = "Qualifying")
            return f"QUALIFYING RUN: {queue[0].getName()}"
        battle = current.getNextBattle()
        if battle is None:
            self.__stageLabel.config(text = "Results")
            return "FINISH ROUND"
        self.__stageLabel.config(text = battle.getStage())
        if current.isTeamBattle(battle):  # v0.15
            a, b = battle.getDrivers()
            return f"TEAM ORDERS: {a.getName()} vs {b.getName()}"
        driver = current.needsTeamRun(battle)[0]
        others = [d for d in battle.getDrivers() if d is not driver]
        return f"{battle.getStage().upper()}: {driver.getName()} vs {others[0].getName()}"

    def __refreshTable(self, current):
        self.__table.delete(*self.__table.get_children())
        if current is None:
            return
        if current.isQualifyingDone():
            drivers = current.getRanking()
        else:
            drivers = current.getTeamDrivers()
        for place, driver in enumerate(drivers, start = 1):
            score = current.getQualifyingScore(driver)
            if not current.isQualifyingDone():
                place = "-"
                shown = "..." if driver in current.getQualifyingQueue() else ("DNS" if score is None else score)
            else:
                shown = "DNS" if score is None else score
            tags = []
            if current.isTeamDriver(driver):
                tags.append("mine")
            elif current.isQualifyingDone() and place > Round.bracket_size:
                tags.append("out")
            self.__table.insert("", "end", values = (place, driver.getName(), shown), tags = tags)

    def __drawBracket(self, current):
        c = self.__bracket
        c.delete("all")
        c.create_text(14, 16, text = "TOP 8 BRACKET", anchor = "w",
                      font = theme.fonts["bodyBold"], fill = theme.pink)
        battles = current.getBattles() if current is not None else []
        byStage = {stage: [b for b in battles if b.getStage() == stage] for stage in Round.stages}
        columns = {"Quarter-final": (14, [40, 110, 180, 250]),
                   "Semi-final": (206, [75, 215]),
                   "Final": (398, [145])}
        for stage in Round.stages:
            x, ys = columns[stage]
            c.create_text(x, 32, text = stage.upper(), anchor = "w",
                          font = theme.fonts["small"], fill = theme.muted)
            for slot, y in enumerate(ys):
                battle = byStage[stage][slot] if slot < len(byStage[stage]) else None
                self.__drawBox(c, x, y, battle, current)
                if stage != "Final":        # line to the next round's box
                    nextX, nextYs = columns[Round.stages[Round.stages.index(stage) + 1]]
                    targetY = nextYs[slot // 2] + EventTab.box_height // 2
                    midY = y + EventTab.box_height // 2
                    c.create_line(x + EventTab.box_width, midY, x + EventTab.box_width + 11, midY,
                                  x + EventTab.box_width + 11, targetY, nextX, targetY,
                                  fill = theme.panel_light, width = 2)
        # champion of the round
        final = byStage["Final"][0] if byStage["Final"] else None
        winner = final.getWinner() if final is not None else None
        c.create_text(398 + EventTab.box_width // 2, 215, text = "ROUND WINNER",
                      font = theme.fonts["small"], fill = theme.muted)
        c.create_text(398 + EventTab.box_width // 2, 238,
                      text = winner.getName() if winner else "?", font = theme.fonts["heading"],
                      fill = theme.cyan if winner and current.isTeamDriver(winner) else theme.text)

    def __drawBox(self, c, x, y, battle, current):
        w, h = EventTab.box_width, EventTab.box_height
        c.create_rectangle(x, y, x + w, y + h, fill = theme.bg, outline = theme.panel_light)
        if battle is None:
            c.create_text(x + 8, y + h // 2, text = "TBD", anchor = "w",
                          font = theme.fonts["small"], fill = theme.muted)
            return
        for row, driver in enumerate(battle.getDrivers()):
            rowY = y + 12 + row * 22
            colour = theme.cyan if current.isTeamDriver(driver) else theme.text
            if battle.isDone() and battle.getWinner() is not driver:
                colour = theme.muted
            c.create_text(x + 8, rowY, text = driver.getName(), anchor = "w",
                          font = theme.fonts["small"], fill = colour)
            if battle.isTeamOrder():  # v0.15
                if battle.getWinner() is driver:
                    c.create_text(x + w - 8, rowY, text = "TO", anchor = "e",
                                  font = theme.fonts["mono"], fill = colour)
            elif battle.hasRun(driver):
                score = battle.getScore(driver)
                c.create_text(x + w - 8, rowY, text = "FF" if score is None else str(score),
                              anchor = "e", font = theme.fonts["mono"], fill = colour)
                
    def __action(self):
        season = self.__season()
        current = season.getCurrentRound()
        if current is None:
            if season.isOver():
                self.__app.endSeason(bankrupt = False)
            else:
                self.__startRound()
            return
        queue = current.getQualifyingQueue()
        if len(queue) > 0:
            self.__qualify(queue[0])
            return
        battle = current.getNextBattle()
        if battle is None:
            self.__finishRound()
        elif current.isTeamBattle(battle):  # v0.15
            TeamOrdersDialog(self.__app.root, battle, self.__teamOrders)
        else:
            self.__battle(battle, current.needsTeamRun(battle)[0])

    def __startRound(self):
        season = self.__season()
        notReady = [d.getName() for d in season.getTeam().getDrivers() if not d.getCar().isReady()]
        if notReady and not messagebox.askyesno(
                "Drivers not ready",
                "These drivers have no tyres or a damaged car and won't start:\n\n"
                + "\n".join(notReady) + "\n\nStart the round anyway? (No = go to the Shop first)"):
            return
        try:
            wages = season.startRound()
        except Bankrupt as error:
            messagebox.showerror("Bankrupt", str(error))
            self.__app.endSeason(bankrupt = True)
            return
        self.__log = []
        self.__addLog(f"Round {season.getRoundsDone() + 1} started. Paid €{wages:,} in wages.")
        self.__app.setEventLock(True)
        self.__app.refresh()

    def __checkCar(self, driver, consequence):
        try:
            driver.getCar().checkCarCondition()
            return True
        except NoTyresLeft as error:
            messagebox.showerror("No tyres left", f"{error}\n{driver.getName()} {consequence}")
        except CarDamaged as error:
            messagebox.showerror("Car's totaled", f"{error}\n{driver.getName()} {consequence}")
        return False

    # qualifying 
    def __qualify(self, driver):
        current = self.__season().getCurrentRound()
        if not self.__checkCar(driver, "won't start this round."):
            current.recordQualifying(driver, None)
            self.__addLog(f"{driver.getName()} did not start.")
            self.__afterQualifyingRun()
            return
        DriftRunWindow(self.__app.root, driver,
                       lambda score, spins: self.__qualifyingDone(driver, score, spins))

    def __qualifyingDone(self, driver, timing, spins):
        current = self.__season().getCurrentRound()
        score = driver.blendScore(timing)  # v0.15 timing + driver rating
        try:
            driver.completeRun(score, spins)
        except (ValueError, NoTyresLeft) as error:
            messagebox.showerror("Run not counted", str(error))
            return
        current.recordQualifying(driver, score)
        self.__addLog(f"{driver.getName()} qualifies with {score} (your timing {timing}, "
                      f"rating {driver.getRating()})." + (f" {spins} spin(s)." if spins else ""))
        self.__afterQualifyingRun()

    def __afterQualifyingRun(self):
        current = self.__season().getCurrentRound()
        if len(current.getQualifyingQueue()) == 0:
            current.finishQualifying()
            top = current.getRanking()[0]
            self.__addLog(f"Qualifying done. {top.getName()} tops the field with "
                          f"{current.getQualifyingScore(top)}.")
            self.__autoBattles()
        self.__app.refresh()

    # ---------- battles ----------
    def __battle(self, battle, driver):
        if not self.__checkCar(driver, "forfeits this battle."):
            battle.forfeit(driver)
            self.__afterBattleRun(battle)
            return
        DriftRunWindow(self.__app.root, driver,
                       lambda score, spins: self.__battleRunDone(battle, driver, score, spins))

    def __battleRunDone(self, battle, driver, timing, spins):
        score = driver.blendScore(timing)  # v0.15 timing + driver rating
        try:
            driver.completeRun(score, spins)
        except (ValueError, NoTyresLeft) as error:
            messagebox.showerror("Run not counted", str(error))
            return
        battle.record(driver, score)
        self.__afterBattleRun(battle)

    def __afterBattleRun(self, battle):
        current = self.__season().getCurrentRound()
        if len(current.needsTeamRun(battle)) == 0:      # both runs 
            self.__logBattle(battle, current.completeBattle(battle))
            self.__autoBattles()
        self.__app.refresh()

    def __teamOrders(self, battle, choice):  # v0.15
        current = self.__season().getCurrentRound()
        if choice is not None:
            current_winner = battle.awardTo(choice)
            self.__addLog(f"{battle.getStage()}: team orders, {current_winner.getName()} goes through.")
        else:
            for driver in battle.getDrivers():
                if not self.__checkCar(driver, "forfeits this battle."):
                    battle.forfeit(driver)
                    continue
                score = current.simulateRun(driver)
                driver.completeRun(score, 0)
                battle.record(driver, score)
            self.__logBattle(battle, battle.decide())
        self.__autoBattles()
        self.__app.refresh()

    # results
    def __finishRound(self):
        season = self.__season()
        number = season.getRoundsDone() + 1
        current = season.getCurrentRound()
        results, earnings = season.finishRound()
        lines = [f"Round {number} won by {results[0][0].getName()}.", ""]
        for driver, position, points, prize in results:
            if current.isTeamDriver(driver):
                qualified = current.getQualifyingScore(driver) is not None
                lines.append(f"{driver.getName()}: {resultText(position, qualified)}"
                             f"  (+{points} pts, €{prize:,})")
        lines += ["", f"Prize money: €{earnings:,}"]
        self.__log = []
        self.__addLog(f"Round {number} finished. Prize money €{earnings:,}.")
        self.__app.setEventLock(False)
        self.__app.refresh()
        messagebox.showinfo(f"Round {number} results", "\n".join(lines))
        if season.isOver():
            self.__app.endSeason(bankrupt = False)

class TeamOrdersDialog(tk.Toplevel):
    def __init__(self, master, battle, onChoice):
        super().__init__(master)
        self.__onChoice = onChoice
        self.__battle = battle
        self.title("Team orders")
        self.configure(bg = theme.bg, padx = 24, pady = 18)
        self.resizable(False, False)
        a, b = battle.getDrivers()

        tk.Label(self, text = "TEAM ORDERS", font = theme.fonts["heading"], fg = theme.pink,
                 bg = theme.bg).pack(anchor = "w")
        tk.Label(self, text = f"{battle.getStage()}: this is a Multi 21 standoff.\n"
                              "Who goes?",
                 font = theme.fonts["body"], fg = theme.text, bg = theme.bg,
                 justify = "left").pack(anchor = "w", pady = (4, 12))
        row = tk.Frame(self, bg = theme.bg)
        row.pack(fill = "x")
        for driver in (a, b):
            button(row, f"{driver.getName()}\nrating {driver.getRating()}",
                   lambda d = driver: self.__choose(d)).pack(side = "left", expand = True,
                                                             fill = "x", padx = 4)
        button(self, "LET THEM RACE", lambda: self.__choose(None),
               colour = theme.panel_light).pack(fill = "x", padx = 4, pady = (8, 0))

        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_reqwidth()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.transient(master)
        self.grab_set()

    def __choose(self, driver):
        self.grab_release()
        self.destroy()
        self.__onChoice(self.__battle, driver)

class SeasonEndScreen(tk.Frame):

    def __init__(self, master, season, bankrupt, onMainMenu, onNewSeason):
        super().__init__(master, bg = theme.bg)
        team = season.getTeam()
        standings = season.getStandings()
        family = theme.fonts["title"][0]

        if bankrupt:
            title, colour = "GAME OVER", theme.bad
            subtitle = (f"{team.getName()} went bankrupt after "
                        f"{season.getRoundsDone()} of {Season.total_rounds} rounds.")
        else:
            champion = season.getChampion()
            if season.isTeamDriver(champion):
                title, colour = "CHAMPIONS!", theme.cyan
                subtitle = (f"{champion.getName()} wins the title for {team.getName()} "
                            f"with {champion.getPoints()} points.")
            else:
                title, colour = "SEASON OVER", theme.pink
                subtitle = (f"{champion.getName()} wins the title with "
                            f"{champion.getPoints()} points.")

        tk.Label(self, text = title, font = (family, 40, "bold"), fg = colour,
                 bg = theme.bg).pack(pady = (40, 4))
        tk.Label(self, text = subtitle, font = theme.fonts["body"], fg = theme.text,
                 bg = theme.bg).pack()
        tk.Label(self, text = f"Final budget  €{team.getBudget():,}", font = theme.fonts["mono"],
                 fg = theme.cyan, bg = theme.bg).pack(pady = (6, 18))

        board = tk.Frame(self, bg = theme.panel, padx = 24, pady = 14)
        board.pack()
        tk.Label(board, text = "FINAL STANDINGS" if not bankrupt else "STANDINGS",
                 font = theme.fonts["bodyBold"], fg = theme.pink,
                 bg = theme.panel).grid(row = 0, column = 0, columnspan = 4, sticky = "w", pady = (0, 6))
        for row, driver in enumerate(standings[:10], start = 1):
            mine = season.isTeamDriver(driver)
            fg = theme.cyan if mine else theme.text
            values = [f"{row}.", driver.getName() + ("  (you)" if mine else ""),
                      f"{driver.getPoints()} pts",
                      f"{driver.getBattleWins()} win" + ("" if driver.getBattleWins() == 1 else "s")]
            for column, value in enumerate(values):
                tk.Label(board, text = value, font = theme.fonts["body"], fg = fg, bg = theme.panel,
                         anchor = "w", width = [4, 24, 8, 8][column]).grid(row = row, column = column)

        buttons = tk.Frame(self, bg = theme.bg)
        buttons.pack(side = "bottom", fill = "x", padx = 24, pady = 20)
        button(buttons, "MAIN MENU", onMainMenu, colour = theme.panel_light).pack(side = "left")
        button(buttons, "NEW SEASON", onNewSeason).pack(side = "right")