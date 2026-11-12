from exceptions import (
    NoTyresLeft,
    CarDamaged,
    InsufficientFunds,
    SquadFull,
    DuplicateDriver,
    MinimumSquad,
    NoRunsRecorded,
    MaxTune
)

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
    
    def         teeringAngle(self):
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
            return self.__runScores
    
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
        
    def completeRun(self, score, spins):
        self.recordRun(score)
        self.__car.useTyres()
        self.__car.daamge(Driver.wear_per_run + spins * Driver.spin_damage)
        
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
        car.checkCanUpgrade()
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
                