import random
import numpy as np
import pandas as pd
import os
from absl import app
from pysc2.agents import base_agent
from pysc2.lib import actions, features, units
from pysc2.env import sc2_env, run_loop

import logging

DATA_FILE = 'DQNs/v19.gz'


logging.basicConfig(format='%(asctime)-15s %(message)s')
fh = logging.FileHandler('logs/#19.log')
logger = logging.getLogger()
logger.setLevel("INFO")

fh_actions = open('logs/#19_decisions.log', "a+")
fh_obs = open('logs/#19_obs.log', "a+")
fh_action_logic = open('logs/#19_action_insights.log', "a+")

setup_greedy = .9
global_log_action = False

class QLearningTable:
    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9):
        self.actions = actions
        self.learning_rate = learning_rate
        self.reward_decay = reward_decay
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation, e_greedy=setup_greedy):
        self.check_state_exist(observation)
        if np.random.uniform() < e_greedy:
            if global_log_action:
                fh_actions.write("<=>")
            state_action = self.q_table.loc[observation, :]
            action = np.random.choice(
                state_action[state_action == np.max(state_action)].index)
        else:
            action = np.random.choice(self.actions)
            if global_log_action:
                fh_actions.write("<~>")
        return action

    def learn(self, s, a, r, s_):
        self.check_state_exist(s_)
        q_predict = self.q_table.loc[s, a]

        #fh_Q.write(str(self.q_table)); fh_Q.write("\r\n")

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


class Agent(base_agent.BaseAgent):
    actions = ("do_nothing",
               "harvest_minerals",
               "build_supply_depot1",
               "build_supply_depot2",
               "build_barracks",
               "train_marine",
               "attack"
               )

    agent_name = "dummy"
    should_log_actions = False


    def log_actions(self, s_message, should_print=True):
        if self.should_log_actions and should_print and global_log_action:
            fh_actions.write(s_message)

    def init_logging(self, agent_name, should_log_actions):
        self.agent_name = agent_name
        self.should_log_actions = should_log_actions
        self.log_actions("stage,agent,action,input,status")


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
        super(Agent, self).step(obs)
        inp = obs
        if obs.first():
            command_center = self.get_my_units_by_type(
                obs, units.Terran.CommandCenter)[0]
            self.base_top_left = (command_center.x < 32)
        self.log_actions("\r\nstep,agent=%s" % self.agent_name)


    def do_nothing(self, obs, check_action_availability_only):
        log_info = not (check_action_availability_only)
        if check_action_availability_only:
            return True
        self.log_actions("noop,OK", log_info)
        return actions.RAW_FUNCTIONS.no_op()


    def harvest_minerals(self, obs, check_action_availability_only):
        log_info = not (check_action_availability_only)
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        idle_scvs = [scv for scv in scvs if scv.order_length == 0]
        self.log_actions("idle_scvs=%i" % len(idle_scvs), log_info)
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
            distances = self.get_distances(obs, mineral_patches, (scv.x, scv.y))
            mineral_patch = mineral_patches[np.argmin(distances)]
            self.log_actions(",OK", log_info)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Harvest_Gather_unit(
                "now", scv.tag, mineral_patch.tag)
        self.log_actions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()


    def build_supply_depot1(self, obs, check_action_availability_only):
        log_info = not (check_action_availability_only)
        supply_depots = self.get_my_units_by_type(obs, units.Terran.SupplyDepot)
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        self.log_actions("supply_depots=%i minerals=%i scvs=%i" % (
                len(supply_depots),
                obs.observation.player.minerals,
                len(scvs)), log_info)
        if (len(supply_depots) == 0 and obs.observation.player.minerals >= 100 and
                len(scvs) > 0):
            supply_depot_xy = (22, 26) if self.base_top_left else (35, 42)
            distances = self.get_distances(obs, scvs, supply_depot_xy)
            scv = scvs[np.argmin(distances)]
            self.log_actions(",OK", log_info)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Build_SupplyDepot_pt(
                "now", scv.tag, supply_depot_xy)
        self.log_actions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()


    def build_supply_depot2(self, obs, check_action_availability_only):
        log_info = not (check_action_availability_only)
        supply_depots = self.get_my_units_by_type(obs, units.Terran.SupplyDepot)
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        self.log_actions("supply_depots=%i minerals=%i scvs=%i" % (
                len(supply_depots),
                obs.observation.player.minerals,
                len(scvs)), log_info)
        if (len(supply_depots) == 1 and obs.observation.player.minerals >= 100 and
                len(scvs) > 0):
            supply_depot_xy = (22-3, 26+3) if self.base_top_left else (35+3, 42-3)
            distances = self.get_distances(obs, scvs, supply_depot_xy)
            scv = scvs[np.argmax(distances)]
            self.log_actions(",OK", log_info)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Build_SupplyDepot_pt(
                "now", scv.tag, supply_depot_xy)
        self.log_actions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()


    def build_barracks(self, obs, check_action_availability_only):
        log_info = not (check_action_availability_only)
        completed_supply_depots = self.get_my_completed_units_by_type(
            obs, units.Terran.SupplyDepot)
        barrackses = self.get_my_units_by_type(obs, units.Terran.Barracks)
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        self.log_actions("completed_supply_depots=%i barracks=%i minerals=%i scvs=%i" % (
                len(completed_supply_depots),
                len(barrackses),
                obs.observation.player.minerals,
                len(scvs)), log_info)
        if (len(completed_supply_depots) > 0 and len(barrackses) < 4 and
                obs.observation.player.minerals >= 150 and len(scvs) > 0):

            if len(barrackses) == 0:
                # Place for the 1st barrack
                barracks_xy = (22, 21) if self.base_top_left else (35, 45)
            elif len(barrackses)==1:
                # Place for the 2nd barrack
                barracks_xy = (22 + 2, 21 + 2) if self.base_top_left else (35 - 2, 45 - 2)
            elif len(barrackses) == 2:
                # Place for the 3rd barrack
                barracks_xy = (22 + 4, 21 + 4) if self.base_top_left else (35 - 4, 45 - 4)
            else:
                # Place for the last barrack
                barracks_xy = (22 + 6, 21 + 6) if self.base_top_left else (35 - 6, 45 - 2)
            distances = self.get_distances(obs, scvs, barracks_xy)
            #scv = scvs[np.argmin(distances)]
            scv = scvs[np.argmax(distances)]
            self.log_actions(",OK", log_info)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Build_Barracks_pt(
                "now", scv.tag, barracks_xy)
        self.log_actions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()


    def train_marine(self, obs, check_action_availability_only):
        log_info = not (check_action_availability_only)
        completed_barrackses = self.get_my_completed_units_by_type(
            obs, units.Terran.Barracks)
        free_supply = (obs.observation.player.food_cap -
                       obs.observation.player.food_used)
        self.log_actions("completed_barrackses=%i free_supply=%i minerals=%i" % (
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

            fh_action_logic.write("\r\n------- train_marine --------\r\n")
            fh_action_logic.write("Number of ready barracks: %i\r\n" % len(completed_barrackses))
            fh_action_logic.write("Load length: %s\r\n" % str(all_order_length))
            fh_action_logic.write("Chosen barrack with length: %i\r\n" % best_barrack.order_length)


            self.log_actions("(best) barracks.order_length=%i" % best_barrack.order_length, log_info)
            if best_barrack.order_length < 5:
                self.log_actions(",OK", log_info)
                if check_action_availability_only:
                    return True
                return actions.RAW_FUNCTIONS.Train_Marine_quick("now", best_barrack.tag)
        self.log_actions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()


    def attack(self, obs, check_action_availability_only):
        log_info = not (check_action_availability_only)
        marines = self.get_my_units_by_type(obs, units.Terran.Marine)
        self.log_actions("marines=%i" % len(marines), log_info)
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
            fh_action_logic.write("\r\n------- Attack ------------------\r\nNumber of marines: %i\r\n" % len(marines))
            fh_action_logic.write("Closest mariner: %i\r\n" % marine.tag)

            # Create an ampty list for army
            marine_army = []
            for marine in marines:
                marine_army.append(marine.tag)

            fh_action_logic.write("Army composition: %s\r\n" % str(marine_army))

            x_offset = random.randint(-4, 4)
            y_offset = random.randint(-4, 4)
            self.log_actions(" target='%s',OK" % selected_target, log_info)
            if check_action_availability_only:
                return True
            return actions.RAW_FUNCTIONS.Attack_pt(
                "now", marine_army, (attack_xy[0] + x_offset, attack_xy[1] + y_offset))
                #"now", marine.tag, (attack_xy[0] + x_offset, attack_xy[1] + y_offset))

        self.log_actions(",FAIL", log_info)
        if check_action_availability_only:
            return False
        return actions.RAW_FUNCTIONS.no_op()



class RandomAgent(Agent):
    agent_name = "RandomAgent"
    should_log_actions = False

    def __init__(self):
        super(RandomAgent, self).__init__()
        super(RandomAgent, self).init_logging(self.agent_name, self.should_log_actions)

    def step(self, obs):
        super(RandomAgent, self).step(obs)
        action = random.choice(self.actions)
        return getattr(self, action)(obs)


class SmartAgent(Agent):
    agent_name = "SmartAgent"
    should_log_actions = True

    def __init__(self):
        super(SmartAgent, self).__init__()
        super(SmartAgent, self).init_logging(self.agent_name, self.should_log_actions)
        self.qtable = QLearningTable(self.actions)
        self.new_game()
        if os.path.isfile(DATA_FILE):
            logger.info('Load previous learnings')
            self.qtable.q_table = pd.read_pickle(DATA_FILE, compression='gzip')
        else:
            logger.info('NO previous learnings located')

    def reset(self):
        super(SmartAgent, self).reset()
        self.new_game()

    def new_game(self):
        self.base_top_left = None
        self.previous_state = None
        self.previous_action = None

    def get_state(self, obs):
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

        enemy_army_band = None
        if enemy_army < 10:
            enemy_army_band = enemy_army
        elif enemy_army < 30:
            enemy_army_band = int((enemy_army - 10) / 3) * 3 + 10
        else:
            enemy_army_band = int((enemy_army - 30) / 5) * 5 + 30

        # self.log_actions(
        #     ",$=%s can_afford_supply_depot=%s can_afford_barracks=%s can_afford_marine=%s" %
        #     (obs.observation.player.minerals, can_afford_supply_depot, can_afford_barracks, can_afford_marine))

        state_dict = {
            "command_centers": len(command_centers),
            "scvs": len(scvs),
            "idle_scvs": len(idle_scvs),
            "supply_depots": len(supply_depots),
            "completed_supply_depots": len(completed_supply_depots),
            "barrackses": len(barrackses),
            "completed_barrackses": len(completed_barrackses),
            "marines": len(marines),
            "queued_marines": queued_marines,
            "free_supply": free_supply,
            "can_afford_supply_depot": can_afford_supply_depot,
            "can_afford_barracks": can_afford_barracks,
            "can_afford_marine": can_afford_marine,
            "enemy_command_centers": len(enemy_command_centers),
            "enemy_scvs": len(enemy_scvs),
            "enemy_supply_depots": len(enemy_supply_depots),
            "enemy_barrackses": len(enemy_barrackses),
            "enemy_factories ": len(enemy_factories),
            "enemy_starport ": len(enemy_starport),
            "enemy_marines": len(enemy_marines),
            "enemy_marauders": len(enemy_marauders),
            "enemy_Tanks1": len(enemy_Tanks1),
            "enemy_Tanks2": len(enemy_Tanks2),
            "enemy_Hells": len(enemy_Hells),
            "enemy_army": enemy_army,
            "enemy_army_band": enemy_army_band,
            "res":obs.observation.player.minerals
        }

        self.log_actions(",get_state:")
        for k, v in state_dict.items():
            self.log_actions(" %s=%s" % (k, v))

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
                can_afford_marine,
                len(enemy_command_centers),
                len(enemy_scvs),
                len(enemy_supply_depots),
                len(enemy_barrackses),
                len(enemy_marines),
                len(enemy_factories),
                len(enemy_starport),
                enemy_army_band)


    def step(self, obs):
        super(SmartAgent, self).step(obs)
        state = str(self.get_state(obs))

        #fh_obs.write(str(obs))
        #fh_obs.write("\r\n")

        # Original 'best known' action based on Q-Table
        action = self.qtable.choose_action(state)
        self.log_actions(",Q-Action=%s" % action)

        while not(getattr(self, action)(obs, check_action_availability_only=True)):
            # previous action was not feasible, choose the alternative action randomly
            action = np.random.choice(self.actions)

        self.log_actions(" Resulting action=%s," % action)
        #if self.should_log_actions: fh_actions.write("\r\nstep,agent=%s,action=%s," % (self.agent_name, action))
        if self.previous_action is not None:
            self.qtable.learn(self.previous_state,
                              self.previous_action,
                              obs.reward,
                              'terminal' if obs.last() else state)

        # Record current learnings
        if obs.last():
            logger.info('Record current learnings')
            self.qtable.q_table.to_pickle(DATA_FILE, 'gzip')

        self.previous_state = state
        self.previous_action = action

        action_res = getattr(self, action)(obs, check_action_availability_only=False)
        if obs.last():
            self.log_actions("\r\nlast.obs,NA,NA,NA,NA")
            #self.log_actions("stage,agent,action,input,status")
        return action_res


def main(unused_argv):
    agentSmart1 = SmartAgent()
    agentSmart2 = SmartAgent()
    #agentRandom = RandomAgent()
    try:
        with sc2_env.SC2Env(
                map_name="Simple64",
                #players=[sc2_env.Agent(sc2_env.Race.terran), sc2_env.Agent(sc2_env.Race.terran)],
                players=[sc2_env.Agent(sc2_env.Race.terran), sc2_env.Bot(sc2_env.Race.terran, sc2_env.Difficulty.medium_hard )],
                agent_interface_format=features.AgentInterfaceFormat(
                    action_space=actions.ActionSpace.RAW,
                    use_raw_units=True,
                    raw_resolution=64,
                ),
                step_mul=48,
                disable_fog=True,
        ) as env:
            run_loop.run_loop([agentSmart1], env, max_episodes=10000)
            #run_loop.run_loop([agentSmart1, agentSmart2], env, max_episodes=1000)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app.run(main)