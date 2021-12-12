import enum

class Terran(enum.IntEnum):
    """Terran units."""
    Armory = 29
    AutoTurret = 31
    Banshee = 55
    Barracks = 21
    BarracksFlying = 46
    BarracksReactor = 38
    BarracksTechLab = 37
    Battlecruiser = 57
    Bunker = 24
    CommandCenter = 18
    CommandCenterFlying = 36
    Cyclone = 692
    EngineeringBay = 22
    Factory = 27
    FactoryFlying = 43
    FactoryReactor = 40
    FactoryTechLab = 39
    FusionCore = 30
    Ghost = 50
    GhostAcademy = 26
    GhostAlternate = 144
    GhostNova = 145
    Hellion = 53
    Hellbat = 484
    KD8Charge = 830
    Liberator = 689
    LiberatorAG = 734
    MULE = 268
    Marauder = 51
    Marine = 48
    Medivac = 54
    MissileTurret = 23
    Nuke = 58
    OrbitalCommand = 132
    OrbitalCommandFlying = 134
    PlanetaryFortress = 130
    PointDefenseDrone = 11
    Raven = 56
    Reactor = 6
    Reaper = 49
    Refinery = 20
    RefineryRich = 1960
    RepairDrone = 1913
    SCV = 45
    SensorTower = 25
    SiegeTank = 33
    SiegeTankSieged = 32
    Starport = 28
    StarportFlying = 44
    StarportReactor = 42
    StarportTechLab = 41
    SupplyDepot = 19
    SupplyDepotLowered = 47
    TechLab = 5
    Thor = 52
    ThorHighImpactMode = 691
    VikingAssault = 34
    VikingFighter = 35
    WidowMine = 498
    WidowMineBurrowed = 500
  
print(str(Terran(21)))