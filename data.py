from models import Car, Driver, Team

team_name = "Night Line Racing"
starting_budget = 20000

car_catalogue = {   # v0.14
    "Nissan Silvia S15":    (250, 60, "images/cars/s15"),
    "Toyota AE86":          (130, 55, "images/cars/ae86"),
    "Toyota Supra MK4":     (320, 58, "images/cars/mk4"),
    "Mazda RX-7 FD":        (280, 62, "images/cars/rx7"),
    "Nissan 350Z":          (290, 57, "images/cars/350z"),
    "Toyota Chaser JZX100": (300, 59, "images/cars/chaser"),
    "Nissan Skyline R34":   (280, 58, "images/cars/r34"),
}

def makeCar(model):
    horsepower, angle, image = car_catalogue[model]
    return Car(model, horsepower, angle, image)

def signingFee(skill):
    return skill * 150

def wageFor(skill):
    return skill * 10

def createStartingTeam():
    team = Team(team_name, starting_budget)
    team.addDriver(Driver("Ren Okada", 72, wageFor(72), makeCar("Nissan Silvia S15")))
    team.addDriver(Driver("Aoi Fujita", 64, wageFor(64), makeCar("Toyota AE86")))
    team.addDriver(Driver("Daichi Mori", 58, wageFor(58), makeCar("Mazda RX-7 FD")))
    return team

# v0.13
draft_budget = 48000

draft_pool = [
    ("Kaito Shimizu",  88, "Toyota Supra MK4"),
    ("Rina Takeda",    82, "Nissan Silvia S15"),
    ("Haruto Kimura",  76, "Mazda RX-7 FD"),
    ("Mei Nakano",     70, "Nissan 350Z"),
    ("Sota Ishikawa",  66, "Toyota Chaser JZX100"),
    ("Yuna Kobayashi", 61, "Nissan Skyline R34"), # v0.14 - v0.15 overlooked change
    ("Riku Matsuda",   55, "Toyota AE86"),
    ("Hana Ogawa",     49, "Nissan Skyline R34"), # v0.14 - v0.15 overlooked change 
    ("Kenji Arakawa",  43, "Toyota AE86"),
    ("Nao Fujii",      37, "Mazda RX-7 FD"),
]


def createDraftPool():
    pool = []
    for name, skill, car in draft_pool:
        pool.append((Driver(name, skill, wageFor(skill), makeCar(car)), signingFee(skill)))
    return pool
# v0.13


# v0.15 - rival drivers seed
rival_drivers = [
    ("Shun Takahara",   90, "Toyota Supra MK4"),
    ("Akira Nishimura", 86, "Nissan Skyline R34"),
    ("Emi Sakamoto",    83, "Toyota Chaser JZX100"),
    ("Daisuke Hori",    80, "Nissan Silvia S15"),
    ("Kenta Morimoto",  77, "Mazda RX-7 FD"),
    ("Saki Yoshida",    74, "Nissan 350Z"),
    ("Taro Watanabe",   71, "Toyota Supra MK4"),
    ("Mio Hayashi",     68, "Nissan Silvia S15"),
    ("Ryo Aoki",        64, "Toyota AE86"),
    ("Kana Endo",       60, "Nissan Skyline R34"),
    ("Yusuke Okamoto",  56, "Toyota Chaser JZX100"),
    ("Ayaka Mori",      52, "Toyota AE86"),
    ("Jun Kondo",       47, "Mazda RX-7 FD"),
]


def createRivals():
    return [Driver(name, skill, wageFor(skill), makeCar(car)) for name, skill, car in rival_drivers]
# v0.15