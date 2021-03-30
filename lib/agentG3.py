from pysc2.agents import base_agent
from pysc2.lib import actions, features
import logging

# from lib.E2_agent import AgentBob
# from lib.l2_war_sgt import L2AgentPeps
# from lib.l2_war_gen import L2AgentGrievous

from lib.G3ai.ai_builder import aiBuilder


class SmartAgentG3(base_agent.BaseAgent):
    agent_name = "SmartAgent Gen3"

    def __init__(self, cfg):
        super(SmartAgentG3, self).__init__()
        logging.getLogger("main").info(f"'{self.agent_name}' created")

        self.aiBob = aiBuilder(cfg)
        # self.agent_Peps = L2AgentPeps(cfg)
        # self.AI_Grievous = L2AgentGrievous(cfg)

        # self.AI_Grievous.assgin_sergant(self.agent_Peps)

        self.aiBob.new_game()
        # self.AI_Grievous.new_game()
        # self.agent_Peps.new_game()

        self.aiBob.load_DQN()
        # self.AI_Grievous.load_DQN()

    def reset(self):
        super(SmartAgentG3, self).reset()
        self.aiBob.reset()
        # self.AI_Grievous.reset()
        # self.agent_Peps.reset()

    def step(self, obs):
        super(SmartAgentG3, self).step(obs)

        # NOOP is not entering the learning matrix as a result....
        # should be recorded in the decisions log anyways

        # Econ (AKA 'Bob, the builder') has the precedence over War (AKA Sargent Pepper)
        res = self.aiBob.step(obs)
        if res is None or obs.last():  # obs.last() is a time for learning!!!
            pass
            # self.AI_Grievous.step(
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
            # self.AI_Grievous.finalise_game()
            # self.agent_Peps.finalise_game()
            self.aiBob.save_global_state()

        # self.AI_Grievous.debug(obs)

        return res
