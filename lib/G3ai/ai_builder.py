from lib.G3ai.ai_base import aiBase
from lib.G3ai.action_list import BuildTicketsEcon

from pysc2.lib import units
from lib.c01_obs_api import *


class aiBuilder(aiBase, BuildTicketsEcon):

    agent_name = "aiBuilder"
    ai_log_suffix = "Econ"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.log.debug("aiBuilder::init()")
        self.fn_db_results = "db/bob_results.csv"
        self.fn_db_decisions = "db/bob_decisions.csv"
        self.fn_db_states = "db/bob_states.csv"

    def get_state(self, obs):
        # State vector should be revised to take into account both ours
        #   and enemy military potential
        completed_supply_depots = get_my_completed_units_by_type(
            obs, units.Terran.SupplyDepot)
        completed_barracks = get_my_completed_units_by_type(
            obs, units.Terran.Barracks)
        marines = get_my_units_by_type(obs, units.Terran.Marine)

        return (len(completed_supply_depots), len(completed_barracks),
                len(marines))
