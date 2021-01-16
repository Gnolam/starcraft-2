'''
 POC stage
 2 TFs:
   - TF1: attack
   - TF2: reserve
 3 states:
 - wait for TF1 to deplete, attack meanwhile
 - wait till TF2 >= 10 mariners
 - (init with: TF2->TF1) 

try again:
states:
- G1: (execute)
  - there are units in TF1
  - continue attack with TF1
- G2: (planning)
  - there are no units in TF1
    - there are >= 10 units in TF2
      - transfer TF2 -> TF1
  - else 'wait'

Gen: contains Peps

'''

import logging
from pysc2.lib import actions, features, units
import numpy as np
import pandas as pd
import random

from l1_class import L1Agent
from l2_war_sgt import L2AgentPeps

class L2AgentGrievous(L1Agent):
    action_list = ("Use4", "Use8", "Use12") # "Add5", "Add8", "Use12"

    agent_name = "grievous"
    sgt = None

    def __init__(self, cfg, sgt):
        self.logger = logging.getLogger(self.agent_name)
        self.logger.info(f"L2AgentGrievous.init({__name__})")
        self.sgt = sgt
        super(L2AgentGrievous, self).__init__(cfg)
