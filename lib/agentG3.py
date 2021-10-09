from pysc2.agents import base_agent
from pysc2.lib import actions
import logging

from lib.G3ai.ai_general import aiGeneral
from lib.G3ai.ai_builder import aiBuilder


class SmartAgentG3(base_agent.BaseAgent):
    agent_name = "Generation 3: learning to wait"

    def __init__(self, cfg):
        super(SmartAgentG3, self).__init__()
        logging.getLogger("main").info(f"'{self.agent_name}' created")

        self.aiBob = aiBuilder(cfg)
        self.aiGen = aiGeneral(cfg)

        # self.AI_Grievous.assgin_sergant(self.agent_Peps)

        self.aiBob.new_game()
        self.aiGen.new_game()

        self.aiBob.load_DQN()
        self.aiGen.load_DQN()

    def reset(self):
        super(SmartAgentG3, self).reset()
        self.aiBob.reset()
        self.aiGen.reset()

    def step(self, obs):
        super(SmartAgentG3, self).step(obs)

        logging.getLogger("dbg").debug("CP01: step()")

        # Econ (AKA 'Bob, the builder') has the precedence over War (AKA Sargent Pepper)
        sc2_order, builder_got_new_orders = self.aiBob.step(obs)

        # General does not take actions,
        # just decides on reserve -> task force reallocation
        if builder_got_new_orders:
            logging.getLogger("dbg").debug(
                f"CP02a: builder got new orders, asking General to make a decision"
            )
            _, _ = self.aiGen.step(obs)
        else:
            logging.getLogger("dbg").debug(
                f"CP02b: builder got NO new orders, no need to disturb the general"
            )

        if sc2_order is None:
            logging.getLogger("dbg").debug(f"CP03: assigned sc2_order is None")
            if self.aiGen.peps is None:
                logging.getLogger("dbg").debug(f"CP04: peps is missing")
                logging.getLogger("main").critical(
                    "Sgt object 'peps' is not defined")
                sc2_order = actions.RAW_FUNCTIONS.no_op()
            else:
                logging.getLogger("dbg").debug(f"CP05: peps is in place")
                sc2_order = self.aiGen.peps.war_attack(obs)

        if obs.last():
            logging.getLogger("dbg").debug(f"CP06: last obs detected")
            self.aiBob.finalise_game(obs.reward)
            self.aiGen.finalise_game(obs.reward)
            # self.agent_Peps.finalise_game()
            # ToDo: ??? describe this ???
            # ToDo: should be the function of the config object
            self.aiBob.save_global_state()

        return sc2_order
