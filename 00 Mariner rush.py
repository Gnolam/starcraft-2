import random
import numpy as np
import pandas as pd
from absl import app
from pysc2.agents import base_agent
from pysc2.lib import actions, features, units
from pysc2.env import sc2_env, run_loop

from agents.l1_class import L1Agent

import logging

run_id = 'v23a_consistent'

########################################################################################################################


DQN_econ = 'DQNs/%s_econ.gz' % run_id
DQN_war = 'DQNs/%s_war.gz' % run_id

logging.basicConfig(format='%(asctime)-15s %(message)s')
fh = logging.FileHandler('logs/%s.log' % run_id)
logger = logging.getLogger()
logger.setLevel("INFO")

fh_decisions = open('logs/%s_decisions.log' % run_id, "a+")
fh_obs = open('logs/%s_obs.log' % run_id, "a+")

fh_econ_state_csv = None
fh_econ_decisions = None

fh_war_state_csv = None
fh_war_decisions = open('logs/%s_war_decisions.log' % run_id, "a+")

global_debug = False

fh_global_debug = open('logs/%s_global.log' % run_id, "a+")

# global_log_action = True
# global_log_action_logic = False

consistent_econ = False
consistent_war = False


########################################################################################################################



########################################################################################################################




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
    consistent_decision_agent = consistent_econ

    def __init__(self, logger):
        super(L2AgentBob, self).__init__(logger)

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
    action_list = ("war_do_nothing", "war_attack")
    # "war_regroup",
    # "war_defend",

    agent_name = "Peps"
    DQN_filename = DQN_war
    fh_decisions = fh_econ_decisions
    fh_state_csv = fh_war_decisions
    consistent_decision_agent = consistent_war

    def __init__(self, logger):
        super(L2AgentPeps, self).__init__(logger)

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

    AI_Peps = L2AgentPeps(logger)
    AI_Bob = L2AgentBob(logger)

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
            # Potentially analyze the situation, while the system is 'idle'
            res = actions.RAW_FUNCTIONS.no_op()

        if obs.last():
            self.AI_Bob.save_DQN()
            self.AI_Peps.save_DQN()

        return res


########################################################################################################################


def main(unused_argv):
    agentSmart1 = SmartAgentG2()
    with sc2_env.SC2Env(
            # map_name="Simple64",
            map_name="Simple96",
            # map_name="AbyssalReef",
            # players=[sc2_env.Agent(sc2_env.Race.terran), sc2_env.Agent(sc2_env.Race.terran)],
            players=[sc2_env.Agent(sc2_env.Race.terran), sc2_env.Bot(sc2_env.Race.terran, sc2_env.Difficulty.medium)],
            # players=[sc2_env.Agent(sc2_env.Race.terran), sc2_env.Bot(sc2_env.Race.terran, sc2_env.Difficulty.medium_hard )],
            agent_interface_format=features.AgentInterfaceFormat(
                action_space=actions.ActionSpace.RAW,
                use_raw_units=True,
                # raw_resolution=64,
                raw_resolution=96
            ),
            step_mul=48,
            disable_fog=True,
    ) as env:
        run_loop.run_loop([agentSmart1], env, max_episodes=10000)
        # run_loop.run_loop([agentSmart1, agentRandom], env, max_episodes=1000)
        # run_loop.run_loop([agentSmart1, agentSmart2], env, max_episodes=1000)
    try:
        pass
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app.run(main)
