from models import Car, Driver, Team

team_name = "ER8 Racing"
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