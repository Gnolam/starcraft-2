from pysc2.agents import base_agent
from pysc2.lib import actions, features
import logging

from l2_econ import L2AgentBob
from l2_war_sgt import L2AgentPeps
from l2_war_gen import L2AgentGrievous

class SmartAgentG2(base_agent.BaseAgent):
    agent_name = "SmartAgent Gen2"
    should_log_actions = True

    def __init__(self, cfg):
        super(SmartAgentG2, self).__init__()
        logging.getLogger("main").info("SmartAgentG2 created")

        self.AI_Bob = L2AgentBob(cfg)
        self.AI_Peps = L2AgentPeps(cfg)
        self.AI_Grievous = L2AgentGrievous(cfg)
        
        self.AI_Grievous.assgin_sergant(self.AI_Peps)

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
            self.AI_Bob.save_global_state()

        self.AI_Grievous.debug(obs)

        return res