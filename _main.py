import logging
import logging.config, yaml, os
from pysc2.env import sc2_env, run_loop
from pysc2.lib import actions, features
from absl import app
from lib.config import Config
from SmartAgentG2 import SmartAgentG2

def main(unused_argv):
    cfg = Config()
    cfg.fix_ADSL_logging()    
    cfg.init_project('config/agents.yml')
    cfg.init_logging('config/logging.yml')    
    
    logging.getLogger("main").info("main() called")
    agentSmart1 = SmartAgentG2(cfg)   

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

if __name__ == "__main__":
    app.run(main)
