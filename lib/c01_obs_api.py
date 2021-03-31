import numpy as np
from pysc2.lib import features
from pysc2.lib import units


class ObsAPI(object):
    """ Main class for API wrappers """

    # To be populated by get_len()
    len_barrackses: int = None
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
        self.len_barrackses = len(
            self.get_my_units_by_type(obs, units.Terran.Barracks))
        self.len_barrackses_100 = len(
            self.get_my_completed_units_by_type(obs, units.Terran.Barracks))

        self.len_supply_depots_100 = len(
            self.get_my_completed_units_by_type(obs, units.Terran.SupplyDepot))
        self.len_scvs = len(self.get_my_units_by_type(obs, units.Terran.SCV))
        self.free_supply = (obs.observation.player.food_cap -
                            obs.observation.player.food_used)

    def get_shortest_queue_building(self, building_list):
        all_order_length = []
        if len(building_list) == 0:
            raise Exception(f"Empty building list")
        for building in building_list:
            all_order_length.append(building.order_length)
        print(
            f"{len(all_order_length)} buildings in order list = {all_order_length}"
        )
        res1 = np.argmin(all_order_length)
        res2 = np.argmin([building.order_length for building in building_list])
        if res1 == res2 and len(building_list) > 1:
            self.logger.debug("OK to use short form")
        else:
            self.logger.warn("Cannot use short form")
        return building_list[res1]

    def get_best_barrack(self, obs):
        if self.len_barrackses_100 < 1:
            raise Exception(f"No barracks to choose from")
        return self.get_shortest_queue_building(
            self.get_my_completed_units_by_type(obs, units.Terran.Barracks))
