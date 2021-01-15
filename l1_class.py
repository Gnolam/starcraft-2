import os
import random
import logging

import numpy as np
import pandas as pd
from pysc2.lib import actions, features, units

from lib.q_table import QLearningTable

class L1Agent:
    agent_name = "L1"
    action_list = []
    DQN_filename = None
    fh_decisions = None
    fh_state_csv = None
    fn_global_debug = None
    consistent_decision_agent = None
    logger = None
    decisions_hist = {}
    step_counter = 0
    game_num = 0

    def __init__(self, cfg):
        logging.getLogger(self.agent_name).info(f"L1.init({self.agent_name})")

        self.qtable = QLearningTable(self.action_list)

        self.DQN_filename,\
        self.fh_decisions,\
        self.fh_state_csv,\
        self.fn_global_debug\
            = cfg.get_filenames(self.agent_name)
            
        self.agent_cfg = cfg.run_cfg.get(self.agent_name)
        self.consistent_decision_agent = cfg.run_cfg.get(self.agent_name)["consistent"]
        self.new_game()

        self.logger.debug(f'consistent_decision_agent = {self.consistent_decision_agent}')

    def reset(self):
        self.new_game()

    def new_game(self):
        self.base_top_left = None
        self.previous_state = None
        self.previous_action = None

        # History of decisions for future discounting
        self.decisions_hist = {}
        self.step_counter = 0
        self.game_num += 1

    def dump_decisions_hist(self):
        # json = json.dumps(self.decisions_hist)
        if True:
            f = open("logs/decisions_G2.%s_%s.json" % (self.agent_name, self.game_num), "w")
            f.write(str(self.decisions_hist))
            f.close()

    def save_DQN(self):
        logging.getLogger(self.agent_name).debug('Record current learnings (%s): %s' % (self.agent_name, self.DQN_filename))
        self.qtable.q_table.to_pickle(self.DQN_filename, 'gzip')

    def load_DQN(self):
        if os.path.isfile(self.DQN_filename):
            logging.getLogger(self.agent_name).info('Load previous learnings (%s)' % self.agent_name)
            self.qtable.q_table = pd.read_pickle(self.DQN_filename, compression='gzip')
        else:
            self.logger.info('NO previous learnings located (%s)' % self.agent_name)

    def log_state(self, s_message, should_print=True):
        if should_print and self.fh_state_csv is not None:
            self.fh_state_csv.write(s_message)

    def get_my_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.raw_units
                if unit.unit_type == unit_type
                and unit.alliance == features.PlayerRelative.SELF]

    def get_all_enemy_units(self, obs):
        return [unit for unit in obs.observation.raw_units
                if unit.alliance == features.PlayerRelative.ENEMY]

    def get_enemy_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.raw_units
                if unit.unit_type == unit_type
                and unit.alliance == features.PlayerRelative.ENEMY]

    def get_my_completed_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.raw_units
                if unit.unit_type == unit_type
                and unit.build_progress == 100
                and unit.alliance == features.PlayerRelative.SELF]

    def get_enemy_completed_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.raw_units
                if unit.unit_type == unit_type
                and unit.build_progress == 100
                and unit.alliance == features.PlayerRelative.ENEMY]

    def get_distances(self, obs, units, xy):
        units_xy = [(unit.x, unit.y) for unit in units]
        return np.linalg.norm(np.array(units_xy) - np.array(xy), axis=1)

    def step(self, obs):
        command_centres = self.get_my_units_by_type(obs, units.Terran.CommandCenter)
        enemy_bases = self.get_enemy_completed_units_by_type(obs, units.Terran.CommandCenter)

        if len(enemy_bases) > 0 and False:
            self.logger.info("MyBase (x,y) = %i,%i \n\r" % (command_center.x, command_center.y))
            self.logger.info("Enemy base = %i,%i\n\r" % (enemy_bases[0].x, enemy_bases[0].y))

        if obs.first():
            self.base_top_left = (command_centres[0].x < 32)

        state = str(self.get_state(obs))

        # No action should take place in case state did not change
        #   no learning either
        if self.consistent_decision_agent and state == self.previous_state and (not obs.last()):
            self.logger.debug("States did not change: skipping")
            return None  # It is a simulation of NOOP

        # Original 'best known' action based on Q-Table
        action = self.qtable.choose_action(state)        
        originally_suggested_action = action

        while not (getattr(self, action)(obs, check_action_availability_only=True)):
            # previous action was not feasible, choose the alternative action randomly
            action = np.random.choice(self.action_list)
        
        if originally_suggested_action != action:
            self.logger.debug(f"Q-Action: '{originally_suggested_action.upper()}(unable to comply)' -> '{action.upper()}'")
        else:
            self.logger.debug(f"Q-Action: '{action.upper()}'")

        # Temporarily accept Draw as Win
        reward = .5 if obs.last() and obs.reward == 0 else obs.reward
        next_state = 'terminal' if obs.last() else state

        if obs.last() and self.agent_name == 'bob':
            logging.getLogger("res").info(f"Game over. Result:  {obs.reward}")

        # 'LEARN' should be across the WHOLE history
        # Q-Table should be updated to consume 'batch' history
        # Record decision for later 'batch' learning
        # ToDo: add Q-Table coef here instead of reward
        if self.previous_action is not None:
            self.decisions_hist[self.step_counter] = {
                'previous_state': self.previous_state,
                'previous_action': self.previous_action,
                'reward': reward,
                'next_state': next_state
            }

        self.step_counter += 1

        self.previous_state = state
        self.previous_action = action

        action_res = getattr(self, action)(obs, check_action_availability_only=False)
        return action_res

    def finalise_game(self):
        #print("[%s]: finalise_game()" % self.agent_name)
        self.dump_decisions_hist()
        self.learn_from_game()
        self.save_DQN()
        return

    def learn_from_game(self):
        reward = None
        reward_decay = .9

        for i in sorted(self.decisions_hist.keys(), reverse=True):
            previous_state = self.decisions_hist[i]['previous_state']
            previous_action = self.decisions_hist[i]['previous_action']

            # Only the final reward (-1 or +1) should be taken into account
            if reward is None:
                reward = self.decisions_hist[i]['reward']
            next_state = self.decisions_hist[i]['next_state']

            fh = open(self.fn_global_debug, "a+")
            fh.write('[%s]: Apply learning for step %s with reward %s\n  Action: %s\n  States (%s -> %s)\n' %
                 (self.agent_name, i, reward, previous_action, previous_state, next_state))
            fh.close()

            self.qtable.learn(
                previous_state,
                previous_action,
                reward,
                next_state,
                fn=self.fn_global_debug
            )

            reward *= reward_decay
        return

    def do_nothing(self, obs, check_action_availability_only):
        if check_action_availability_only:
            return True
        actions.RAW_FUNCTIONS.no_op()

    def econ_do_nothing(self, obs, check_action_availability_only):
        return True if check_action_availability_only else None
        
    def war_do_nothing(self, obs, check_action_availability_only):
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

    def war_attack(self, obs, check_action_availability_only):
        should_log = not (check_action_availability_only)
        marines = self.get_my_units_by_type(obs, units.Terran.Marine)        
        if should_log: self.logger.debug("  > marines=%i" % len(marines))
        if len(marines) > 0:
            # attack_xy = (38, 44) if self.base_top_left else (19, 23) # 64
            attack_xy = (
                69 if self.base_top_left else 19 + random.randint(-6, 6),
                77 if self.base_top_left else 27 + random.randint(-6, 6)
            )

            if True:
                # ToDo: record my Base (x,y) at the start of the game
                # my_base_xy = (19, 23) if self.base_top_left else (38, 44) # 64
                my_base_xy = (19, 27) if self.base_top_left else (69, 77)  # 96

                enemy_marines = self.get_enemy_units_by_type(obs, units.Terran.Marine)
                enemy_scvs = self.get_enemy_units_by_type(obs, units.Terran.SCV)
                enemy_base = self.get_enemy_completed_units_by_type(obs, units.Terran.CommandCenter)
                any_enemy_targets = self.get_all_enemy_units(obs)

                attack_target = None
                selected_target = "N/A"

                if len(enemy_base) > 0:
                    attack_target = enemy_base[np.argmin(self.get_distances(obs, enemy_base, my_base_xy))]
                    selected_target = "Base"
                elif len(enemy_scvs) > 0:
                    attack_target = enemy_scvs[np.argmin(self.get_distances(obs, enemy_scvs, my_base_xy))]
                    selected_target = "SCV"
                elif len(enemy_marines) > 0:
                    attack_target = enemy_marines[np.argmin(self.get_distances(obs, enemy_marines, my_base_xy))]
                    selected_target = "Mariner"
                elif len(any_enemy_targets) > 0:
                    attack_target = any_enemy_targets[np.argmin(self.get_distances(obs, any_enemy_targets, my_base_xy))]
                    selected_target = "ANY"

                if attack_target is not None:
                    attack_xy = (attack_target.x, attack_target.y)
                    if should_log: self.logger.debug(f"  > No target was selected. 'selected_target' case is: '{selected_target}'")
                    
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
            if should_log: self.logger.debug("Action: Attack('%s')" % selected_target)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Attack_pt(
                "now", marine_army, (attack_xy[0] + x_offset, attack_xy[1] + y_offset))
            # "now", marine.tag, (attack_xy[0] + x_offset, attack_xy[1] + y_offset))

        if should_log: self.logger.debug("FAIL")
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()
