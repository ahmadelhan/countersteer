import unittest

from data import createStartingTeam, makeCar, createDraftPool, draft_budget  # v0.13
from data import createRivals  # v0.15
import random  # v0.15
from models import Car, Driver, Team, Draft # v0.13
from models import Battle, Round, Season  # v0.15
from minigame import scoreSection
from exceptions import (
    NoTyresLeft,
    CarDamaged,
    InsufficientFunds,
    SquadFull,
    MinimumSquad,
    DuplicateDriver,
    NoRunsRecorded,
    MaxTune,
    DraftIncomplete,    # v0.13
    InvalidTeamName, # v0.13
    Bankrupt,        # v0.15
)


def newDriver(name="Test Driver", skill=50):
    return Driver(name, skill, skill * 10, makeCar("Toyota AE86"))


class TestCar(unittest.TestCase):

    def test_new_car_is_ready(self):
        car = makeCar("Nissan Silvia S15")
        self.assertEqual(car.getCondition(), 100)
        self.assertEqual(car.getTyresets(), Car.starting_tyres)
        self.assertTrue(car.isReady())

    def test_no_tyres_raises_error(self):
        car = makeCar("Nissan Silvia S15")
        for _ in range(Car.starting_tyres):
            car.useTyres()
        with self.assertRaises(NoTyresLeft):
            car.checkCarCondition()

    def test_damaged_car_raises_error(self):
        car = makeCar("Nissan Silvia S15")
        car.damage(80)
        with self.assertRaises(CarDamaged):
            car.checkCarCondition()

    def test_repair_restores_condition(self):
        car = makeCar("Nissan Silvia S15")
        car.damage(40)
        self.assertEqual(car.getRepairCost(), 40 * 50)
        car.repair()
        self.assertEqual(car.getCondition(), 100)

    def test_max_tune_raises_error(self):
        car = makeCar("Nissan Silvia S15")
        for _ in range(Car.max_tune - 1):
            car.upgradeTune()
        with self.assertRaises(MaxTune):
            car.upgradeTune()


class TestDriver(unittest.TestCase):

    def test_average_before_runs_raises_error(self):
        with self.assertRaises(NoRunsRecorded):
            newDriver().getAverageScore()

    def test_best_before_runs_raises_error(self):
        with self.assertRaises(NoRunsRecorded):
            newDriver().getBestScore()

    def test_average_and_best(self):
        driver = newDriver()
        driver.recordRun(80)
        driver.recordRun(60)
        self.assertEqual(driver.getAverageScore(), 70.0)
        self.assertEqual(driver.getBestScore(), 80)

    def test_complete_run_uses_tyres_and_damages_car(self):
        driver = newDriver()
        driver.completeRun(75, spins=1)
        car = driver.getCar()
        self.assertEqual(car.getTyresets(), Car.starting_tyres - 1)
        self.assertEqual(car.getCondition(), 100 - Driver.wear_per_run - Driver.spin_damage)

    def test_invalid_score_raises_value_error(self):
        with self.assertRaises(ValueError):
            newDriver().recordRun(150)

    def test_invalid_skill_raises_value_error(self):
        with self.assertRaises(ValueError):
            newDriver(skill=0)

    def test_empty_name_raises_value_error(self):
        with self.assertRaises(ValueError):
            newDriver(name="   ")


class TestTeam(unittest.TestCase):

    def setUp(self):
        self.team = createStartingTeam()     # 3 drivers, €20,000

    def test_starting_team(self):
        self.assertEqual(self.team.getSize(), 3)
        self.assertEqual(self.team.getBudget(), 20000)

    def test_spend_too_much_raises_error(self):
        with self.assertRaises(InsufficientFunds):
            self.team.spend(999999)
        self.assertEqual(self.team.getBudget(), 20000)      # nothing taken

    def test_buy_tyres(self):
        driver = self.team.getDriver(0)
        self.team.buyTyres(driver)
        self.assertEqual(driver.getCar().getTyresets(), Car.starting_tyres + 1)
        self.assertEqual(self.team.getBudget(), 20000 - Team.tyre_price)

    def test_squad_full_raises_error(self):
        self.team.signDriver(newDriver("Extra One"), 0)
        self.team.signDriver(newDriver("Extra Two"), 0)
        with self.assertRaises(SquadFull):
            self.team.signDriver(newDriver("Extra Three"), 0)

    def test_duplicate_driver_raises_error(self):
        with self.assertRaises(DuplicateDriver):
            self.team.signDriver(newDriver("ren okada"), 0)

    def test_release_last_driver_raises_error(self):
        self.team.releaseDriver(0)
        self.team.releaseDriver(0)
        with self.assertRaises(MinimumSquad):
            self.team.releaseDriver(0)

    def test_upgrade_costs_money(self):
        driver = self.team.getDriver(0)
        cost = self.team.upgradeCar(driver)
        self.assertEqual(driver.getCar().getTuneLevel(), 2)
        self.assertEqual(self.team.getBudget(), 20000 - cost)

    def test_top_driver_and_sorting(self):
        with self.assertRaises(NoRunsRecorded):
            self.team.getTopDriver()
        self.team.getDriver(1).recordRun(90)
        self.team.getDriver(2).recordRun(60)
        self.assertEqual(self.team.getTopDriver().getName(), "Aoi Fujita")
        names = [d.getName() for d in self.team.getSortedDrivers("Best score")]
        self.assertEqual(names, ["Aoi Fujita", "Daichi Mori", "Ren Okada"])

    def test_reset_all(self):
        driver = self.team.getDriver(0)
        driver.completeRun(80, 0)
        self.team.spend(5000)
        self.team.resetAll()
        self.assertEqual(self.team.getBudget(), 20000)
        self.assertEqual(driver.getRunsCompleted(), 0)
        self.assertEqual(driver.getCar().getTyresets(), Car.starting_tyres)


class TestMiniGameScoring(unittest.TestCase):

    def test_perfect_press(self):
        self.assertEqual(scoreSection(100, 100, 20), (100, False))

    def test_edge_of_sweet_spot(self):
        self.assertEqual(scoreSection(120, 100, 20), (75, False))

    def test_way_off_is_a_spin(self):
        self.assertEqual(scoreSection(200, 100, 20), (0, True))

# v0.13
class TestDraft(unittest.TestCase):

    def setUp(self):
        self.draft = Draft(createDraftPool(), draft_budget)

    def test_pick_takes_the_fee(self):
        self.draft.pick(0)
        self.assertEqual(self.draft.getBudgetLeft(), draft_budget - self.draft.getFee(0))

    def test_pick_twice_raises_error(self):
        self.draft.pick(0)
        with self.assertRaises(DuplicateDriver):
            self.draft.pick(0)

    def test_fourth_pick_raises_error(self):
        for index in (7, 8, 9):
            self.draft.pick(index)
        with self.assertRaises(SquadFull):
            self.draft.pick(6)

    def test_too_expensive_raises_error(self):
        small = Draft(createDraftPool(), 5000)
        with self.assertRaises(InsufficientFunds):
            small.pick(0)

    def test_unpick_refunds(self):
        self.draft.pick(0)
        self.draft.unpick(0)
        self.assertEqual(self.draft.getBudgetLeft(), draft_budget)

    def test_empty_name_raises_error(self):
        with self.assertRaises(InvalidTeamName):
            self.draft.buildTeam("   ")

    def test_long_name_raises_error(self):
        with self.assertRaises(InvalidTeamName):
            self.draft.buildTeam("x" * (Draft.max_name_length + 1))

    def test_incomplete_draft_raises_error(self):
        self.draft.pick(0)
        with self.assertRaises(DraftIncomplete):
            self.draft.buildTeam("Midnight Club")

    def test_build_team(self):
        for index in (0, 1, 9):
            self.draft.pick(index)
        team = self.draft.buildTeam("  Midnight Club ")
        self.assertEqual(team.getName(), "Midnight Club")
        self.assertEqual(team.getSize(), 3)
        self.assertEqual(team.getBudget(), self.draft.getBudgetLeft())
# v0.13

# v0.15
def playRound(season, teamScore):
    season.startRound()
    current = season.getCurrentRound()
    for driver in current.getQualifyingQueue():
        current.recordQualifying(driver, teamScore)
    current.finishQualifying()
    battle = current.getNextBattle()
    while battle is not None:
        for driver in current.needsTeamRun(battle):
            battle.record(driver, teamScore)
        current.completeBattle(battle)
        battle = current.getNextBattle()
    return season.finishRound()


class TestBattle(unittest.TestCase):

    def test_higher_score_wins(self):
        a, b = newDriver("A"), newDriver("B")
        battle = Battle("Final", a, b)
        battle.record(a, 70)
        battle.record(b, 80)
        self.assertIs(battle.decide(), b)
        self.assertIs(battle.getLoser(), a)
        self.assertEqual(b.getBattleWins(), 1)

    def test_tie_goes_to_higher_seed(self):
        a, b = newDriver("A"), newDriver("B")
        battle = Battle("Final", a, b)
        battle.record(a, 75)
        battle.record(b, 75)
        self.assertIs(battle.decide(), a)

    def test_forfeit_loses(self):
        a, b = newDriver("A"), newDriver("B")
        battle = Battle("Final", a, b)
        battle.forfeit(a)
        battle.record(b, 10)
        self.assertIs(battle.decide(), b)

    def test_decide_before_both_run_raises_error(self):
        a, b = newDriver("A"), newDriver("B")
        battle = Battle("Final", a, b)
        battle.record(a, 50)
        with self.assertRaises(ValueError):
            battle.decide()


class TestSeason(unittest.TestCase):

    def setUp(self):
        self.team = createStartingTeam()
        self.season = Season(self.team, createRivals(), random.Random(1))

    def test_start_round_pays_wages(self):
        wages = self.season.startRound()
        self.assertEqual(wages, self.season.getWageBill())
        self.assertEqual(self.team.getBudget(), 20000 - wages)

    def test_bankrupt_when_wages_unaffordable(self):
        self.team.spend(self.team.getBudget() - 100)     # leave €100
        with self.assertRaises(Bankrupt):
            self.season.startRound()

    def test_bracket_is_top_8_seeded(self):
        self.season.startRound()
        current = self.season.getCurrentRound()
        for driver in current.getQualifyingQueue():
            current.recordQualifying(driver, 99)
        current.finishQualifying()
        ranking = current.getRanking()
        battles = current.getBattles()
        self.assertEqual(len(battles), 4)
        self.assertEqual(battles[0].getDrivers(), [ranking[0], ranking[7]])     # 1 v 8

    def test_must_qualify_team_first(self):
        self.season.startRound()
        with self.assertRaises(ValueError):
            self.season.getCurrentRound().finishQualifying()

    def test_did_not_start_misses_bracket(self):
        self.season.startRound()
        current = self.season.getCurrentRound()
        for driver in current.getQualifyingQueue():
            current.recordQualifying(driver, None)
        current.finishQualifying()
        for battle in current.getBattles():
            for driver in battle.getDrivers():
                self.assertFalse(current.isTeamDriver(driver))

    def test_round_gives_points_and_prize(self):
        before = self.team.getBudget()
        results, earnings = playRound(self.season, 100)
        positions = [position for _, position, _, _ in results]
        self.assertEqual(positions.count(1), 1)
        self.assertEqual(positions.count(2), 1)
        self.assertEqual(sum(d.getPoints() for d in self.season.getStandings()), 25 + 18 + 12 * 2 + 6 * 4)
        self.assertEqual(self.team.getBudget(), before - self.season.getWageBill() + earnings)

    def test_full_season_has_champion(self):
        with self.assertRaises(ValueError):
            self.season.getChampion()
        for _ in range(Season.total_rounds):
            playRound(self.season, 90)
        self.assertTrue(self.season.isOver())
        champion = self.season.getChampion()
        self.assertEqual(champion, self.season.getStandings()[0])
        with self.assertRaises(ValueError):
            self.season.startRound()

    def test_reset_season(self):
        playRound(self.season, 90)
        self.season.resetAll()
        self.assertEqual(self.season.getRoundsDone(), 0)
        self.assertTrue(all(d.getPoints() == 0 for d in self.season.getStandings()))
        self.assertEqual(self.team.getBudget(), 20000)
# v0.15


# v0.15 crew chief scoring
class TestScoringAndOrders(unittest.TestCase):

    def test_score_is_half_timing_half_rating(self):
        driver = newDriver(skill = 50)
        self.assertEqual(driver.blendScore(100), round(100 * 0.5 + driver.getRating() * 0.5))

    def test_better_driver_scores_higher_with_same_timing(self):
        rookie = newDriver("Rookie", 30)
        star = Driver("Star", 90, 900, makeCar("Toyota Supra MK4"))
        self.assertGreater(star.blendScore(80), rookie.blendScore(80))

    def test_upgrade_raises_rating(self):
        driver = newDriver()
        before = driver.getRating()
        driver.getCar().upgradeTune()
        self.assertGreater(driver.getRating(), before)

    def test_team_orders(self):
        a, b = newDriver("A"), newDriver("B")
        battle = Battle("Semi-final", a, b)
        battle.awardTo(b)
        self.assertIs(battle.getWinner(), b)
        self.assertTrue(battle.isTeamOrder())
        self.assertEqual(b.getBattleWins(), 1)
        with self.assertRaises(ValueError):
            battle.awardTo(a)

    def test_rivals_improve_each_round(self):
        first = Round(1, [], createRivals(), random.Random(1))
        fourth = Round(4, [], createRivals(), random.Random(1))
        self.assertEqual(first.getRivalBonus(), 0)
        self.assertEqual(fourth.getRivalBonus(), 3 * Round.rival_improvement)

    def test_team_battle_detected(self):
        team = createStartingTeam()
        current = Round(1, team.getDrivers(), createRivals(), random.Random(1))
        a, b = team.getDriver(0), team.getDriver(1)
        self.assertTrue(current.isTeamBattle(Battle("Final", a, b)))
        self.assertFalse(current.isTeamBattle(Battle("Final", a, createRivals()[0])))
# v0.15


if __name__ == "__main__":
    unittest.main(verbosity=2)