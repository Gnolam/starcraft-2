from l1_class import L1Agent
from pysc2.lib import units
import logging


class L2AgentBob(L1Agent):
    action_list = (
        "econ_do_nothing",
        "econ_harvest_minerals",
        "econ_build_supply_depot",
        "econ_build_barracks",
        "econ_train_marine"
    )

    agent_name = "bob"

    def __init__(self, cfg):
        self.logger = logging.getLogger(self.agent_name)
        self.logger.info(f"L2AgentBob.init({__name__})")
        super(L2AgentBob, self).__init__(cfg)

    def step(self, obs):
        ## print("step at L2AgentBob (%s)" % self.agent_name)
        return super(L2AgentBob, self).step(obs)

    def get_state(self, obs):
        # info for counters
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        idle_scvs = [scv for scv in scvs if scv.order_length == 0]
        command_centers = self.get_my_units_by_type(obs, units.Terran.CommandCenter)
        supply_depots = self.get_my_units_by_type(obs, units.Terran.SupplyDepot)
        completed_supply_depots = self.get_my_completed_units_by_type(
            obs, units.Terran.SupplyDepot)
        barrackses = self.get_my_units_by_type(obs, units.Terran.Barracks)
        completed_barrackses = self.get_my_completed_units_by_type(
            obs, units.Terran.Barracks)
        marines = self.get_my_units_by_type(obs, units.Terran.Marine)

        queued_marines = (completed_barrackses[0].order_length
                          if len(completed_barrackses) > 0 else 0)

        free_supply = (obs.observation.player.food_cap -
                       obs.observation.player.food_used)
        can_afford_supply_depot = obs.observation.player.minerals >= 100
        can_afford_barracks = obs.observation.player.minerals >= 150
        can_afford_marine = obs.observation.player.minerals >= 50

        enemy_scvs = self.get_enemy_units_by_type(obs, units.Terran.SCV)
        enemy_command_centers = self.get_enemy_units_by_type(obs, units.Terran.CommandCenter)
        enemy_supply_depots = self.get_enemy_units_by_type(obs, units.Terran.SupplyDepot)
        enemy_barrackses = self.get_enemy_units_by_type(obs, units.Terran.Barracks)
        enemy_factories = self.get_enemy_units_by_type(obs, units.Terran.Factory)
        enemy_starport = self.get_enemy_units_by_type(obs, units.Terran.Starport)

        # state_dict = {
        #     "command_centers": len(command_centers),
        #     "scvs": len(scvs),
        #     "idle_scvs": len(idle_scvs),
        #     "supply_depots": len(supply_depots),
        #     "completed_supply_depots": len(completed_supply_depots),
        #     "barrackses": len(barrackses),
        #     "completed_barrackses": len(completed_barrackses),
        #     "marines": len(marines),
        #     "queued_marines": queued_marines,
        #     "free_supply": free_supply,
        #     "can_afford_supply_depot": can_afford_supply_depot,
        #     "can_afford_barracks": can_afford_barracks,
        #     "can_afford_marine": can_afford_marine,
        #     "enemy_command_centers": len(enemy_command_centers),
        #     "enemy_scvs": len(enemy_scvs),
        #     "enemy_supply_depots": len(enemy_supply_depots),
        #     "enemy_barrackses": len(enemy_barrackses),
        #     "enemy_factories ": len(enemy_factories),
        #     "enemy_starport ": len(enemy_starport),
        #     "enemy_army_band": enemy_army_band,
        #     "res":obs.observation.player.minerals
        # }

        # self.log_actions(",get_state:")
        # for k, v in state_dict.items():
        #     self.log_actions(" %s=%s" % (k, v))

        return (len(command_centers),
                len(scvs),
                len(idle_scvs),
                len(supply_depots),
                len(completed_supply_depots),
                len(barrackses),
                len(completed_barrackses),
                len(marines),
                queued_marines,
                free_supply,
                can_afford_supply_depot,
                can_afford_barracks,
                can_afford_marine
                )

