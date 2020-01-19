import random
import numpy as np
import pandas as pd
import os
from absl import app
from pysc2.agents import base_agent
from pysc2.lib import actions, features, units
from pysc2.env import sc2_env, run_loop

import logging

build_prefix = 'v22b'

DQN_econ = 'DQNs/v22b_econ.gz'
DQN_war = 'DQNs/v22b_war.gz'


logging.basicConfig(format='%(asctime)-15s %(message)s')
fh = logging.FileHandler('logs/%s.log' % build_prefix)
logger = logging.getLogger()
logger.setLevel("INFO")

fh_decisions = open('logs/%s_decisions.log' % build_prefix, "a+")
fh_obs = open('logs/%s_obs.log' % build_prefix, "a+")

fh_econ_state_csv = None
fh_econ_decisions = None

fh_war_state_csv = None
fh_war_decisions = open('logs/%s_war_decisions.log' % build_prefix, "a+")

global_debug = False

fh_global_debug = open('logs/%s_global.log' % build_prefix, "a+")

setup_greedy = .9
# global_log_action = True
# global_log_action_logic = False

########################################################################################################################

class QLearningTable:
    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9):
        self.actions = actions
        self.learning_rate = learning_rate
        self.reward_decay = reward_decay
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation, e_greedy=setup_greedy):
        self.check_state_exist(observation)
        if np.random.uniform() < e_greedy:
            # if global_log_action:
            #     fh_decisions.write("<=>")
            state_action = self.q_table.loc[observation, :]
            action = np.random.choice(
                state_action[state_action == np.max(state_action)].index)
        else:
            action = np.random.choice(self.actions)
            # if global_log_action:
            #     fh_decisions.write("<~>")
        return action

    def learn(self, s, a, r, s_):
        self.check_state_exist(s_)
        q_predict = self.q_table.loc[s, a]

        #fh_Q.write(str(self.q_table)); fh_Q.write("\r\n")
        #print("R = %i" % r)

        if s_ != 'terminal':
            q_target = r + self.reward_decay * self.q_table.loc[s_, :].max()
        else:
            q_target = r
        self.q_table.loc[s, a] += self.learning_rate * (q_target - q_predict)

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            self.q_table = self.q_table.append(pd.Series([0] * len(self.actions),
                                                         index=self.q_table.columns,
                                                         name=state))

########################################################################################################################

class L1Agent:

    # ToDo: these params should be passed from sub-class
    #hjaction_list = ("do_nothing","do_nothing")
    agent_name = "L1"
    DQN_filename = None
    fh_decisions = None
    fh_state_csv = None


    def __init__(self):
        self.qtable = QLearningTable(self.action_list)
        self.new_game()

    def reset(self):
        self.new_game()

    def new_game(self):
        self.base_top_left = None
        self.previous_state = None
        self.previous_action = None

    def save_DQN(self):
        logger.info('Record current learnings (%s): %s' % (self.agent_name, self.DQN_filename))
        self.qtable.q_table.to_pickle(self.DQN_filename, 'gzip')

    def load_DQN(self):
        if os.path.isfile(DQN_econ):
            logger.info('Load previous learnings (%s)' % self.agent_name)
            self.qtable.q_table = pd.read_pickle(self.DQN_filename, compression='gzip')
        else:
            logger.info('NO previous learnings located (%s)' % self.agent_name)

    def log_decisions(self, s_message, should_print=True):
        if should_print and self.fh_decisions is not None:
            self.fh_decisions.write(s_message)

    def log_state(self, s_message, should_print=True):
        if should_print and self.fh_state_csv is not None:
            self.fh_state_csv.write(s_message)


    def get_my_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.raw_units
                if unit.unit_type == unit_type
                and unit.alliance == features.PlayerRelative.SELF]


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

        ## print("step at L1 (%s)" % self.agent_name)

        command_centres = self.get_my_units_by_type(obs, units.Terran.CommandCenter)
        enemy_bases = self.get_enemy_completed_units_by_type(obs, units.Terran.CommandCenter)

        if len(enemy_bases) > 0 and False:
            fh_action_logic.write("MyBase (x,y) = %i,%i \n\r" % (command_center.x, command_center.y))
            fh_action_logic.write("Enemy base = %i,%i\n\r" % (enemy_bases[0].x, enemy_bases[0].y))

        if obs.first():
            self.base_top_left = (command_centres[0].x < 32)

        self.log_decisions("\r\nstep,agent=%s" % self.agent_name)

        state = str(self.get_state(obs))

        # Original 'best known' action based on Q-Table
        action = self.qtable.choose_action(state)
        self.log_decisions(",Q-Action=%s" % action)


        while not(getattr(self, action)(obs, check_action_availability_only=True)):
            # previous action was not feasible, choose the alternative action randomly
            action = np.random.choice(self.action_list)


        #self.log_decisions(" Resulting action=%s," % action)
        if self.previous_action is not None:
            self.qtable.learn(self.previous_state,
                              self.previous_action,
                              1 if obs.last() and obs.reward == 0 else obs.reward,
                              'terminal' if obs.last() else state)

        self.previous_state = state
        self.previous_action = action

        ## print("step(%s) ~> %s()" % (self.agent_name, action))
        action_res = getattr(self, action)(obs, check_action_availability_only=False)
        ## print("CP7")
        return action_res


    def do_nothing(self, obs, check_action_availability_only):
        ## print(" do_nothing(%i)" % check_action_availability_only)
        if check_action_availability_only:
            return True
        actions.RAW_FUNCTIONS.no_op()


    def econ_do_nothing(self, obs, check_action_availability_only):
        ## print("  econ_nothing(%i)" % check_action_availability_only)
        log_info = not check_action_availability_only
        if check_action_availability_only:
            return True
        self.log_decisions("noop,OK", log_info)
        return None
        #return actions.RAW_FUNCTIONS.no_op()

    def war_do_nothing(self, obs, check_action_availability_only):
        ## print(" war_nothing(%i)" % check_action_availability_only)
        log_info = not (check_action_availability_only)
        if check_action_availability_only:
            return True
        self.log_decisions("noop,OK", log_info)
        return None
        #return actions.RAW_FUNCTIONS.no_op()

    def econ_harvest_minerals(self, obs, check_action_availability_only):
        ## print(" econ_harvest_minerals(%i)" % check_action_availability_only)
        log_info = not (check_action_availability_only)
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        idle_scvs = [scv for scv in scvs if scv.order_length == 0]
        self.log_decisions("idle_scvs=%i" % len(idle_scvs), log_info)
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
            self.log_decisions(",OK", log_info)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Harvest_Gather_unit(
                "now", scv.tag, mineral_patch.tag)
        self.log_decisions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()


    def econ_build_supply_depot(self, obs, check_action_availability_only):
        ## print(" econ_build_supply_depot(%i)" % check_action_availability_only)
        log_info = not (check_action_availability_only)
        supply_depots = self.get_my_units_by_type(obs, units.Terran.SupplyDepot)
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        self.log_decisions("supply_depots=%i minerals=%i scvs=%i" % (
                len(supply_depots),
                obs.observation.player.minerals,
                len(scvs)), log_info)
        if (len(supply_depots) < 4 and obs.observation.player.minerals >= 100 and
                len(scvs) > 0):
            #supply_depot_xy = (22, 26) if self.base_top_left else (35, 42)
            if len(supply_depots) == 0:
                supply_depot_xy = (20 + 1, 27 + 3) if self.base_top_left else (69 - 3, 77 - 3) # 96 res
            elif len(supply_depots) == 1:
                supply_depot_xy = (20 + 3, 27 + 3) if self.base_top_left else (69 - 5, 77 - 3)  # 96 res
            elif len(supply_depots) == 2:
                supply_depot_xy = (20 - 3, 27 + 5) if self.base_top_left else (69 - 5, 77 - 5)  # 96 res
            else:
                supply_depot_xy = (20 - 3, 27 + 7) if self.base_top_left else (69 - 5, 77 - 7)  # 96 res
            distances = self.get_distances(obs, scvs, supply_depot_xy)
            scv = scvs[np.argmax(distances)]
            self.log_decisions(",OK", log_info)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Build_SupplyDepot_pt(
                "now", scv.tag, supply_depot_xy)
        self.log_decisions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()


    def econ_build_barracks(self, obs, check_action_availability_only):
        ## print(" econ_build_barracks(%i)" % check_action_availability_only)
        log_info = not (check_action_availability_only)
        completed_supply_depots = self.get_my_completed_units_by_type(
            obs, units.Terran.SupplyDepot)
        barrackses = self.get_my_units_by_type(obs, units.Terran.Barracks)
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        self.log_decisions("completed_supply_depots=%i barracks=%i minerals=%i scvs=%i" % (
                len(completed_supply_depots),
                len(barrackses),
                obs.observation.player.minerals,
                len(scvs)), log_info)
        if (len(completed_supply_depots) > 0 and len(barrackses) < 5 and
                obs.observation.player.minerals >= 150 and len(scvs) > 0):

            if len(barrackses) == 0:
                # Place for the 1st barrack
                #barracks_xy = (22, 21) if self.base_top_left else (35, 45)
                barracks_xy = (20 + 7, 27 + 0) if self.base_top_left else (69 - 7, 77 - 0)  # 96 res
            elif len(barrackses) == 1:
                # Place for the 2nd barrack
                #barracks_xy = (22 + 2, 21 + 2) if self.base_top_left else (35 - 2, 45 - 2)
                barracks_xy = (20 + 9, 27 + 4) if self.base_top_left else (69 - 9, 77 - 2)  # 96 res
            elif len(barrackses) == 2:
                # Place for the 3rd barrack
                #barracks_xy = (22 + 4, 21 + 4) if self.base_top_left else (35 - 4, 45 - 4)
                barracks_xy = (20 + 7, 27 + 4) if self.base_top_left else (69 - 11, 77 - 4)  # 96 res
            elif len(barrackses) == 3:
                # Place for the 4th barrack
                barracks_xy = (20 + 9, 27 + 0) if self.base_top_left else (69 - 13, 77 - 2)  # 96 res
            else:
                # Place for the last barrack
                #barracks_xy = (22 + 6, 21 + 6) if self.base_top_left else (35 - 6, 45 - 2)
                barracks_xy = (20 + 1, 27 + 6) if self.base_top_left else (69 - 7, 77 - 6)  # 96 res
            distances = self.get_distances(obs, scvs, barracks_xy)
            #scv = scvs[np.argmin(distances)]
            scv = scvs[np.argmax(distances)]
            self.log_decisions(",OK", log_info)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Build_Barracks_pt(
                "now", scv.tag, barracks_xy)
        self.log_decisions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()


    def econ_train_marine(self, obs, check_action_availability_only):
        log_info = not (check_action_availability_only)
        completed_barrackses = self.get_my_completed_units_by_type(
            obs, units.Terran.Barracks)
        free_supply = (obs.observation.player.food_cap -
                       obs.observation.player.food_used)
        self.log_decisions("completed_barrackses=%i free_supply=%i minerals=%i" % (
            len(completed_barrackses),
            free_supply,
            obs.observation.player.minerals), log_info)

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


            self.log_decisions("(best) barracks.order_length=%i" % best_barrack.order_length, log_info)
            if best_barrack.order_length < 5:
                self.log_decisions(",OK", log_info)
                if check_action_availability_only:
                    return True
                return actions.RAW_FUNCTIONS.Train_Marine_quick("now", best_barrack.tag)
        self.log_decisions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()


    def war_attack(self, obs, check_action_availability_only):
        log_info = not (check_action_availability_only)
        marines = self.get_my_units_by_type(obs, units.Terran.Marine)
        self.log_decisions("marines=%i" % len(marines), log_info)
        if len(marines) > 0:
            attack_xy = (38, 44) if self.base_top_left else (19, 23)

            if True:
                # ToDo: record my Base (x,y) at the start of the game
                my_base_xy = (19, 23) if self.base_top_left else (38, 44)

                enemy_marines = self.get_enemy_units_by_type(obs, units.Terran.Marine)
                enemy_scvs = self.get_enemy_units_by_type(obs, units.Terran.SCV)
                enemy_base = self.get_enemy_completed_units_by_type(obs,units.Terran.CommandCenter)

                attack_target = None
                selected_target = "N/A"

                if len(enemy_base) > 0:
                    attack_target = enemy_base[np.argmin(self.get_distances(obs, enemy_base, my_base_xy))]
                    selected_target = "Base"
                elif len(enemy_scvs) > 0:
                    attack_target = enemy_scvs[np.argmin(self.get_distances(obs, enemy_scvs, my_base_xy))]
                    selected_target = "SCV"
                elif len(enemy_marines) > 0:
                    attack_target = enemy_marines[np.argmin (self.get_distances(obs, enemy_marines, my_base_xy))]
                    selected_target = "Mariner"

                if attack_target is not None:
                    attack_xy = (attack_target.x, attack_target.y)
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
            self.log_decisions(" target='%s',OK" % selected_target, log_info)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Attack_pt(
                "now", marine_army, (attack_xy[0] + x_offset, attack_xy[1] + y_offset))
                #"now", marine.tag, (attack_xy[0] + x_offset, attack_xy[1] + y_offset))

        self.log_decisions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()


########################################################################################################################


class L2AgentBob(L1Agent):
    action_list = (
        "econ_do_nothing",
        "econ_harvest_minerals",
        "econ_build_supply_depot",
        "econ_build_barracks",
        "econ_train_marine"
    )

    agent_name = "Bob"
    DQN_filename = DQN_econ
    fh_decisions = fh_econ_decisions
    fh_state_csv = fh_econ_state_csv



    def __init__(self):
        super(L2AgentBob, self).__init__()

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

        enemy_scvs = self.get_enemy_units_by_type(obs, units.Terran.SCV)
        enemy_command_centers = self.get_enemy_units_by_type(obs, units.Terran.CommandCenter)
        enemy_supply_depots = self.get_enemy_units_by_type(obs, units.Terran.SupplyDepot)
        enemy_barrackses = self.get_enemy_units_by_type(obs, units.Terran.Barracks)
        enemy_factories = self.get_enemy_units_by_type(obs, units.Terran.Factory)
        enemy_starport = self.get_enemy_units_by_type(obs, units.Terran.Starport)

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


########################################################################################################################


class L2AgentPeps(L1Agent):

    action_list = ("war_do_nothing","war_attack")
    # "war_regroup",
    # "war_defend",

    agent_name = "Peps"
    DQN_filename = DQN_war
    fh_decisions = fh_econ_decisions
    fh_state_csv = fh_war_decisions

    def __init__(self):
        super(L2AgentPeps, self).__init__()


    def step(self, obs):
        return super(L2AgentPeps, self).step(obs)


    def get_state(self, obs):
        marines = self.get_my_units_by_type(obs, units.Terran.Marine)

        # enemy_scvs = self.get_enemy_units_by_type(obs, units.Terran.SCV)
        # enemy_command_centers = self.get_enemy_units_by_type(obs, units.Terran.CommandCenter)
        # enemy_supply_depots = self.get_enemy_units_by_type(obs, units.Terran.SupplyDepot)
        enemy_barrackses = self.get_enemy_units_by_type(obs, units.Terran.Barracks)
        enemy_factories = self.get_enemy_units_by_type(obs, units.Terran.Factory)
        enemy_starport = self.get_enemy_units_by_type(obs, units.Terran.Starport)
        enemy_marines = self.get_enemy_units_by_type(obs, units.Terran.Marine)
        enemy_marauders = self.get_enemy_units_by_type(obs, units.Terran.Marauder)
        enemy_Tanks1 = self.get_enemy_units_by_type(obs, units.Terran.SiegeTank)
        enemy_Tanks2 = self.get_enemy_units_by_type(obs, units.Terran.SiegeTankSieged)
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

        return (
                len(marines),
                enemy_army_band
        )


########################################################################################################################


class SmartAgentG2(base_agent.BaseAgent):
    agent_name = "SmartAgent Gen2"
    should_log_actions = True

    AI_Peps = L2AgentPeps()
    AI_Bob = L2AgentBob()

    def __init__(self):
        super(SmartAgentG2, self).__init__()

        self.AI_Bob.new_game()
        self.AI_Peps.new_game()

        self.AI_Bob.load_DQN()
        self.AI_Peps.load_DQN()


    def reset(self):
        super(SmartAgentG2, self).reset()
        self.AI_Bob.reset()
        self.AI_Peps.reset()


    def step(self, obs):
        super(SmartAgentG2, self).step(obs)

        # Econ (AKA 'Bob, the builder') has the precedence over War (AKA Sargent Pepper)
        res = self.AI_Bob.step(obs)
        if res is None:
            res = self.AI_Peps.step(obs)
        if res is None:
            res = actions.RAW_FUNCTIONS.no_op()

        if obs.last():
            self.AI_Bob.save_DQN()
            self.AI_Peps.save_DQN()

        return res


########################################################################################################################


def main(unused_argv):
    agentSmart1 = SmartAgentG2()
    with sc2_env.SC2Env(
            #map_name="Simple64",
            map_name="Simple96",
            #map_name="AbyssalReef",
            #players=[sc2_env.Agent(sc2_env.Race.terran), sc2_env.Agent(sc2_env.Race.terran)],
            players=[sc2_env.Agent(sc2_env.Race.terran), sc2_env.Bot(sc2_env.Race.terran, sc2_env.Difficulty.medium )],
            #players=[sc2_env.Agent(sc2_env.Race.terran), sc2_env.Bot(sc2_env.Race.terran, sc2_env.Difficulty.medium_hard )],
            agent_interface_format=features.AgentInterfaceFormat(
                action_space=actions.ActionSpace.RAW,
                use_raw_units=True,
                #raw_resolution=64,
                raw_resolution=96
            ),
            step_mul=48,
            disable_fog=True,
    ) as env:
        run_loop.run_loop([agentSmart1], env, max_episodes=10000)
        #run_loop.run_loop([agentSmart1, agentRandom], env, max_episodes=1000)
        #run_loop.run_loop([agentSmart1, agentSmart2], env, max_episodes=1000)
    try:
        pass
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app.run(main)