class GameError(Exception):
    pass

class NoTyresLeft(GameError):
    pass

class CarDamaged(GameError):
    pass

class InsufficientFunds(GameError):
    pass

class SquadFull(GameError):
    pass

class MinimumSquad(GameError):
    pass

class DuplicateDriver(GameError):
    pass

class NoRunsRecorded(GameError):
    pass

class MaxTune(GameError):
    pass

class Bankrupt(GameError):
    pass

