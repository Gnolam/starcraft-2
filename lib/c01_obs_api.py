import numpy as np
from pysc2.lib import features
from pysc2.lib import units


class ObsAPI(object):
    """ Main class for API wrappers """

    # To be populated by get_len()
    len_barracks: int = None
    len_barracks_100: int = None
    len_supply_depots: int = None
    len_supply_depots_100: int = None
    len_scvs: int = None
    free_supply: int = None

    def __init__(self):
        super().__init__()

    def get_my_units_by_type(self, obs, unit_type):
        return [
            unit for unit in obs.observation.raw_units
            if unit.unit_type == unit_type
            and unit.alliance == features.PlayerRelative.SELF
        ]

    def get_all_enemy_units(self, obs):
        return [
            unit for unit in obs.observation.raw_units
            if unit.alliance == features.PlayerRelative.ENEMY
        ]

    def get_enemy_units_by_type(self, obs, unit_type):
        return [
            unit for unit in obs.observation.raw_units
            if unit.unit_type == unit_type
            and unit.alliance == features.PlayerRelative.ENEMY
        ]

    def get_my_completed_units_by_type(self, obs, unit_type):
        return [
            unit for unit in obs.observation.raw_units
            if unit.unit_type == unit_type and unit.build_progress == 100
            and unit.alliance == features.PlayerRelative.SELF
        ]

    def get_enemy_completed_units_by_type(self, obs, unit_type):
        return [
            unit for unit in obs.observation.raw_units
            if unit.unit_type == unit_type and unit.build_progress == 100
            and unit.alliance == features.PlayerRelative.ENEMY
        ]

    def get_distances(self, obs, units, xy):
        units_xy = [(unit.x, unit.y) for unit in units]
        return np.linalg.norm(np.array(units_xy) - np.array(xy), axis=1)

    def get_nearest_unit(self, obs, units, xy):
        return units[np.argmax(self.get_distances(obs, units, xy))]

    def build_with_scv_xy(self, obs, xy_options, ith_count):
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        building_xy = xy_options[ith_count]
        scv = self.get_nearest_unit(obs, scvs, building_xy)
        return scv.tag, building_xy

    def get_len(self, obs):
        """ Calculate all basic state variables for decision making """
        self.len_barracks = len(
            self.get_my_units_by_type(obs, units.Terran.Barracks))
        self.len_barracks_100 = len(
            self.get_my_completed_units_by_type(obs, units.Terran.Barracks))

        self.len_supply_depots = len(
            self.get_my_units_by_type(obs, units.Terran.SupplyDepot))
        self.len_supply_depots_100 = len(
            self.get_my_completed_units_by_type(obs, units.Terran.SupplyDepot))

        self.len_scvs = len(self.get_my_units_by_type(obs, units.Terran.SCV))
        self.free_supply = (obs.observation.player.food_cap -
                            obs.observation.player.food_used)

    def get_shortest_queue(self, building_list):
        return building_list[np.argmin(
            [building.order_length for building in building_list])]

    def get_best_barrack(self, obs):
        if self.len_barracks_100 < 1:
            raise Exception(f"No barracks to choose from")
        return self.get_shortest_queue(
            self.get_my_completed_units_by_type(obs, units.Terran.Barracks))
