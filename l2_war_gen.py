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

    action = None
    agent_name = "grievous"
    sgt = None

    def __init__(self, cfg, sgt):
        self.logger = logging.getLogger(self.agent_name)
        self.logger.info(f"L2AgentGrievous.init({__name__})")
        self.sgt = sgt
        super(L2AgentGrievous, self).__init__(cfg)

    def debug(self, obs):
        self.logger.debug("state: "+ str(self.get_state(obs, return_dict = True)))

    def step(self, obs):
        return super(L2AgentGrievous, self).step(obs)

    def get_state(self, obs, return_dict = True):
        count_marines = len(self.get_my_units_by_type(obs, units.Terran.Marine))

        # enemy_scvs = self.get_enemy_units_by_type(obs, units.Terran.SCV)
        # enemy_command_centers = self.get_enemy_units_by_type(obs, units.Terran.CommandCenter)
        # enemy_supply_depots = self.get_enemy_units_by_type(obs, units.Terran.SupplyDepot)
        count_enemy_barrackses = len(self.get_enemy_units_by_type(obs, units.Terran.Barracks))
        count_enemy_factories = len(self.get_enemy_units_by_type(obs, units.Terran.Factory))
        count_enemy_starport = len(self.get_enemy_units_by_type(obs, units.Terran.Starport))
        count_enemy_marines = len(self.get_enemy_units_by_type(obs, units.Terran.Marine))
        count_enemy_marauders = len(self.get_enemy_units_by_type(obs, units.Terran.Marauder))
        count_enemy_tanks = \
          len(self.get_enemy_units_by_type(obs, units.Terran.SiegeTank)) +\
          len(self.get_enemy_units_by_type(obs, units.Terran.SiegeTankSieged))
        count_enemy_hells = len(self.get_enemy_units_by_type(obs, units.Terran.Hellion))

        enemy_marines_band = 0 if count_enemy_marines ==0 else (int(count_enemy_marines/3)+1)*3
        enemy_marauders_band = 0 if count_enemy_marauders ==0 else (int(count_enemy_marauders/2)+1)*2

        if return_dict:
          return (
            count_marines, # TF1/reserve
            enemy_marines_band,
            enemy_marauders_band,
            count_enemy_barrackses,
            count_enemy_factories,
            count_enemy_starport,
            count_enemy_tanks,
            count_enemy_hells            
          )
        else:
          return ( # TF1/reserve
            f"our marines:{count_marines}, enemy marines:~{enemy_marines_band}, marauders:~{enemy_marauders_band}, tanks:{count_enemy_tanks} " +\
            f"hells:{count_enemy_hells} barrackses:{count_enemy_barrackses} " +\
            f"factories:{count_enemy_factories}, factories:{count_enemy_factories}, starport:{count_enemy_starport}" 
          )
