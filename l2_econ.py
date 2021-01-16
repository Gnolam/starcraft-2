from l1_class import L1Agent
#from pysc2.lib import units
import logging
from pysc2.lib import actions, features, units
import numpy as np
import pandas as pd
import random


class L2AgentBob(L1Agent):
    action_list = (
        "econ_do_nothing",
        "econ_harvest_minerals",
        "econ_build_supply_depot",
        "econ_build_barracks",
        "econ_train_marine"
    )

    agent_name = "bob"

    def __init__(self, cfg):
        self.logger = logging.getLogger(self.agent_name)
        self.logger.info(f"L2AgentBob.init({__name__})")
        super(L2AgentBob, self).__init__(cfg)

    def step(self, obs):
        ## print("step at L2AgentBob (%s)" % self.agent_name)
        return super(L2AgentBob, self).step(obs)

    def get_state(self, obs):
        # info for counters
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        idle_scvs = [scv for scv in scvs if scv.order_length == 0]
        command_centers = self.get_my_units_by_type(obs, units.Terran.CommandCenter)
        supply_depots = self.get_my_units_by_type(obs, units.Terran.SupplyDepot)
        completed_supply_depots = self.get_my_completed_units_by_type(
            obs, units.Terran.SupplyDepot)
        barrackses = self.get_my_units_by_type(obs, units.Terran.Barracks)
        completed_barrackses = self.get_my_completed_units_by_type(
            obs, units.Terran.Barracks)
        marines = self.get_my_units_by_type(obs, units.Terran.Marine)

        queued_marines = (completed_barrackses[0].order_length
                          if len(completed_barrackses) > 0 else 0)

        free_supply = (obs.observation.player.food_cap -
                       obs.observation.player.food_used)
        can_afford_supply_depot = obs.observation.player.minerals >= 100
        can_afford_barracks = obs.observation.player.minerals >= 150
        can_afford_marine = obs.observation.player.minerals >= 50

        # enemy_scvs = self.get_enemy_units_by_type(obs, units.Terran.SCV)
        # enemy_command_centers = self.get_enemy_units_by_type(obs, units.Terran.CommandCenter)
        # enemy_supply_depots = self.get_enemy_units_by_type(obs, units.Terran.SupplyDepot)
        # enemy_barrackses = self.get_enemy_units_by_type(obs, units.Terran.Barracks)
        # enemy_factories = self.get_enemy_units_by_type(obs, units.Terran.Factory)
        # enemy_starport = self.get_enemy_units_by_type(obs, units.Terran.Starport)

        # state_dict = {
        #     "command_centers": len(command_centers),
        #     "scvs": len(scvs),
        #     "idle_scvs": len(idle_scvs),
        #     "supply_depots": len(supply_depots),
        #     "completed_supply_depots": len(completed_supply_depots),
        #     "barrackses": len(barrackses),
        #     "completed_barrackses": len(completed_barrackses),
        #     "marines": len(marines),
        #     "queued_marines": queued_marines,
        #     "free_supply": free_supply,
        #     "can_afford_supply_depot": can_afford_supply_depot,
        #     "can_afford_barracks": can_afford_barracks,
        #     "can_afford_marine": can_afford_marine,
        #     "enemy_command_centers": len(enemy_command_centers),
        #     "enemy_scvs": len(enemy_scvs),
        #     "enemy_supply_depots": len(enemy_supply_depots),
        #     "enemy_barrackses": len(enemy_barrackses),
        #     "enemy_factories ": len(enemy_factories),
        #     "enemy_starport ": len(enemy_starport),
        #     "enemy_army_band": enemy_army_band,
        #     "res":obs.observation.player.minerals
        # }

        # self.log_actions(",get_state:")
        # for k, v in state_dict.items():
        #     self.log_actions(" %s=%s" % (k, v))

        return (len(command_centers),
                len(scvs),
                len(idle_scvs),
                len(supply_depots),
                len(completed_supply_depots),
                len(barrackses),
                len(completed_barrackses),
                len(marines),
                queued_marines,
                free_supply,
                can_afford_supply_depot,
                can_afford_barracks,
                can_afford_marine
                )

    def econ_do_nothing(self, obs, check_action_availability_only):
        return True if check_action_availability_only else None

    def econ_harvest_minerals(self, obs, check_action_availability_only):
        ## print(" econ_harvest_minerals(%i)" % check_action_availability_only)
        should_log = not (check_action_availability_only)
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        idle_scvs = [scv for scv in scvs if scv.order_length == 0]        
        if should_log: self.logger.debug(f"  > idle_scvs={len(idle_scvs)}")
        if len(idle_scvs) > 0:
            mineral_patches = [unit for unit in obs.observation.raw_units
                               if unit.unit_type in [
                                   units.Neutral.BattleStationMineralField,
                                   units.Neutral.BattleStationMineralField750,
                                   units.Neutral.LabMineralField,
                                   units.Neutral.LabMineralField750,
                                   units.Neutral.MineralField,
                                   units.Neutral.MineralField750,
                                   units.Neutral.PurifierMineralField,
                                   units.Neutral.PurifierMineralField750,
                                   units.Neutral.PurifierRichMineralField,
                                   units.Neutral.PurifierRichMineralField750,
                                   units.Neutral.RichMineralField,
                                   units.Neutral.RichMineralField750
                               ]]
            scv = random.choice(idle_scvs)

            # ToDo: check if the distance from SCV or from StarBase
            distances = self.get_distances(obs, mineral_patches, (scv.x, scv.y))
            mineral_patch = mineral_patches[np.argmin(distances)]

            if should_log: self.logger.debug("Action: Harvest_Gather_unit")
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Harvest_Gather_unit(
                "now", scv.tag, mineral_patch.tag)
        if should_log: self.logger.debug("FAIL")
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()

    def econ_build_supply_depot(self, obs, check_action_availability_only):
        ## print(" econ_build_supply_depot(%i)" % check_action_availability_only)
        should_log = not (check_action_availability_only)
        supply_depots = self.get_my_units_by_type(obs, units.Terran.SupplyDepot)
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        if should_log: self.logger.debug(f"  > supply_depots={len(supply_depots)} minerals={obs.observation.player.minerals} scvs={len(scvs)}")
        if (len(supply_depots) < 4 and obs.observation.player.minerals >= 100 and
                len(scvs) > 0):
            # supply_depot_xy = (22, 26) if self.base_top_left else (35, 42)
            if len(supply_depots) == 0:
                supply_depot_xy = (20 + 1, 27 + 3) if self.base_top_left else (69 - 3, 77 - 3)  # 96 res
            elif len(supply_depots) == 1:
                supply_depot_xy = (20 + 3, 27 + 3) if self.base_top_left else (69 - 5, 77 - 3)  # 96 res
            elif len(supply_depots) == 2:
                supply_depot_xy = (20 - 3, 27 + 5) if self.base_top_left else (69 - 5, 77 - 5)  # 96 res
            else:
                supply_depot_xy = (20 - 3, 27 + 7) if self.base_top_left else (69 - 5, 77 - 7)  # 96 res
            distances = self.get_distances(obs, scvs, supply_depot_xy)
            scv = scvs[np.argmax(distances)]

            if should_log: self.logger.debug("Action: Build_SupplyDepot")
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Build_SupplyDepot_pt(
                "now", scv.tag, supply_depot_xy)
        if should_log: self.logger.debug("FAIL")
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()

    def econ_build_barracks(self, obs, check_action_availability_only):
        ## print(" econ_build_barracks(%i)" % check_action_availability_only)
        should_log = not (check_action_availability_only)
        completed_supply_depots = self.get_my_completed_units_by_type(
            obs, units.Terran.SupplyDepot)
        barrackses = self.get_my_units_by_type(obs, units.Terran.Barracks)
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        
        if should_log: self.logger.debug(
            "  > completed_supply_depots=%i barracks=%i minerals=%i scvs=%i" % (
            len(completed_supply_depots),
            len(barrackses),
            obs.observation.player.minerals,
            len(scvs))
        )
        if (len(completed_supply_depots) > 0 and len(barrackses) < 5 and
                obs.observation.player.minerals >= 150 and len(scvs) > 0):

            if len(barrackses) == 0:
                # Place for the 1st barrack
                # barracks_xy = (22, 21) if self.base_top_left else (35, 45)
                barracks_xy = (20 + 7, 27 + 0) if self.base_top_left else (69 - 7, 77 - 0)  # 96 res
            elif len(barrackses) == 1:
                # Place for the 2nd barrack
                # barracks_xy = (22 + 2, 21 + 2) if self.base_top_left else (35 - 2, 45 - 2)
                barracks_xy = (20 + 9, 27 + 4) if self.base_top_left else (69 - 9, 77 - 2)  # 96 res
            elif len(barrackses) == 2:
                # Place for the 3rd barrack
                # barracks_xy = (22 + 4, 21 + 4) if self.base_top_left else (35 - 4, 45 - 4)
                barracks_xy = (20 + 7, 27 + 4) if self.base_top_left else (69 - 11, 77 - 4)  # 96 res
            elif len(barrackses) == 3:
                # Place for the 4th barrack
                barracks_xy = (20 + 9, 27 + 0) if self.base_top_left else (69 - 13, 77 - 2)  # 96 res
            else:
                # Place for the last barrack
                # barracks_xy = (22 + 6, 21 + 6) if self.base_top_left else (35 - 6, 45 - 2)
                barracks_xy = (20 + 1, 27 + 6) if self.base_top_left else (69 - 7, 77 - 6)  # 96 res
            distances = self.get_distances(obs, scvs, barracks_xy)
            # scv = scvs[np.argmin(distances)]
            scv = scvs[np.argmax(distances)]
            if should_log: self.logger.debug("Action: Build_Barracks")
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Build_Barracks_pt(
                "now", scv.tag, barracks_xy)
        if should_log: self.logger.debug("FAIL")
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()

    def econ_train_marine(self, obs, check_action_availability_only):

        should_log = not (check_action_availability_only)
        completed_barrackses = self.get_my_completed_units_by_type(
            obs, units.Terran.Barracks)
        free_supply = (obs.observation.player.food_cap -
                       obs.observation.player.food_used)        
        if should_log: 
            self.logger.debug(
                "  > completed_barrackses=%i free_supply=%i minerals=%i" % (
                len(completed_barrackses),
                free_supply,
                obs.observation.player.minerals)
            )

        # BugFix: price for Mariner is 50, not 100
        if (len(completed_barrackses) > 0 and obs.observation.player.minerals >= 50
                and free_supply > 0):

            # choose the barrack with the shortest que
            all_order_length = []
            for barrack in completed_barrackses:
                all_order_length.append(barrack.order_length)
            best_barrack = completed_barrackses[np.argmin(all_order_length)]

            # if global_log_action_logic:
            #     fh_action_logic.write("\r\n------- train_marine --------\r\n")
            #     fh_action_logic.write("Number of ready barracks: %i\r\n" % len(completed_barrackses))
            #     fh_action_logic.write("Load length: %s\r\n" % str(all_order_length))
            #     fh_action_logic.write("Chosen barrack with length: %i\r\n" % best_barrack.order_length)
            
            if should_log: self.logger.debug("  > min(barracks.order_length)=%i" % best_barrack.order_length)
            
            if best_barrack.order_length < 5:
                if should_log: self.logger.debug("Action: Train_Marine")
                if check_action_availability_only:
                    return True
                return actions.RAW_FUNCTIONS.Train_Marine_quick("now", best_barrack.tag)
        if should_log: self.logger.debug("FAIL")
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()    
