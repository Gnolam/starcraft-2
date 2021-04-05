from lib.G3ai.ai_base import aiBase
from lib.G3ai.action_list import BuildTicketsEcon

from pysc2.lib import actions, units
import numpy as np
import random


class aiBuilder(aiBase, BuildTicketsEcon):

    agent_name = "aiBuilder"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.logger.debug("aiBuilder::init()")

    def get_state(self, obs):
        # State vector should be revised to take into account both ours
        #   and enemy military potential
        completed_supply_depots = self.get_my_completed_units_by_type(
            obs, units.Terran.SupplyDepot)
        completed_barracks = self.get_my_completed_units_by_type(
            obs, units.Terran.Barracks)
        marines = self.get_my_units_by_type(obs, units.Terran.Marine)

        return (len(completed_supply_depots), len(completed_barracks),
                len(marines))
