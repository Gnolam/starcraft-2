import random
import numpy as np
from pysc2.lib import units, features, actions
from lib.G3ai.ai_base import aiBase
from lib.G3ai.action_list import BuildTicketsWar


class Sergant(aiBase):
    agent_name = "aSgt"
    TF1 = None

    def __init__(self, cfg):
        super().__init__(cfg)
        self.logger.debug("Sergant::init()")

    def war_attack(self, obs):  # -> actions.RAW_FUNCTIONS:
        """Performs an attack using units in TF1 only

        Returns:
            [SC2 action]: actions.RAW_FUNCTIONS.no_op()
        """
        all_my_marines = self.get_my_units_by_type(obs, units.Terran.Marine)
        self.logger.debug("count(all my marines)=%i" % len(all_my_marines))

        if self.TF1 is None:
            # marines = []
            self.logger.debug("FT1 is empty. Quitting")
            return actions.RAW_FUNCTIONS.no_op()
        # marines = [
        #     unit for unit in obs.observation.raw_units
        #     if unit.unit_type == units.Terran.Marine and unit.alliance ==
        #     features.PlayerRelative.SELF and unit.tag in set(self.TF1)
        # ]
        TF1_marines = [
            marine for marine in all_my_marines if marine.tag in set(self.TF1)
        ]

        self.logger.debug("count(alive TF1 marines)=%i" % len(TF1_marines))
        if len(TF1_marines) > 0:

            attack_xy = (69 if self.pipeline.base_top_left else 19 +
                         random.randint(-6, 6),
                         77 if self.pipeline.base_top_left else 27 +
                         random.randint(-6, 6))

            # ToDo: record my Base (x,y) at the start of the game
            # my_base_xy = (19, 23) if self.base_top_left else (38, 44) # 64
            my_base_xy = (19,
                          27) if self.pipeline.base_top_left else (69,
                                                                   77)  # 96

            enemy_marines = self.get_enemy_units_by_type(
                obs, units.Terran.Marine)
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
                self.logger.warning("No target found, Victory?")
                # raise Exception("Failed to find a target for attack")
                return actions.RAW_FUNCTIONS.no_op()

            # If clause may me redundant here
            if attack_target is not None:
                attack_xy = (attack_target.x, attack_target.y)
                self.logger.debug(f"'selected_target' is: '{selected_target}'")

            # ??? distances = self.get_distances(obs, TF1_marines, attack_xy)

            # ??? marine = TF1_marines[np.argmax(distances)]
            # if global_log_action_logic:
            #     fh_action_logic.write("\r\n------- Attack ------------------\r\nNumber of marines: %i\r\n" % len(marines))
            #     fh_action_logic.write("Closest mariner: %i\r\n" % marine.tag)

            # Create an ampty list for army
            marine_army = []
            for marine in TF1_marines:
                marine_army.append(marine.tag)

            # if global_log_action_logic:
            #     fh_action_logic.write("Army composition: %s\r\n" % str(marine_army))

            x_offset = random.randint(-4, 4)
            y_offset = random.randint(-4, 4)
            self.logger.debug("Action: Attack('%s')" % selected_target)
            return actions.RAW_FUNCTIONS.Attack_pt(
                "now", marine_army,
                (attack_xy[0] + x_offset, attack_xy[1] + y_offset))
            # "now", marine.tag, (attack_xy[0] + x_offset, attack_xy[1] + y_offset))
        else:
            self.logger.debug("All TF1 units are dead. Resetting")
            self.TF1 = None
            return actions.RAW_FUNCTIONS.no_op()

    def transfer_reserves_to_TF1(self, obs):
        # ToDo: rewrite this chunk to transfer 'ALL' units into TF1

        all_my_marines = self.get_my_units_by_type(obs, units.Terran.Marine)
        all_my_marine_IDs = [(marine.tag) for marine in all_my_marines]

        if all_my_marine_IDs is None:
            self.logger.error("No marines to transfer")
        else:
            if self.TF1 is None:
                transfer_marine_IDs = list(set(all_my_marine_IDs))
            else:
                transfer_marine_IDs = list(
                    set(all_my_marine_IDs).difference(self.TF1))
            self.logger.info(
                f"Reinforcement has arrived: Transferring {len(transfer_marine_IDs)} marines to TF1"
            )

            self.logger.debug(
                f"TF1 Size:{len(all_my_marine_IDs)-len(transfer_marine_IDs)}, TF2 Size: {len(transfer_marine_IDs)}, IDs: {str(transfer_marine_IDs)}"
            )

            self.TF1 = all_my_marine_IDs

            self.logger.debug(
                f"New TF1 assignment. Size: {len(self.TF1)}, IDs: {str(self.TF1)}"
            )


class aiGeneral(aiBase, BuildTicketsWar):

    peps = None
    fn_transfer_to_TF1 = None
    agent_name = "aiWarPlanner"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.logger.debug("aiGeneral::init()")
        self.peps = Sergant(cfg)

        # It is used by BuildTicketsWar::pt_Gen_transfer_reserve()
        self.fn_transfer_to_TF1 = self.peps.transfer_reserves_to_TF1
        if self.fn_transfer_to_TF1 is None:
            raise Exception(
                "fn_transfer_to_TF1 callable pointer is still None")

    def get_state(self, obs):
        # State vector should be revised to take into account both ours
        #   and enemy military potential
        my_marines = self.get_my_units_by_type(obs, units.Terran.Marine)

        # enemy_barrackses = self.get_enemy_units_by_type(obs, units.Terran.Barracks)
        # enemy_factories = self.get_enemy_units_by_type(obs, units.Terran.Factory)
        # enemy_starport = self.get_enemy_units_by_type(obs, units.Terran.Starport)
        enemy_marines = self.get_enemy_units_by_type(obs, units.Terran.Marine)
        enemy_marauders = self.get_enemy_units_by_type(obs,
                                                       units.Terran.Marauder)
        enemy_Tanks1 = self.get_enemy_units_by_type(obs,
                                                    units.Terran.SiegeTank)
        enemy_Tanks2 = self.get_enemy_units_by_type(
            obs, units.Terran.SiegeTankSieged)
        enemy_Hells = self.get_enemy_units_by_type(obs, units.Terran.Hellion)

        enemy_army = \
            len(enemy_marines) * 1 + \
            len(enemy_marauders) * 2 + \
            len(enemy_Tanks1) * 4 + \
            len(enemy_Tanks2) * 4 + \
            len(enemy_Hells) * 3

        if enemy_army < 10:
            enemy_army_band = enemy_army
        elif enemy_army < 30:
            enemy_army_band = int((enemy_army - 10) / 3) * 3 + 10
        else:
            enemy_army_band = int((enemy_army - 30) / 5) * 5 + 30

        return (len(my_marines), enemy_army_band)
