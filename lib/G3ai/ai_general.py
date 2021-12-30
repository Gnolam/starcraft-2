import random
import numpy as np
from pysc2.lib import units, features, actions
from lib.G3ai.ai_base import aiBase
from lib.G3ai.action_list import BuildTicketsWar
from lib.c01_obs_api import get_enemy_unit_type_counts


class Sergant(aiBase):
    agent_name = "aSgt"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.log.debug("Sergant::init()")
        self.tf1_tag_list = []
        self.reserve_tag_list = []
        self.my_all_army_tag_list = []

    def update_my_army(self, obs):
        self.my_all_army_tag_list = [
            marine.tag
            for marine in self.get_my_units_by_type(obs, units.Terran.Marine)
        ]

    def update_tf1_and_reserve_tags(self, obs):
        """ Update the `tf1_tag_list` and `reserve_tag_list`. Drops dead units """
        self.update_my_army(obs)

        self.tf1_tag_list = list(
            set(self.my_all_army_tag_list).intersection(set(
                self.tf1_tag_list)))

        self.reserve_tag_list = list(
            set(self.my_all_army_tag_list).difference(set(self.tf1_tag_list)))

    def report_status(self, obs):
        self.log.debug(f"TF1: {len(self.tf1_tag_list)}")
        self.log.debug(f"Res: {len(self.reserve_tag_list)}")
        self.log.debug(f"All: {len(self.my_all_army_tag_list)}")

    def war_attack(self, obs):  # -> actions.RAW_FUNCTIONS:
        """Performs an attack using units in TF1 only

        Returns:
            [SC2 action]: actions.RAW_FUNCTIONS.no_op()
        """

        if len(self.tf1_tag_list) == 0:
            self.log.debug("FT1 is empty. Quitting")
            return actions.RAW_FUNCTIONS.no_op()

        tf1_units = [
            marine
            for marine in self.get_my_units_by_type(obs, units.Terran.Marine)
            if marine.tag in set(self.tf1_tag_list)
        ]

        if len(tf1_units) == 0:
            self.log.error("Should not occur. All TF1 units are dead")
            self.tf1_tag_list = []
            return actions.RAW_FUNCTIONS.no_op()

        self.log.debug(f"count(alive TF1 marines)={len(tf1_units)}")

        attack_xy = (69 if self.pipeline.base_top_left else 19 +
                     random.randint(-6, 6),
                     77 if self.pipeline.base_top_left else 27 +
                     random.randint(-6, 6))

        # ToDo: record my Base (x,y) at the start of the game
        # my_base_xy = (19, 23) if self.base_top_left else (38, 44) # 64
        my_base_xy = (19, 27) if self.pipeline.base_top_left else (69,
                                                                   77)  # 96

        enemy_marines = self.get_enemy_units_by_type(obs, units.Terran.Marine)
        enemy_scvs = self.get_enemy_units_by_type(obs, units.Terran.SCV)
        enemy_base = self.get_enemy_completed_units_by_type(
            obs, units.Terran.CommandCenter)
        any_enemy_targets = self.get_all_enemy_units(obs)

        attack_target = None
        selected_target = "N/A"

        if len(enemy_base) > 0:
            attack_target = enemy_base[np.argmin(
                self.get_distances(obs, enemy_base, my_base_xy))]
            selected_target = "Base"
        elif len(enemy_scvs) > 0:
            attack_target = enemy_scvs[np.argmin(
                self.get_distances(obs, enemy_scvs, my_base_xy))]
            selected_target = "SCV"
        elif len(enemy_marines) > 0:
            attack_target = enemy_marines[np.argmin(
                self.get_distances(obs, enemy_marines, my_base_xy))]
            selected_target = "Mariner"
        elif len(any_enemy_targets) > 0:
            attack_target = any_enemy_targets[np.argmin(
                self.get_distances(obs, any_enemy_targets, my_base_xy))]
            selected_target = "ANY"
        else:
            self.log.warning("No target found, Victory?")
            # raise Exception("Failed to find a target for attack")
            return actions.RAW_FUNCTIONS.no_op()

        # If clause may me redundant here
        if attack_target is not None:
            attack_xy = (attack_target.x, attack_target.y)
            self.log.debug(f"'selected_target' is: '{selected_target}'")

        # Create an ampty list for army
        marine_army = []
        for marine in tf1_units:
            marine_army.append(marine.tag)

        x_offset = random.randint(-4, 4)
        y_offset = random.randint(-4, 4)
        self.log.debug(f"Action: Attack('{selected_target}')")
        return actions.RAW_FUNCTIONS.Attack_pt(
            "now", marine_army,
            (attack_xy[0] + x_offset, attack_xy[1] + y_offset))
        # "now", marine.tag, (attack_xy[0] + x_offset, attack_xy[1] + y_offset))

    def transfer_reserves_to_tf1(self, obs):
        """Transfers ALL reserve units into TF1"""
        self.update_tf1_and_reserve_tags(obs)

        if len(self.reserve_tag_list) == 0:
            self.log.error("No marines to transfer")
        else:
            self.report_status(obs)

            self.tf1_tag_list = self.my_all_army_tag_list
            self.reserve_tag_list = []


class aiGeneral(aiBase, BuildTicketsWar):

    peps: Sergant = None
    fn_transfer_to_TF1 = None
    agent_name = "aiWarPlanner"
    ai_log_suffix = "War"

    # Switcher between different state functions
    define_state = None

    def __init__(self, cfg):
        super().__init__(cfg)
        self.log.debug("aiGeneral::init()")
        self.peps = Sergant(cfg)

        self.define_state = cfg.config.get('AI-General', 'define_state')
        # ToDo: validate `define_state` to be in accaptable range ('simple_1' or 'split_3')

        self.fn_db_results = "db/war_results.csv"
        self.fn_db_decisions = "db/war_decisions.csv"
        self.fn_db_states = "db/war_states.csv"

        # It is used by BuildTicketsWar::pt_Gen_transfer_reserve()
        self.fn_transfer_to_TF1 = self.peps.transfer_reserves_to_tf1
        if self.fn_transfer_to_TF1 is None:
            raise Exception(
                "fn_transfer_to_TF1 callable pointer is still None")

        self.init2()
        self.ai_drf.update()

    def get_state(self, obs):
        # State vector should be revised to take into account both ours
        #   and enemy military potential

        self.peps.update_tf1_and_reserve_tags(obs)

        tf1_size = len(self.peps.tf1_tag_list)
        res_size = len(self.peps.reserve_tag_list)

        enemy_count_dict = get_enemy_unit_type_counts(obs)

        self.write_tidy_vector_to_file(self.fn_db_states, {
            "tf1_size": tf1_size,
            "reserve_size": res_size
        }, "own_")
        self.write_tidy_vector_to_file(self.fn_db_states, enemy_count_dict,
                                       "enemy_")

        if self.define_state == 'simple_1':
            enemy_marines = self.get_enemy_units_by_type(
                obs, units.Terran.Marine)
            enemy_marauders = self.get_enemy_units_by_type(
                obs, units.Terran.Marauder)
            enemy_Tanks1 = self.get_enemy_units_by_type(
                obs, units.Terran.SiegeTank)
            enemy_Tanks2 = self.get_enemy_units_by_type(
                obs, units.Terran.SiegeTankSieged)
            enemy_Hells = self.get_enemy_units_by_type(obs,
                                                       units.Terran.Hellion)
            enemy_mines1 = self.get_enemy_units_by_type(
                obs, units.Terran.WidowMine)
            enemy_mines2 = self.get_enemy_units_by_type(
                obs, units.Terran.WidowMineBurrowed)

            enemy_army = \
                len(enemy_marines) * 1 + \
                len(enemy_marauders) * 2 + \
                len(enemy_Tanks1) * 4 + \
                len(enemy_Tanks2) * 4 + \
                len(enemy_mines1) * 3 + \
                len(enemy_mines2) * 3 + \
                len(enemy_Hells) * 3

            if enemy_army < 10:
                enemy_army_band = enemy_army
            elif enemy_army < 30:
                enemy_army_band = int((enemy_army - 10) / 3) * 3 + 10
            else:
                enemy_army_band = int((enemy_army - 30) / 5) * 5 + 30

            return (tf1_size, res_size, enemy_army_band)

        if self.define_state == 'split_3':

            enemy_foot = \
                + 1 * len(self.get_enemy_units_by_type(obs, units.Terran.Marine)) \
                + 2 * len(self.get_enemy_units_by_type(obs, units.Terran.Marauder)) \

            enemy_heavy = \
                + len(self.get_enemy_units_by_type(obs, units.Terran.SiegeTank)) \
                + len(self.get_enemy_units_by_type(obs, units.Terran.SiegeTankSieged)) \
                + len(self.get_enemy_units_by_type(obs, units.Terran.Hellion)) \
                + len(self.get_enemy_units_by_type(obs, units.Terran.Hellbat)) \
                + len(self.get_enemy_units_by_type(obs, units.Terran.WidowMine)) \
                + len(self.get_enemy_units_by_type(obs, units.Terran.WidowMineBurrowed))

            enemy_flying = \
                + len(self.get_enemy_units_by_type(obs, units.Terran.Medivac)) \
                + len(self.get_enemy_units_by_type(obs, units.Terran.Raven))

            if enemy_foot < 4:
                enemy_foot_band = 4
            elif enemy_foot < 10:
                enemy_foot_band = int((enemy_foot - 4) / 2) * 2 + 4
            else:
                enemy_foot_band = int((enemy_foot - 10) / 4) * 4 + 10

            return (tf1_size, res_size, enemy_foot_band, enemy_heavy,
                    enemy_flying)

        raise Exception(
            f"'{self.define_state}' is not an allowed value for 'define_state' variable"
        )
