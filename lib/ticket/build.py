"Module for build tickets implementation"

from pysc2.lib import actions, units
from lib.ticket.base_build import BuildTicketBase


class POBuildSupplyDepot(BuildTicketBase):
    """ Requests and waits till the Supply Depot is constructed """

    # It is a class property and should stay here
    sc2_building_tag = units.Terran.SupplyDepot
    building_name = "SupplyDepot"
    should_be_checked_for_retry = True

    def __init__(self):
        super().__init__()
        self.build_location_xy_options_top = {
            0: (20 + 1, 27 + 3),
            1: (20 + 3, 27 + 3),
            2: (20 - 3, 27 + 5),
            3: (20 - 3, 27 + 7)
        }
        self.build_location_xy_options_bottom = {
            0: (69 - 3, 77 - 3),
            1: (69 - 5, 77 - 3),
            2: (69 - 5, 77 - 5),
            3: (69 - 5, 77 - 7)
        }

    def fn_sc2_build_building(self):
        return actions.RAW_FUNCTIONS.Build_SupplyDepot_pt(
            "now", self.assigned_scv_tag, self.assigned_building_xy)

    def run(self, obs):
        # This class does not have any downstream dependencies

        self.get_len(obs)

        # Invalidate order
        if self.len_supply_depots >= 4:
            self.logger.warning(
                "Too many supply depos! (len_supply_depots = %s)",
                str(self.len_supply_depots))
            return False, None  # False - this order must be deleted

        # All conditions are met, generate an order and finish
        if (obs.observation.player.minerals >= 100 and self.len_scvs > 0):
            self.mark_in_progress()
            return True, self.generate_sc2_build_order(obs,
                                                       self.len_supply_depots)
        return True, None


# ----------------------------------------------------------------------------


class POBuildBarracks(BuildTicketBase):
    """ Requests and waits till the Barracks is constructed """
    # It is a class property and should stay here
    sc2_building_tag = units.Terran.Barracks
    building_name = "Barracks"
    should_be_checked_for_retry = True

    def __init__(self):
        super().__init__()
        self.build_location_xy_options_top = {
            0: (27 + 6, 20 + 0),
            1: (27 + 3, 20 + 2),
            2: (27 + 0, 20 + 4),
            3: (27 + 3, 20 + 9),
            4: (27 + 0, 20 + 11)
        }
        self.build_location_xy_options_bottom = {
            0: (69 - 7, 77 - 0),
            1: (69 - 9, 77 - 2),
            2: (69 - 11, 77 - 4),
            3: (69 - 13, 77 - 6),
            4: (69 - 7, 77 - 6)
        }

    def fn_sc2_build_building(self):
        return actions.RAW_FUNCTIONS.Build_Barracks_pt(
            "now", self.assigned_scv_tag, self.assigned_building_xy)

    def run(self, obs):
        self.get_len(obs)

        if self.len_barracks >= 5:
            self.logger.warning("Too many barracks! (len_barracks=%s)",
                                str(self.len_barracks))
            return False, None  # False - this order must be deleted

        # All conditions are met, generate an order and finish
        if (self.len_supply_depots_100 > 0
                and obs.observation.player.minerals >= 150
                and self.len_scvs > 0):
            self.mark_in_progress()
            return True, self.generate_sc2_build_order(obs, self.len_barracks)
        return True, None
