from pysc2.agents import base_agent
from pysc2.lib import actions, features
import logging

from lib.G3ai.ai_general import aiGeneral
from lib.G3ai.ai_builder import aiBuilder

# from lib.E2_agent import AgentBob
# from lib.l2_war_sgt import L2AgentPeps
# from lib.l2_war_gen import L2AgentGrievous


class SmartAgentG3(base_agent.BaseAgent):
    agent_name = "SmartAgent Gen3"

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

        # Gen is called for action every time Bob's order is fulfilled
        self.aiBob.link_gen(self.aiGen)

    def reset(self):
        super(SmartAgentG3, self).reset()
        self.aiBob.reset()
        self.aiGen.reset()

    def step(self, obs):
        super(SmartAgentG3, self).step(obs)

        # Econ (AKA 'Bob, the builder') has the precedence over War (AKA Sargent Pepper)
        res = self.aiBob.step(obs)
        if res is None or obs.last():  # obs.last() is a time for learning!!!
            pass
            # ToDo: this is the placeholder for Sgt logic
            # self.aiGen.step(obs)
            #     obs)  # General is kind of always ready to give orders
            # if self.agent_Peps.war_attack(obs,
            #                               check_action_availability_only=True):
            #     # Sgt should always attack if he has TF1
            #     res = self.agent_Peps.war_attack(
            #         obs, check_action_availability_only=False)

        # .war_attack() results into no_op() itself but just in case...
        if res is None:
            # Potentially analyze the situation, while the system is 'idle'
            res = actions.RAW_FUNCTIONS.no_op()

        if obs.last():
            self.aiBob.finalise_game()
            # self.aiGen.finalise_game()
            # self.agent_Peps.finalise_game()
            self.aiBob.save_global_state()

        # self.AI_Grievous.debug(obs)

        return res
