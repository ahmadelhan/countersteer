from exceptions import (
    NoTyresLeft,
    CarDamaged,
    InsufficientFunds,
    SquadFull,
    DuplicateDriver,
    MinimumSquad,
    NoRunsRecorded,
    MaxTune,
    DraftIncomplete,    # v0.14
    InvalidTeamName,    # v0.14
    Bankrupt            # v0.15
)
import random  # v0.15 rival scores

class Car:
    min_run_condition = 30
    max_tune = 5
    starting_tyres = 4
    
    def __init__(self, model, horsepower, steeringAngle, imagePath=""):
        self.__model = model
        self.__horsepower = horsepower
        self.__steeringAngle = steeringAngle
        self.__imagePath = imagePath
        self.__tuneLevel = 1
        self.__condition = 100
        self.__tyresets = Car.starting_tyres

# getters
    def getModel(self):
        return self.__model
    
    def getHorsepower(self):
        return self.__horsepower
    
    def getSteeringAngle(self):
        return self.__steeringAngle
    
    def getImagePath(self):
        return self.__imagePath
    
    def getTuneLevel(self):
        return self.__tuneLevel
    
    def getCondition(self):
        return self.__condition
    
    def getTyresets(self):
        return self.__tyresets
# getters

    def checkCarCondition(self):
        if self.__tyresets == 0:
            raise NoTyresLeft(
                f"{self.__model} has no tyre sets."
            )
        if self.__condition < Car.min_run_condition:
            raise CarDamaged(
                f"{self.__model} is at {self.__condition}% condition.\n"
                f"It must be at least {Car.min_run_condition} to race."
            )
    
    def isReady(self):
        try:
            self.checkCarCondition()
            return True
        except (NoTyresLeft, CarDamaged):
            return False
    
    def useTyres(self):
        if self.__tyresets == 0:
            raise NoTyresLeft(
                f"{self.__model} has no tyre sets."
            )
        self.__tyresets -= 1
    
    def addTyres(self, sets):
        self.__tyresets += sets
    
    def damage(self, amount):
        self.__condition = max(0, self.__condition - amount)
        
    def getRepairCost(self):
        return (100 - self.__condition) * 50
    
    def repair(self):
        self.__condition = 100
        
    def checkUpgradeValid(self):
        if self.__tuneLevel >= Car.max_tune:
            raise MaxTune(
                f"{self.__model} is already at max tune"
                f" (level {Car.max_tune})"
            )
            
    def getUpgradeCost(self):
        return self.__tuneLevel * 2000
    
    def upgradeTune(self):
        self.checkUpgradeValid()
        self.__tuneLevel += 1
        
    def resetAll(self):
        self.__tuneLevel = 1
        self.__condition = 100
        self.__tyresets = Car.starting_tyres
        
class Driver:
    wear_per_run = 3
    spin_damage = 15
    timing_weight = 0.5     # v0.15 50% timing, 50% driver + car
    
    def __init__(self, name, skill, wage, car):
        if name.strip() == "":
            raise ValueError("A driver NEEDS a name, c'mon now.")
        if skill < 1 or skill > 100:
            raise ValueError("Let's be realistic here, between 1 to 100 now.")
        self.__name = name.strip()
        self.__skill = skill
        self.__wage = wage
        self.__car = car
        self.__runScores = []
        self.__battleWins = 0
        self.__points = 0
        
# getters
    def getName(self):
        return self.__name
    
    def getSkill(self):
        return self.__skill
        
    def getWage(self):
            return self.__wage
        
    def getCar(self):
            return self.__car
        
    def getRunScores(self):
            return list(self.__runScores) 
    
    def getRunsCompleted(self):
            return len(self.__runScores)
        
    def getBattleWins(self):
            return self.__battleWins
        
    def getPoints(self):
            return self.__points
# getters

    def getAverageScore(self):
        if len(self.__runScores) == 0:
            raise NoRunsRecorded(
                f"{self.__name} hasn't raced yet."
            )
        return round(sum(self.__runScores) / len(self.__runScores), 1)
    
    def getBestScore(self):
        if len(self.__runScores) == 0:
            raise NoRunsRecorded(
                f"{self.__name} hasn't raced yet."
            )
        return max(self.__runScores)
    
    def recordRun(self, score):
        if score < 0 or score > 100:
            raise ValueError("Can't score more than 100 or less than 0.")
        self.__runScores.append(score)
        
    def completeRun(self, score, spins, strategy = None): # v0.20 strategy
        tyres = 1
        spinDamage = Driver.spin_damage
        if strategy is not None:                # v0.20
            strategy.checkTyres(self.__car)
            tyres = strategy.getTyreSets()
            spinDamage = strategy.getSpinDamage(spinDamage)
        self.recordRun(score)
        for _ in range(tyres):
            self.__car.useTyres()
        self.__car.damage(Driver.wear_per_run + spins * spinDamage)
        
    def getRating(self):  # v0.15
        car = self.__car
        rating = self.__skill * 0.65 + car.getHorsepower() / 20 + car.getTuneLevel() * 4
        return min(100, round(rating))

    def blendScore(self, timing, bonus = 0):  # v0.15
        rating = min(100, self.getRating() + bonus)
        score = timing * Driver.timing_weight + rating * (1 - Driver.timing_weight)
        return max(0, min(100, round(score)))

    def sweetSpotWidth(self):
        width = (18 + self.__skill * 0.15
                 + self.__car.getTuneLevel() * 3
                 - (100 - self.__car.getCondition()) * 0.1)
        return max(10, min(45, round(width)))
    
# game layer
    def addPoints(self, points):
        self.__points += points
    
    def addBattleWin(self):
        self.__battleWins += 1
        
    def resetAll(self):
        self.__runScores = []
        self.__battleWins = 0
        self.__points = 0
        self.__car.resetAll()
# game layer

class Team:
    max_drivers = 5
    tyre_price = 600
    
    def __init__(self, name, budget):
        self.__name = name
        self.__budget = budget
        self.__startingBudget = budget
        self.__drivers = []
        
# getters
    def getName(self):
        return self.__name
    
    def getBudget(self):
            return self.__budget
        
    def getDrivers(self):
            return self.__drivers
        
    def getDriver(self, index):
            return self.__drivers[index]
        
    def getSize(self):
            return len(self.__drivers)
# getters

    def spend(self, amount):
        if amount > self.__budget: 
            raise InsufficientFunds(
                f"You do not have the money for this.\n"
                f"That costs €{amount} but the team only has "
                f"€{self.__budget}."
            )
        self.__budget -= amount
        
    def earn(self, amount):
        self.__budget += amount
    
    def driverExists(self, name):
        for driver in self.__drivers:
            if driver.getName().lower() == name.strip().lower():
                return True
        return False
    
    def addDriver(self, driver):
        if len(self.__drivers) >= Team.max_drivers:
            raise SquadFull(
                f"Can't recruit more drivers than what you already have ({Team.max_drivers})."
            )
        if self.driverExists(driver.getName()):
            raise DuplicateDriver(
                f"{driver.getName()} is already on the team."
            )
        self.__drivers.append(driver)
        
    def signDriver(self, driver, fee):
        if len(self.__drivers) >= Team.max_drivers:
            raise SquadFull(
                "The squad's full."
            )
        if self.driverExists(driver.getName()):
            raise DuplicateDriver(
                f"{driver.getName()} is already on the team."
            )
        self.spend(fee)
        self.__drivers.append(driver)
        
    def releaseDriver(self, index):
        if len(self.__drivers) <= 1:
            raise MinimumSquad(
                "A team needs a driver. How else are they going to compete."
            )
        return self.__drivers.pop(index)
    
    def buyTyres(self, driver, sets = 1):
        self.spend(Team.tyre_price * sets)
        driver.getCar().addTyres(sets)
        
    def repairCar(self, driver):
        cost = driver.getCar().getRepairCost()
        if cost > 0:
            self.spend(cost)
            driver.getCar().repair()
        return cost
    
    def upgradeCar(self, driver):
        car = driver.getCar()
        car.checkUpgradeValid()
        cost = car.getUpgradeCost()
        self.spend(cost)
        car.upgradeTune()
        return cost
    
    # getters 2
    def getSortedDrivers(self, sortBy):
        def scoreOrMinus(driver, scoreMethod):
            try:
                return scoreMethod(driver)
            except NoRunsRecorded:
                return -1
                
        if sortBy ==  "Best score":
            key = lambda d: scoreOrMinus(d, Driver.getBestScore)
        elif sortBy == "Average score":
            key = lambda d: scoreOrMinus(d, Driver.getAverageScore)
        elif sortBy == "Skill":
            key = lambda d: d.getSkill()
        elif sortBy == "Condition":
            key = lambda d: d.getCar().getCondition()
        else:
            raise ValueError(f"Pick a valid sorting option: {sortBy}")
        return sorted(self.__drivers, key = key, reverse = True)
    
    def getDriversReady(self):
        return [d for d in self.__drivers if d.getCar().isReady()]
    
    def getTopDriver(self):
        withRuns = [d for d in self.__drivers if d.getRunsCompleted() > 0]
        if len(withRuns) == 0:
            raise NoRunsRecorded("No drivers have raced yet.")
        return max (withRuns, key = lambda d: d.getBestScore())
    
    def resetAll(self):
        self.__budget = self.__startingBudget
        for driver in self.__drivers:
            driver.resetAll()

# v0.13
class Draft:
    team_size = 3
    max_name_length = 24

    def __init__(self, pool, budget):
        self.__pool = pool         
        self.__picked = []          # indexes
        self.__budget = budget

# getters
    def getPoolSize(self):
        return len(self.__pool)

    def getDriver(self, index):
        return self.__pool[index][0]

    def getFee(self, index):
        return self.__pool[index][1]

    def getPicked(self):
        return [self.__pool[i][0] for i in self.__picked]

    def isPicked(self, index):
        return index in self.__picked

    def getBudget(self):
        return self.__budget

    def getBudgetLeft(self):
        spent = sum(self.__pool[i][1] for i in self.__picked)
        return self.__budget - spent
# getters

    def pick(self, index):
        driver, fee = self.__pool[index]
        if index in self.__picked:
            raise DuplicateDriver(
                f"{driver.getName()} is already on the team."
            )
        if len(self.__picked) >= Draft.team_size:
            raise SquadFull(
                f"You can only draft {Draft.team_size} drivers. Remove one."
            )
        if fee > self.getBudgetLeft():
            raise InsufficientFunds(
                f"{driver.getName()} costs €{fee:,}. "
                f"€{self.getBudgetLeft():,} left."
            )
        self.__picked.append(index)

    def unpick(self, index):
        if index in self.__picked:
            self.__picked.remove(index)

    def checkTeamName(self, name):
        name = name.strip()
        if name == "":
            raise InvalidTeamName("A team needs a name.")
        if len(name) > Draft.max_name_length:
            raise InvalidTeamName(
                f"Team names can be at most {Draft.max_name_length} characters "
                f"(current {len(name)})."
            )
        return name

    def buildTeam(self, name):
        name = self.checkTeamName(name)
        if len(self.__picked) < Draft.team_size:
            raise DraftIncomplete(
                f"Draft {Draft.team_size} drivers before starting "
                f"({len(self.__picked)} picked)."
            )
        team = Team(name, self.getBudgetLeft())
        for driver in self.getPicked():
            team.addDriver(driver)
        return team
# v0.13


# v0.20 strategy
class Strategy:
    lines = {   # target width, marker speed, bonus, spin damage
        "Safe":       {"width": 1.3,  "speed": 0.9,  "bonus": -2, "spin": 0.6},
        "Balanced":   {"width": 1.0,  "speed": 1.0,  "bonus": 0,  "spin": 1.0},
        "Aggressive": {"width": 0.75, "speed": 1.2,  "bonus": 5,  "spin": 1.5},
    }
    line_order = ["Safe", "Balanced", "Aggressive"]
    fresh_tyre_width = 1.2      # easier skillcheck
    fresh_tyre_sets = 2         # for two tyresets
    pressure_timing = 85        # timing needed for pressure 
    pressure_rival_loss = 6     # rival loses
    pressure_own_loss = 8       # player loses 
    min_halfwidth = 6

    def __init__(self, line = "Balanced", freshTyres = False, pressure = False):
        if line not in Strategy.lines:
            raise ValueError(f"'{line}' isn't a racing line...")
        self.__line = line
        self.__freshTyres = freshTyres
        self.__pressure = pressure

# getters
    def getLine(self):
        return self.__line

    def hasFreshTyres(self):
        return self.__freshTyres

    def hasPressure(self):
        return self.__pressure
# getters

    def getTyreSets(self):
        return Strategy.fresh_tyre_sets if self.__freshTyres else 1

    def checkTyres(self, car):
        needed = self.getTyreSets()
        if car.getTyresets() < needed:
            raise NoTyresLeft(
                f"Fresh tyres use {needed} sets but the {car.getModel()} only has "
                f"{car.getTyresets()}.\nBuy tyres in the Shop or run on used tyres."
            )

    def applyWidth(self, halfwidth):
        width = halfwidth * Strategy.lines[self.__line]["width"]
        if self.__freshTyres:
            width *= Strategy.fresh_tyre_width
        return max(Strategy.min_halfwidth, round(width))

    def getSpeedFactor(self):
        return Strategy.lines[self.__line]["speed"]

    def getBonus(self):
        return Strategy.lines[self.__line]["bonus"]

    def getSpinDamage(self, baseDamage):
        return round(baseDamage * Strategy.lines[self.__line]["spin"])

    def pressureWorked(self, timing):
        return self.__pressure and timing >= Strategy.pressure_timing

    def finalScore(self, score, timing):
        score += self.getBonus()
        if self.__pressure and not self.pressureWorked(timing):
            score -= Strategy.pressure_own_loss
        return max(0, min(100, score))

    def getRivalLoss(self, timing):
        return Strategy.pressure_rival_loss if self.pressureWorked(timing) else 0

    def describe(self):
        parts = [self.__line, "fresh tyres" if self.__freshTyres else "used tyres"]
        if self.__pressure:
            parts.append("pressure on")
        return ", ".join(parts)
# v0.20


# v0.15 game layer
class Battle:
    def __init__(self, stage, higherSeed, lowerSeed):
        self.__stage = stage
        self.__drivers = [higherSeed, lowerSeed]
        self.__scores = {}          # driver -> score, None = forfeited
        self.__winner = None

# getters
    def getStage(self):
        return self.__stage

    def getDrivers(self):
        return list(self.__drivers)

    def getScore(self, driver):
        return self.__scores.get(driver)

    def hasRun(self, driver):
        return driver in self.__scores

    def getWinner(self):
        return self.__winner

    def getLoser(self):
        if self.__winner is None:
            return None
        return self.__drivers[1] if self.__winner is self.__drivers[0] else self.__drivers[0]

    def isDone(self):
        return self.__winner is not None
# getters

    def record(self, driver, score):
        if driver not in self.__drivers:
            raise ValueError(f"{driver.getName()} isn't in this battle.")
        if score is not None and (score < 0 or score > 100):
            raise ValueError("Can't score more than 100 or less than 0.")
        self.__scores[driver] = score

    def forfeit(self, driver):
        self.record(driver, None)

    def awardTo(self, driver):  # v0.15 team orders
        if driver not in self.__drivers:
            raise ValueError(f"{driver.getName()} isn't in this battle.")
        if self.__winner is not None:
            raise ValueError("Battle's been decided.")
        self.__winner = driver
        driver.addBattleWin()
        return driver

    def applyPressure(self, driver, points):  # v0.20 strategy
        score = self.__scores.get(driver)
        if score is None:
            return None
        self.__scores[driver] = max(0, score - points)
        return self.__scores[driver]

    def isTeamOrder(self):  # v0.15
        return self.__winner is not None and len(self.__scores) == 0

    def decide(self):
        higher, lower = self.__drivers
        if higher not in self.__scores or lower not in self.__scores:
            raise ValueError("Both drivers must run before the battle is decided.")
        higherScore = self.__scores[higher]
        lowerScore = self.__scores[lower]
        if lowerScore is not None and (higherScore is None or lowerScore > higherScore):
            self.__winner = lower
        else:
            self.__winner = higher          
        self.__winner.addBattleWin()
        return self.__winner


class Round:
    bracket_size = 8
    stages = ["Quarter-final", "Semi-final", "Final"]
    seed_pairs = [(0, 7), (3, 4), (1, 6), (2, 5)]       # 1v8, 4v5, 2v7, 3v6
    points_table = {1: 25, 2: 18, 3: 12, 5: 6}       
    prize_table = {1: 7000, 2: 4500, 3: 3000, 5: 1800}  # v0.15 lowered
    appearance_fee = 500                                # v0.15 lowered
    rival_improvement = 3                               # v0.15

    def __init__(self, number, teamDrivers, rivals, rng):
        self.__number = number
        self.__teamDrivers = list(teamDrivers)
        self.__rivals = list(rivals)
        self.__rng = rng
        self.__qualifying = {}          # driver -> score, None = did not start
        self.__ranking = []           
        self.__stageIndex = 0
        self.__battles = []             

# getters
    def getNumber(self):
        return self.__number

    def getTeamDrivers(self):
        return list(self.__teamDrivers)

    def isTeamDriver(self, driver):
        return driver in self.__teamDrivers

    def getQualifyingQueue(self):
        return [d for d in self.__teamDrivers if d not in self.__qualifying]

    def isQualifyingDone(self):
        return len(self.__ranking) > 0

    def getQualifyingScore(self, driver):
        return self.__qualifying.get(driver)

    def getRanking(self):
        return list(self.__ranking)

    def getBattles(self):
        return list(self.__battles)

    def getStageName(self):
        return Round.stages[min(self.__stageIndex, len(Round.stages) - 1)]
# getters

    def getRivalBonus(self):  # v0.15
        return (self.__number - 1) * Round.rival_improvement

    def simulateRun(self, driver):
        # v0.15
        timing = self.__rng.gauss(78, 10)
        if self.__rng.random() < 0.08:        
            timing *= 0.5
        timing = max(0, min(100, timing))
        bonus = 0 if driver in self.__teamDrivers else self.getRivalBonus()
        return driver.blendScore(timing, bonus)

    # qualifying 
    def recordQualifying(self, driver, score):
        if driver not in self.__teamDrivers:
            raise ValueError(f"{driver.getName()} isn't on your team.")
        self.__qualifying[driver] = score

    def finishQualifying(self):
        if len(self.getQualifyingQueue()) > 0:
            raise ValueError("Every team driver must run first.")
        for rival in self.__rivals:
            self.__qualifying[rival] = self.simulateRun(rival)
        everyone = self.__teamDrivers + self.__rivals
        ranked = [d for d in everyone if self.__qualifying[d] is not None]
        ranked.sort(key = lambda d: self.__qualifying[d], reverse = True)
        didNotStart = [d for d in everyone if self.__qualifying[d] is None]
        self.__ranking = ranked + didNotStart
        top = self.__ranking[:Round.bracket_size]
        for high, low in Round.seed_pairs:
            self.__battles.append(Battle(Round.stages[0], top[high], top[low]))

    # battles 
    def __currentStageBattles(self):
        stage = Round.stages[self.__stageIndex]
        return [b for b in self.__battles if b.getStage() == stage]

    def getNextBattle(self):
        if not self.isQualifyingDone():
            return None
        for battle in self.__currentStageBattles():
            if not battle.isDone():
                return battle
        if self.__stageIndex == len(Round.stages) - 1:
            return None                         # final decided
        winners = [b.getWinner() for b in self.__currentStageBattles()]
        self.__stageIndex += 1
        for i in range(0, len(winners), 2):
            self.__battles.append(Battle(Round.stages[self.__stageIndex], winners[i], winners[i + 1]))
        return self.getNextBattle()

    def needsTeamRun(self, battle):
        return [d for d in battle.getDrivers() if d in self.__teamDrivers and not battle.hasRun(d)]

    def isTeamBattle(self, battle):  # v0.15 immersion
        return all(d in self.__teamDrivers for d in battle.getDrivers())

    def completeBattle(self, battle):
        if len(self.needsTeamRun(battle)) > 0:
            raise ValueError("Your driver has to run before the battle can be decided.")
        for driver in battle.getDrivers():
            if not battle.hasRun(driver):
                battle.record(driver, self.simulateRun(driver))
        return battle.decide()

    def isFinished(self):
        return self.isQualifyingDone() and self.getNextBattle() is None

    # results 
    def getResults(self):
        if not self.isFinished():
            raise ValueError("The round isn't finished yet.")
        final = self.__battles[-1]
        positions = {final.getWinner(): 1, final.getLoser(): 2}
        for battle in self.__battles:
            if battle.getStage() == "Semi-final":
                positions[battle.getLoser()] = 3
            elif battle.getStage() == "Quarter-final":
                positions[battle.getLoser()] = 5
        for place, driver in enumerate(self.__ranking, start = 1):
            if driver not in positions:
                positions[driver] = place    
        results = []
        for driver in sorted(positions, key = lambda d: (positions[d], self.__ranking.index(d))):
            position = positions[driver]
            points = Round.points_table.get(position, 0)
            prize = Round.prize_table.get(position, 0)
            if prize == 0 and self.__qualifying[driver] is not None:
                prize = Round.appearance_fee
            results.append((driver, position, points, prize))
        return results


class Season:
    total_rounds = 4

    def __init__(self, team, rivals, rng = None):
        self.__team = team
        self.__rivals = rivals
        self.__rng = rng if rng is not None else random.Random()
        self.__roundsDone = 0
        self.__current = None
        self.__history = []           
# getters
    def getTeam(self):
        return self.__team

    def getRivals(self):
        return list(self.__rivals)

    def getRoundsDone(self):
        return self.__roundsDone

    def getCurrentRound(self):
        return self.__current

    def isRoundInProgress(self):
        return self.__current is not None

    def isOver(self):
        return self.__roundsDone >= Season.total_rounds

    def getHistory(self):
        return list(self.__history)

    def getWageBill(self):
        return sum(d.getWage() for d in self.__team.getDrivers())
# getters

    def startRound(self):
        if self.isOver():
            raise ValueError("The season's over.")
        if self.__current is not None:
            raise ValueError("A round's already running.")
        wages = self.getWageBill()
        if wages > self.__team.getBudget():
            raise Bankrupt(
                f"Driver wages are €{wages:,} but the team only has "
                f"€{self.__team.getBudget():,}.\nThe team's got no money."
            )
        self.__team.spend(wages)
        self.__current = Round(self.__roundsDone + 1, self.__team.getDrivers(),
                               self.__rivals, self.__rng)
        return wages

    def finishRound(self):
        results = self.__current.getResults()
        earnings = 0
        for driver, position, points, prize in results:
            driver.addPoints(points)
            if self.__current.isTeamDriver(driver):
                earnings += prize
        self.__team.earn(earnings)
        winner = results[0][0]
        self.__history.append(f"Round {self.__current.getNumber()}: won by {winner.getName()}")
        self.__roundsDone += 1
        self.__current = None
        return results, earnings

    def getStandings(self):
        everyone = self.__team.getDrivers() + self.__rivals
        return sorted(everyone, key = lambda d: (d.getPoints(), d.getBattleWins()), reverse = True)

    def getChampion(self):
        if not self.isOver():
            raise ValueError("The season isn't over yet.")
        return self.getStandings()[0]

    def isTeamDriver(self, driver):
        return driver in self.__team.getDrivers()

    def resetAll(self):
        self.__team.resetAll()
        for rival in self.__rivals:
            rival.resetAll()
        self.__roundsDone = 0
        self.__current = None
        self.__history = []
# v0.15