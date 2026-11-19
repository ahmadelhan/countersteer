from models import Car, Driver, Team

team_name = "Night Line Racing"
starting_budget = 20000

car_catalogue = {
    "Nissan Silvia S15":   (250, 60, "images/s15.png"),
    "Toyota AE86":         (130, 55, "images/ae86.png"),
    "Toyota Supra MK4":    (320, 58, "images/supra.png"),
    "Mazda RX-7 FD":       (280, 62, "images/rx7.png"),
    "Nissan 350Z":         (290, 57, "images/350z.png"),
    "Toyota Chaser JZX100": (300, 59, "images/chaser.png"),
    "Nissan Silvia S13":   (205, 61, "images/s13.png"),
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
    ("Yuna Kobayashi", 61, "Nissan Silvia S13"),
    ("Riku Matsuda",   55, "Toyota AE86"),
    ("Hana Ogawa",     49, "Nissan Silvia S13"),
    ("Kenji Arakawa",  43, "Toyota AE86"),
    ("Nao Fujii",      37, "Mazda RX-7 FD"),
]


def createDraftPool():
    pool = []
    for name, skill, car in draft_pool:
        pool.append((Driver(name, skill, wageFor(skill), makeCar(car)), signingFee(skill)))
    return pool
# v0.13