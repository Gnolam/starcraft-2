import numpy as np
import random
from pysc2.lib import features, actions, units
import collections
"""
Module for basic functionality with SC2 'obs' object
"""


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

    def select_scv_to_build(self, obs, xy_options, ith_count):
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)

        if len(xy_options) <= ith_count:
            self.logger.error("array is smaller than index: index = " +
                              str(ith_count) + ", while array = " +
                              str(xy_options))

        self.logger.debug("index = " + str(ith_count) + ", array = " +
                          str(xy_options))

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
            raise Exception("No barracks to choose from")
        return self.get_shortest_queue(
            self.get_my_completed_units_by_type(obs, units.Terran.Barracks))

    def resume_harvesting(self, obs):
        """
        Assigns 'harvest minerals' order if idle workers exist
        
        Note: Should be called only if current order is None
        """

        # Init
        worker_type = units.Terran.SCV

        idle_workers = [
            worker for worker in self.get_my_units_by_type(obs, worker_type)
            if worker.order_length == 0
        ]

        if len(idle_workers) > 0:
            mineral_patches = [
                unit for unit in obs.observation.raw_units
                if unit.unit_type in [
                    units.Neutral.BattleStationMineralField,
                    units.Neutral.BattleStationMineralField750, units.Neutral.
                    LabMineralField, units.Neutral.LabMineralField750,
                    units.Neutral.MineralField, units.Neutral.MineralField750,
                    units.Neutral.PurifierMineralField,
                    units.Neutral.PurifierMineralField750,
                    units.Neutral.PurifierRichMineralField,
                    units.Neutral.PurifierRichMineralField750, units.Neutral.
                    RichMineralField, units.Neutral.RichMineralField750
                ]
            ]
            random_idle_worker = random.choice(idle_workers)
            distances = self.get_distances(
                obs, mineral_patches,
                (random_idle_worker.x, random_idle_worker.y))
            closest_mineral_patch = mineral_patches[np.argmin(distances)]

            return actions.RAW_FUNCTIONS.Harvest_Gather_unit(
                "now", random_idle_worker, closest_mineral_patch.tag)
        # Allows to take another action
        return None

    def report_invalid_method(self):
        """Helper function to report a call to invalid method"""
        # ToDO: detect caller's name
        err_msg = 'This method should not be called directly. It is a placeholder only'
        self.logger.error(err_msg)
        raise Exception(f"{self.__class__.__name__}::run(): {err_msg}")


def get_unit_type_counts(obs, unit_list: list) -> dict:
    """ Returns a dictionary of unit counts by type """
    unit_type_count = [
        str(units.Terran(unit.unit_type)) for unit in obs.observation.raw_units
        if unit.tag in set(unit_list)
    ]

    return dict(collections.Counter(unit_type_count))


def get_enemy_unit_type_counts(obs) -> dict:
    """ Returns a collection of enemy unit counts by type """

    return get_unit_type_counts(obs, [
        unit.tag for unit in obs.observation.raw_units
        if unit.alliance == features.PlayerRelative.ENEMY
    ])
