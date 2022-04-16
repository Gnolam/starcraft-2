from pysc2.lib import actions, units
from lib.ticket.base import TicketBase
from lib.c01_obs_api import *


class BuildTicketBase(TicketBase):
    new_building_metadata = {
        "Barrack": {
            "class_name": "POBuildBarracks",
            "should_build_function": "should_build_barrack",
            "max_building": 5
        },
        "SupplyDepot": {
            "class_name": "POBuildSupplyDepot",
            "should_build_function": "should_build_supply_depot",
            "max_building": 4
        },
    }

    # To be used by Bob Build orders only
    building_name = None
    sc2_building_tag = None
    assigned_scv_tag = None
    assigned_building_xy = None
    should_be_checked_for_retry = None
    retry_counter = None
    build_location_xy_options_top = None
    build_location_xy_options_bottom = None
    is_actioned = None

    def __init__(self):
        super().__init__()
        self.retry_counter = 0

    def should_build_barrack(self, obs) -> bool:
        self.get_len(obs)
        if self.len_barracks_100 < 1:
            return True, "No barracks yet built"
        order_length = self.get_best_barrack(obs).order_length
        return order_length > 3, f"best order_length inside barracks: ({order_length}) > 3"

    def should_build_supply_depot(self, obs) -> bool:
        self.get_len(obs)
        if self.len_supply_depots < 1:
            return True, "No Supply Depots yet built"
        return self.free_supply < 5, f"free_supply status: ({self.free_supply}) < 5"

    def build_dependency(self, obs, metadata_key) -> bool:
        """ Generalised function for constructing buildings """

        self.logger.debug(f"~> build_dependency('{metadata_key}')")

        self.get_len(obs)

        build_class_name = self.new_building_metadata[metadata_key][
            "class_name"]
        should_build_function = self.new_building_metadata[metadata_key][
            "should_build_function"]

        sc2_building_tag = eval(f"{build_class_name}.sc2_building_tag")
        # !!! ------- is_building_promised = self.pipelene.is_promised(metadata_key)

        len_building_all = len(get_my_units_by_type(obs, sc2_building_tag))
        len_building_100 = len(
            get_my_completed_units_by_type(obs, sc2_building_tag))
        is_building_in_progress = (len_building_all != len_building_100)

        self.logger.debug("  [CP121]: " + "build_class_name: " +
                          str(build_class_name) + ", should_build_function:" +
                          str(should_build_function) + ", tag: " +
                          str(sc2_building_tag) + ", all: " +
                          str(len_building_all) + " / complete: " +
                          str(len_building_100) + ", complete: " +
                          str(is_building_in_progress))

        # self.logger.debug(f"{metadata_key}: " + "")

        if is_building_promised:
            if is_building_in_progress:
                self.logger.debug(
                    f"  {metadata_key} promise was fulfilled, invalidate promise"
                )
                # !!! ------- self.pipelene.resolve_promise(metadata_key)
            else:
                # Yes, it was already promised but
                self.logger.debug(
                    "  " + str({metadata_key}) +
                    " was already promised but it is not in progress yet")
            return

        if is_building_in_progress:
            self.logger.debug(f"  {metadata_key} is already in progress")
            return

        # No ready building atm
        if len_building_all == 0:
            # No ready/in progress buildings and no promised, we need to do something about it
            self.logger.debug(f"Requesting first {metadata_key}: " +
                              f"(len_building_all = {len_building_all})")
            # !!! -------  self.pipelene.make_promise(metadata_key)
            self.pipelene.add_order(eval(f"{build_class_name}()"))
            return

        should_build, should_build_msg = getattr(self,
                                                 should_build_function)(obs)

        if should_build:
            self.logger.debug(f"Requesting new {metadata_key}: " +
                              f"({should_build_msg})")
            # !!! ------ self.pipelene.make_promise(metadata_key)
            self.pipelene.add_order(eval(f"{build_class_name}()"))
        else:
            self.logger.debug(f"  No need to build the {metadata_key}: " +
                              f"({should_build_msg})")

    def fn_sc2_build_building(self):
        self.report_invalid_method()

    def implement_build_action(self):
        """
        To be called if SCV fails to build for some reason

        Should return the SC2 order for a given `self.assigned_scv_tag` SCV
        """
        if not self.validate_building_inputs():
            return None

        self.logger.info("SC2: Build " + self.building_name)
        return self.fn_sc2_build_building()

    def generate_sc2_build_order(self, obs, len_building):
        """Generalisation of initial build order"""
        self.mark_as_issued()
        self.logger.info("SC2: Generating request for " + self.building_name)
        build_location_xy_options = self.build_location_xy_options_top if self.base_top_left else self.build_location_xy_options_bottom

        self.logger.info("Assigning SCV and building coords")
        self.assigned_scv_tag, self.assigned_building_xy = select_scv_to_build(
            obs, build_location_xy_options, len_building)

        return self.implement_build_action()

    def retry_action_if_needed(self, obs):
        self.logger.debug("~> retry_action_if_needed()")
        """ Check if SCV is idle, when it is supposed to work """
        if not self.validate_building_inputs():
            return None

        # Check if SCV is idle, if no - OK
        assigned_scv_order_length = [
            unit.order_length for unit in obs.observation.raw_units
            if unit.tag == self.assigned_scv_tag
        ]

        if len(assigned_scv_order_length) == 0:
            self.logger.warning("  Assigned SCV is dead?")
            return None

        if assigned_scv_order_length == 0:
            self.logger.debug("  Assigned SCV is still working")
            return None

        self.retry_counter += 1
        self.logger.debug(
            "found idle SCV, which is actually assigned to a job")

        if self.retry_counter % 20 == 0:
            self.logger.warning("  Failed to retry the build after " +
                                str(self.retry_counter) + " attempts")

        return self.implement_build_action()

    def validate_building_inputs(self):
        """ Confirm that SCV and building info is present"""
        is_valid = True

        if self.assigned_scv_tag is None:
            # raise Exception('SCV tag is not assigned')
            self.logger.warning(str(self) + ". SCV tag is not assigned")
            is_valid = False

        if self.assigned_building_xy is None:
            #raise Exception('Building XY is not assigned')
            self.logger.warning(str(self) + '. Building XY is not assigned')
            is_valid = False

        return is_valid
