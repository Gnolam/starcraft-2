# System libs
import logging, logging.config, yaml
from pysc2.env import sc2_env, run_loop
from pysc2.lib import actions, features
from pysc2.agents import base_agent
from absl import app
import os

# Custom libs
from src.l2_econ import L2AgentBob
from src.l2_war import L2AgentPeps
from src.config import Config

########################################################################################################################
cfg = Config('config/agents.yml', 'config/logging.yml')

logger=logging.getLogger(__name__)
logger.debug("Logging initiated")

########################################################################################################################

class SmartAgentG2(base_agent.BaseAgent):
    agent_name = "SmartAgent Gen2"
    should_log_actions = True

    # ToDo: init the config object
    #   - pass the results here

    AI_Peps = L2AgentPeps(cfg)
    AI_Bob = L2AgentBob(cfg)

    def __init__(self):
        super(SmartAgentG2, self).__init__()

        print(">> SmartAgentG2 started")
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

        # NOOP is not entering the learning matrix as a result....
        # should be recorded in the decisions log anyways

        # Econ (AKA 'Bob, the builder') has the precedence over War (AKA Sargent Pepper)
        res = self.AI_Bob.step(obs)
        if res is None or obs.last():  # obs.last() is a time for learning!!!
            res = self.AI_Peps.step(obs)
        if res is None:
            # Potentially analyze the situation, while the system is 'idle'
            res = actions.RAW_FUNCTIONS.no_op()

        if obs.last():
            self.AI_Bob.finalise_game()
            self.AI_Peps.finalise_game()

        return res

########################################################################################################################

def main(unused_argv):
    # Define finctional logging
    #   log file handler should be passed via class constructor

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
        run_loop.run_loop([agentSmart1], env, max_episodes=1000)
        # run_loop.run_loop([agentSmart1, agentRandom], env, max_episodes=1000)
        # run_loop.run_loop([agentSmart1, agentSmart2], env, max_episodes=1000)
    try:
        pass
    except KeyboardInterrupt:
        pass

#if __name__ == "__main__":
#    app.run(main)
agentSmart1 = SmartAgentG2()
# %%
# data["run_id"]

# %%


