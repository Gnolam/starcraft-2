import logging
import logging.config
import yaml
import os
from pysc2.env import sc2_env, run_loop
from pysc2.lib import actions, features
from absl import app
from lib.config import Config
from lib.agentG3 import SmartAgentG3
from lib.G3.pipeline import Pipeline
from lib.G3.pipeline_orders import poTrainMarine, poBuildBarracks
from lib.ticket_status import TicketStatus


def main(unused_argv):
    cfg = Config()
    cfg.fix_ADSL_logging()
    cfg.init_project('config/agents.yml')
    cfg.init_logging('config/logging.yml')

    logging.getLogger("main").info("main() called")
    agentSmart1 = SmartAgentG3(cfg)

    with sc2_env.SC2Env(
            # map_name="Simple64",
            map_name="Simple96",
            # map_name="AbyssalReef",
            # players=[sc2_env.Agent(sc2_env.Race.terran),
            #   sc2_env.Agent(sc2_env.Race.terran)],
            players=[
                sc2_env.Agent(sc2_env.Race.terran),
                sc2_env.Bot(sc2_env.Race.terran, sc2_env.Difficulty.hard)
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
        run_loop.run_loop([agentSmart1], env, max_episodes=10000)
        # run_loop.run_loop([agentSmart1, agentRandom], env, max_episodes=10000)
        # run_loop.run_loop([agentSmart1, agentSmart2], env, max_episodes=1000)
    try:
        pass
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app.run(main)

if False:
    cfg = Config()
    cfg.fix_ADSL_logging()
    cfg.init_logging('config/logging.yml')

    a = Pipeline()
    order_ID = a.add_order(poTrainMarine(number_of_mariners_to_build=4))
    print(f"new order ID: {order_ID}")

    a.book[0].run("")
    print(a)
    a.book[1].resign_as_blocker()
    print(a)
    a.book[2].resign_as_blocker()
    print(a)

    print([(ticket.ID, ticket.str_status()) for ticket in a.book])

    print([(ticket.ID, ticket.str_status()) for ticket in a.book
           if ticket.get_status() == TicketStatus.ACTIVE])

    a.run()

    # c = poBuildMariners(number_of_mariners_to_build=4)
    # c.run()
