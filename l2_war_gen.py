'''
 POC stage

how to make sure that the decision is considered and
logged only after TF is transferred?
get_state should indicate that



Gen:
- choose the next best order,
which is 'wait until x units are ready and rush them'
- once they are ready, join them into TF1

Peps:
- always attack with whatever is in TF1



 2 TFs:
   - TF1: attack
   - TF2: reserve
 3 states:
 - wait for TF1 to deplete, attack meanwhile
 - wait till TF2 >= 10 marines
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
    action_list = ("Gen_Add_4_marines_to_TF1", "Gen_Add_8_marines_to_TF1",
                   "Gen_Add_12_marines_to_TF1", "Gen_Add_16_marines_to_TF1")

    action = None
    agent_name = "grievous"
    sgt = None
    TF1 = []
    prev_state = ""

    # def __init__(self, cfg, sgt):
    #     logging.getLogger(self.agent_name).info(f"L2AgentGrievous.init({__name__})")
    #     super(L2AgentGrievous, self).__init__(cfg)

    def assgin_sergant(self, sgt):
        self.logger.debug(
            f"Sergant: '{str(sgt.agent_name)}' was assigned for duty")
        self.sgt = sgt

    def debug(self, obs):
        self.logger.debug("state: " + str(self.get_state(obs, is_debug=True)))
        self.Gen_Add_8_marines_to_TF1(obs,
                                      check_action_availability_only=False)

    # def step(self, obs):
    #     return super(L2AgentGrievous, self).step(obs)

    def get_state(self, obs, is_debug=False):
        if self.current_action is not None and not is_debug:
            if not (getattr(self, self.current_action)(
                    obs, check_action_availability_only=False)):
                # Gen still founds it impossible to issue an order
                return self.prev_state

        count_marines = len(self.get_my_units_by_type(obs,
                                                      units.Terran.Marine))
        count_enemy_barrackses = len(
            self.get_enemy_units_by_type(obs, units.Terran.Barracks))
        count_enemy_factories = len(
            self.get_enemy_units_by_type(obs, units.Terran.Factory))
        count_enemy_starport = len(
            self.get_enemy_units_by_type(obs, units.Terran.Starport))
        count_enemy_marines = len(
            self.get_enemy_units_by_type(obs, units.Terran.Marine))
        count_enemy_marauders = len(
            self.get_enemy_units_by_type(obs, units.Terran.Marauder))
        count_enemy_tanks = (
            len(self.get_enemy_units_by_type(obs, units.Terran.SiegeTank)) +
            len(self.get_enemy_units_by_type(obs,
                                             units.Terran.SiegeTankSieged)))
        count_enemy_hells = len(
            self.get_enemy_units_by_type(obs, units.Terran.Hellion))

        enemy_marines_band = 0 if count_enemy_marines == 0 else (
            int(count_enemy_marines / 3) + 1) * 3
        enemy_marauders_band = 0 if count_enemy_marauders == 0 else (
            int(count_enemy_marauders / 2) + 1) * 2

        if is_debug:
            return (  # TF1/reserve?
                f"our marines:{count_marines}, " +
                f"enemy marines:~{enemy_marines_band}, " +
                f"marauders:~{enemy_marauders_band}, " +
                f"tanks:{count_enemy_tanks} " + f"hells:{count_enemy_hells} " +
                f"barrackses:{count_enemy_barrackses} " +
                f"factories:{count_enemy_factories}, " +
                f"factories:{count_enemy_factories}, " +
                f"starport:{count_enemy_starport}")

        new_state = (
            count_marines,  # TF1/reserve
            enemy_marines_band,
            enemy_marauders_band,
            count_enemy_barrackses,
            count_enemy_factories,
            count_enemy_starport,
            count_enemy_tanks,
            count_enemy_hells)
        self.prev_state = new_state
        return new_state

    def Gen_Add_4_marines_to_TF1(self, obs, check_action_availability_only):
        return self.Gen_Add_X_marines_to_TF1(obs, 4,
                                             check_action_availability_only)

    def Gen_Add_8_marines_to_TF1(self, obs, check_action_availability_only):
        return self.Gen_Add_X_marines_to_TF1(obs, 8,
                                             check_action_availability_only)

    def Gen_Add_12_marines_to_TF1(self, obs, check_action_availability_only):
        return self.Gen_Add_X_marines_to_TF1(obs, 12,
                                             check_action_availability_only)

    def Gen_Add_16_marines_to_TF1(self, obs, check_action_availability_only):
        return self.Gen_Add_X_marines_to_TF1(obs, 16,
                                             check_action_availability_only)

    def Gen_Add_X_marines_to_TF1(self, obs, number_of_marines_in_reinforcement,
                                 check_action_availability_only):
        if check_action_availability_only:
            return True

        marines = self.get_my_units_by_type(obs, units.Terran.Marine)
        marine_IDs = [(marine.tag) for marine in marines]
        TF2_marine_IDs = list(set(marine_IDs).difference(self.TF1))
        self.logger.debug(
            f"TF1 Size:{len(marine_IDs)-len(TF2_marine_IDs)}, TF2 Size: {len(TF2_marine_IDs)}, IDs: {str(TF2_marine_IDs)}"
        )

        if len(TF2_marine_IDs) >= number_of_marines_in_reinforcement:
            self.logger.info(
                f"Reinforcement has arrived: Transferring {len(TF2_marine_IDs)} marines to TF1"
            )
            self.TF1 = marine_IDs
            self.sgt.assign_TF1(marine_IDs)
            return True
        return False
