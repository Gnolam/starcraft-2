from lib.G3pipe.ticket_base import BasePipelineTicket
from pysc2.lib import actions, units
from lib.c01_obs_api import *


class BasePipelineBuildTicket(BasePipelineTicket):
    new_building_metadata = {
        "Barrack": {
            "class_name": "poBuildBarracks",
            "should_build_function": "should_build_barrack",
            "max_building": 5
        },
        "SupplyDepot": {
            "class_name": "poBuildSupplyDepot",
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
        is_building_promised = self.pipelene.is_promised(metadata_key)

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
                self.pipelene.resolve_promise(metadata_key)
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
            self.pipelene.make_promise(metadata_key)
            self.pipelene.add_order(eval(f"{build_class_name}()"))
            return

        should_build, should_build_msg = getattr(self,
                                                 should_build_function)(obs)

        if should_build:
            self.logger.debug(f"Requesting new {metadata_key}: " +
                              f"({should_build_msg})")
            self.pipelene.make_promise(metadata_key)
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


# ----------------------------------------------------------------------------


class poBuildSupplyDepot(BasePipelineBuildTicket):
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
            self.logger.warn("Too many supply depos! " +
                             f"(len_supply_depots = {self.len_supply_depots})")
            return False, None  # False - this order must be deleted

        # All conditions are met, generate an order and finish
        if (obs.observation.player.minerals >= 100 and self.len_scvs > 0):
            self.mark_in_progress()
            return True, self.generate_sc2_build_order(obs,
                                                       self.len_supply_depots)
        return True, None


# ----------------------------------------------------------------------------


class poBuildBarracks(BasePipelineBuildTicket):
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
            self.logger.warn("Too many barracks!" + " (len_barracks=" +
                             str(self.len_barracks) + ")")
            return False, None  # False - this order must be deleted

        # All conditions are met, generate an order and finish
        if (self.len_supply_depots_100 > 0
                and obs.observation.player.minerals >= 150
                and self.len_scvs > 0):
            self.mark_in_progress()
            return True, self.generate_sc2_build_order(obs, self.len_barracks)
        return True, None


# ----------------------------------------------------------------------------


class poTrainMarine(BasePipelineBuildTicket):
    number_of_mariners_to_build: int = None
    number_of_mariners_to_build_remaining: int = None
    number_of_barracks_requested: int = None

    should_be_checked_for_retry = False

    def __init__(self, number_of_mariners_to_build: int):
        super().__init__()
        self.number_of_mariners_to_build = number_of_mariners_to_build
        self.number_of_mariners_to_build_remaining = number_of_mariners_to_build
        self.number_of_barracks_requested = 0

    def __str__(self):
        message = super().__str__()

        if self.is_opened():
            message += (
                f", {self.number_of_mariners_to_build_remaining} (out of " +
                f"{self.number_of_mariners_to_build}) left")
        return message

    def generate_sc2_train_order(self, obs, best_barrack_tag):
        self.logger.info("SC2: Train 'Marine'")
        return actions.RAW_FUNCTIONS.Train_Marine_quick(
            "now", best_barrack_tag)

    def run(self, obs):
        if self.number_of_mariners_to_build_remaining <= 0:
            err_msg = ("number_of_mariners_to_build_remaining: " +
                       str(self.number_of_mariners_to_build_remaining) +
                       ". This function should not have been called")
            self.logger.error(err_msg)
            raise Exception(f"{self.__class__.__name__}::run(): {err_msg}")

        self.get_len(obs)

        self.build_dependency(obs, "SupplyDepot")
        self.build_dependency(obs, "Barrack")

        # All conditions are met, generate an order and finish
        if (self.len_barracks_100 > 0 and obs.observation.player.minerals >= 50
                and self.free_supply > 0):

            best_barrack = self.get_best_barrack(obs)

            # if there is still a place for a brave new marine?
            if best_barrack.order_length < 5:
                self.number_of_mariners_to_build_remaining -= 1
                if self.number_of_mariners_to_build_remaining <= 0:
                    self.mark_complete()
                return True, self.generate_sc2_train_order(
                    obs, best_barrack.tag)
            else:
                # No place for mariners at the moment
                self.logger.info("All barracks are full at the moment")
                return True, None
        return True, None


class poAccumulateReserve(BasePipelineTicket):
    """ Add the new units to reserve """

    should_be_checked_for_retry = False

    def __init__(self):
        super().__init__()

    def __str__(self):
        message = super().__str__()

        if self.is_opened():
            message += "Accumulate"
        return message

    def run(self, obs):
        self.logger.debug("Do nothing atm")

        self.mark_in_progress()
        return True, None


class poGenTransferReserve(BasePipelineTicket):
    """ Assign all reserve units to TF1 """

    fn_transfer_to_TF1 = None
    should_be_checked_for_retry = False

    def __init__(self, fn_transfer_to_TF1):
        super().__init__()
        self.fn_transfer_to_TF1 = fn_transfer_to_TF1

    def __str__(self):
        message = super().__str__()

        if self.is_opened():
            message += "Transfer"
        return message

    def run(self, obs):
        self.logger.debug("Reinforce TF1")
        self.fn_transfer_to_TF1(obs)

        self.mark_in_progress()
        return True, None
