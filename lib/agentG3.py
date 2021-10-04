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

        # Econ (AKA 'Bob, the builder') has the precedence over War (AKA Sargent Pepper)
        res, builder_got_new_orders = self.aiBob.step(obs)

        # General does not take actions,
        # just decides on reserve -> task force reallocation
        if builder_got_new_orders:
            _, _ = self.aiGen.step(obs)

        if res is None:
            if self.aiGen.peps is None:
                logging.getLogger("main").warn(
                    "Sgt object 'peps' is not defined")
                res = actions.RAW_FUNCTIONS.no_op()
            else:
                res = self.aiGen.peps.war_attack(obs)

        if obs.last():
            self.aiBob.finalise_game()
            self.aiGen.finalise_game()
            # self.agent_Peps.finalise_game()
            # ToDo: ??? describe this ???
            # ToDo: should be the function of the config object
            self.aiBob.save_global_state()

        return res
