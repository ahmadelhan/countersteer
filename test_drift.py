import unittest

from data import createStartingTeam, makeCar
from models import Car, Driver, Team
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
