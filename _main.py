import logging
import logging.config
import h2o
from pysc2.env import sc2_env, run_loop
from pysc2.lib import actions, features
from absl import app
from lib.config import Config
from lib.agentG3 import SmartAgentG3


def main(unused_argv):

    cfg = Config('config.ini')

    logging.getLogger("main").info("main() called")
    my_sc2_agent = SmartAgentG3(cfg)

    with sc2_env.SC2Env(
            # map_name="Simple64",
            map_name="Simple96",
            # map_name="AbyssalReef",
            # players=[sc2_env.Agent(sc2_env.Race.terran),
            #   sc2_env.Agent(sc2_env.Race.terran)],
            players=[
                sc2_env.Agent(sc2_env.Race.terran),
                sc2_env.Bot(sc2_env.Race.terran,
                            sc2_env.Difficulty.medium_hard)
            ],
            # players=[
            #   sc2_env.Agent(sc2_env.Race.terran),
            #   sc2_env.Bot(
            #       sc2_env.Race.terran,
            #       sc2_env.Difficulty.medium_hard )],
            # players=[sc2_env.Agent(sc2_env.Race.terran),
            #   sc2_env.Bot(
            #       sc2_env.Race.terran,
            #       sc2_env.Difficulty.hard )],
            agent_interface_format=features.AgentInterfaceFormat(
                action_space=actions.ActionSpace.RAW,
                use_raw_units=True,
                # raw_resolution=64,
                raw_resolution=96),
            step_mul=48,
            disable_fog=True,
    ) as env:
        run_loop.run_loop([my_sc2_agent], env, max_episodes=1)
        # run_loop.run_loop([agentSmart1, agentRandom], env, max_episodes=10000)
        # run_loop.run_loop([agentSmart1, agentSmart2], env, max_episodes=1000)
    try:
        pass
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app.run(main)
