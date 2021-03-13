import random
import numpy as np

from c02_lifecycle import GameLifecycle
from pysc2.lib import units, features, actions


class L2AgentPeps(GameLifecycle):
    action_list = ("war_do_nothing", "war_attack")
    agent_name = "peps"
    TF1 = None

    # def __init__(self, cfg):
    #     logging.getLogger(self.agent_name).info(f"L2AgentPeps.init({__name__})")
    #     super(L2AgentPeps, self).__init__(cfg)

    # def step(self, obs):
    #     return super(L2AgentPeps, self).step(obs)

    def get_state(self, obs):
        marines = self.get_my_units_by_type(obs, units.Terran.Marine)

        # enemy_scvs = self.get_enemy_units_by_type(obs, units.Terran.SCV)
        # enemy_command_centers =
        #   self.get_enemy_units_by_type(obs, units.Terran.CommandCenter)
        # enemy_supply_depots =
        #   self.get_enemy_units_by_type(obs, units.Terran.SupplyDepot)
        # enemy_barrackses = self.get_enemy_units_by_type(
        #     obs, units.Terran.Barracks)
        # enemy_factories = self.get_enemy_units_by_type(obs,
        #                                                units.Terran.Factory)
        # enemy_starport = self.get_enemy_units_by_type(obs,
        #                                               units.Terran.Starport)
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

        # state_dict = {
        #     "marines": len(marines),
        #     "enemy_barrackses": len(enemy_barrackses),
        #     "enemy_factories ": len(enemy_factories),
        #     "enemy_starport ": len(enemy_starport),
        #     "enemy_marines": len(enemy_marines),
        #     "enemy_marauders": len(enemy_marauders),
        #     "enemy_Tanks1": len(enemy_Tanks1),
        #     "enemy_Tanks2": len(enemy_Tanks2),
        #     "enemy_Hells": len(enemy_Hells),
        #     "enemy_army": enemy_army,
        #     "enemy_army_band": enemy_army_band
        # }

        # self.log_actions(",get_state:")
        # for k, v in state_dict.items():
        #     self.log_actions(" %s=%s" % (k, v))

        return (len(marines), enemy_army_band)

    def war_do_nothing(self, obs, check_action_availability_only):
        return True if check_action_availability_only else None

    def war_attack(self, obs, check_action_availability_only):
        should_log = not (check_action_availability_only)
        marines = self.get_my_units_by_type(obs, units.Terran.Marine)
        if should_log:
            self.logger.debug("  > all marines=%i" % len(marines))

        if self.TF1 is None:
            marines = []
        else:
            marines = [
                unit for unit in obs.observation.raw_units
                if unit.unit_type == units.Terran.Marine and unit.alliance ==
                features.PlayerRelative.SELF and unit.tag in set(self.TF1)
            ]
            marines = [
                marine for marine in marines if marine.tag in set(self.TF1)
            ]

        if should_log:
            self.logger.debug("  > TF1 marines=%i" % len(marines))
        if len(marines) > 0:
            # attack_xy = (38, 44) if self.base_top_left else (19, 23) # 64
            attack_xy = (69 if self.base_top_left else 19 +
                         random.randint(-6, 6),
                         77 if self.base_top_left else 27 +
                         random.randint(-6, 6))

            if True:
                # ToDo: record my Base (x,y) at the start of the game
                # my_base_xy = (19, 23) if self.base_top_left else (38, 44) # 64
                my_base_xy = (19, 27) if self.base_top_left else (69, 77)  # 96

                enemy_marines = self.get_enemy_units_by_type(
                    obs, units.Terran.Marine)
                enemy_scvs = self.get_enemy_units_by_type(
                    obs, units.Terran.SCV)
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
                        self.get_distances(obs, any_enemy_targets,
                                           my_base_xy))]
                    selected_target = "ANY"

                if attack_target is not None:
                    attack_xy = (attack_target.x, attack_target.y)
                    if should_log:
                        self.logger.debug(
                            f"  > No target was selected. 'selected_target' case is: '{selected_target}'"
                        )

                    # self.log_decisions(
                    #     "No target was selected.\n  'Any enemy' vector is: %s\n" % str(any_enemy_targets),
                    #     should_log=True)

            else:
                selected_target = "Default"
            distances = self.get_distances(obs, marines, attack_xy)

            marine = marines[np.argmax(distances)]
            # if global_log_action_logic:
            #     fh_action_logic.write("\r\n------- Attack ------------------\r\nNumber of marines: %i\r\n" % len(marines))
            #     fh_action_logic.write("Closest mariner: %i\r\n" % marine.tag)

            # Create an ampty list for army
            marine_army = []
            for marine in marines:
                marine_army.append(marine.tag)

            # if global_log_action_logic:
            #     fh_action_logic.write("Army composition: %s\r\n" % str(marine_army))

            x_offset = random.randint(-4, 4)
            y_offset = random.randint(-4, 4)
            if should_log:
                self.logger.debug("Action: Attack('%s')" % selected_target)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Attack_pt(
                "now", marine_army,
                (attack_xy[0] + x_offset, attack_xy[1] + y_offset))
            # "now", marine.tag, (attack_xy[0] + x_offset, attack_xy[1] + y_offset))

        if should_log:
            self.logger.debug("FAIL")
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()

    def assign_TF1(self, unit_IDs):
        if unit_IDs is not None:
            if len(unit_IDs) > 0:
                self.TF1 = unit_IDs
                self.logger.debug(
                    f"New TF1 assignment. Size: {len(unit_IDs)}, IDs: {str(unit_IDs)}"
                )
