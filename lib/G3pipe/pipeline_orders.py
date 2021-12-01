from lib.G3pipe.ticket_base import BasePipelineTicket
from pysc2.lib import actions, units
# ----------------------------------------------------------------------------


class BasePipelineBuildTicket(BasePipelineTicket):
    def __init__(self):
        super().__init__()

    sc2_building_ID = None

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

    def should_build_barrack(self, obs) -> bool:
        self.get_len(obs)
        if self.len_barracks_100 < 1:
            return True, "No barracks at all"
        order_length = self.get_best_barrack(obs).order_length
        return order_length > 3, f"order_length ({order_length}) > 3"

    def should_build_supply_depot(self, obs) -> bool:
        self.get_len(obs)
        if self.len_supply_depots < 1:
            return True, "No Supply Depots at all"
        return self.free_supply < 5, f"free_supply ({self.free_supply}) < 5"

    def build_dependency(self, obs, metadata_key) -> bool:
        """ Generalised function for constructing buildings """
        self.get_len(obs)

        build_class_name = self.new_building_metadata[metadata_key][
            "class_name"]
        should_build_function = self.new_building_metadata[metadata_key][
            "should_build_function"]

        sc2_building_ID = eval(f"{build_class_name}.sc2_building_ID")
        is_building_promised = self.pipelene.promise_check(metadata_key)

        len_building_all = len(self.get_my_units_by_type(obs, sc2_building_ID))
        len_building_100 = len(
            self.get_my_completed_units_by_type(obs, sc2_building_ID))
        is_building_in_progress = (len_building_all != len_building_100)

        # self.logger.debug(f"{metadata_key}: " + "")

        if is_building_promised:
            if is_building_in_progress:
                # promise was fulfilled, invalidate promise
                self.pipelene.promise_resolve(metadata_key)
            else:
                # Yes, it was already promised
                self.logger.debug(f"  {metadata_key} was already promised")
            return

        if is_building_in_progress:
            self.logger.debug(f"  {metadata_key} is already in progress")
            return

        # No ready building atm
        if len_building_all == 0:
            # No ready/in progress buildings and no promised, we need to do something about it
            self.logger.debug(f"Requesting first {metadata_key}: " +
                              f"(len_building_all = {len_building_all})")
            self.pipelene.promise_make(metadata_key)
            self.pipelene.add_order(eval(f"{build_class_name}()"))
            return

        should_build, should_build_msg = getattr(self,
                                                 should_build_function)(obs)

        if should_build:
            self.logger.debug(f"Requesting new {metadata_key}: " +
                              f"({should_build_msg})")
            self.pipelene.promise_make(metadata_key)
            self.pipelene.add_order(eval(f"{build_class_name}()"))
        else:
            self.logger.debug(f"  No need to build the {metadata_key}: " +
                              f"({should_build_msg})")


# ----------------------------------------------------------------------------


class poBuildSupplyDepot(BasePipelineBuildTicket):
    """ Requests and waits till the Supply Depot is constructed """

    sc2_building_ID = units.Terran.SupplyDepot

    def __init__(self):
        super().__init__()

    def generate_sc2_order(self, obs):
        # ToDo: should be loaded via map config
        xy_options = {
            0: (20 + 1, 27 + 3),
            1: (20 + 3, 27 + 3),
            2: (20 - 3, 27 + 5),
            3: (20 - 3, 27 + 7)
        } if self.base_top_left else {
            0: (69 - 3, 77 - 3),
            1: (69 - 5, 77 - 3),
            2: (69 - 5, 77 - 5),
            3: (69 - 5, 77 - 7)
        }
        self.logger.info("SC2: Build 'Supply Depot'")
        scv_tag, building_xy = self.build_with_scv_xy(
            obs, xy_options, self.len_supply_depots_100)
        return actions.RAW_FUNCTIONS.Build_SupplyDepot_pt(
            "now", scv_tag, building_xy)

    def run(self, obs):
        # This class does not have any downstream dependencies

        self.get_len(obs)

        # Invalidate order
        if (self.len_supply_depots >= 4):
            self.logger.warn("Too many supply depos! " +
                             f"(len_supply_depots = {self.len_supply_depots})")
            return False, None  # False - this order must be deleted

        # All conditions are met, generate an order and finish
        if (obs.observation.player.minerals >= 100 and self.len_scvs > 0):
            self.mark_complete()
            return True, self.generate_sc2_order(obs)
        return True, None


# ----------------------------------------------------------------------------


class poBuildBarracks(BasePipelineBuildTicket):
    """ Requests and waits till the Barracks is constructed """

    sc2_building_ID = units.Terran.Barracks

    def __init__(self):
        super().__init__()

    def generate_sc2_order(self, obs):
        # ToDo: should be loaded via map config
        xy_options = {
            0: (27 + 4, 20 + 0),
            1: (27 + 2, 20 + 0),
            2: (27 + 0, 20 + 0),
            3: (27 + 2, 20 + 7),
            4: (27 + 0, 20 + 7)
            # 0: (20 + 7, 20 + 0),
            # 1: (20 + 9, 27 + 4),
            # 2: (20 + 7, 27 + 4),
            # 3: (20 + 11, 27 + 2),
            # 4: (20 + 11, 27 + 0)
        } if self.base_top_left else {
            0: (69 - 7, 77 - 0),
            1: (69 - 9, 77 - 2),
            2: (69 - 11, 77 - 4),
            3: (69 - 13, 77 - 2),
            4: (69 - 7, 77 - 6)
        }
        self.logger.info("SC2: Build 'Barracks'")
        scv_tag, building_xy = self.build_with_scv_xy(obs, xy_options,
                                                      self.len_barracks)
        return actions.RAW_FUNCTIONS.Build_Barracks_pt("now", scv_tag,
                                                       building_xy)

    def run(self, obs):
        self.get_len(obs)

        if (self.len_barracks >= 5):
            self.logger.warn("Too many barracks!" +
                             f" (len_barracks={self.len_barracks})")
            return False, None  # False - this order must be deleted

        # All conditions are met, generate an order and finish
        if (self.len_supply_depots_100 > 0
                and obs.observation.player.minerals >= 150
                and self.len_scvs > 0):
            self.mark_complete()
            return True, self.generate_sc2_order(obs)
        return True, None


# ----------------------------------------------------------------------------


class poTrainMarine(BasePipelineBuildTicket):
    number_of_mariners_to_build: int = None
    number_of_mariners_to_build_remaining: int = None
    number_of_barracks_requested: int = None

    def __init__(self, number_of_mariners_to_build: int):
        super().__init__()
        self.number_of_mariners_to_build = number_of_mariners_to_build
        self.number_of_mariners_to_build_remaining = number_of_mariners_to_build
        self.number_of_barracks_requested = 0

    def __str__(self):
        s = super().__str__()

        if self.status_is_active():
            s += (f", {self.number_of_mariners_to_build_remaining} (out of " +
                  f"{self.number_of_mariners_to_build}) left")
        return s

    def generate_sc2_order(self, obs, best_barrack_tag):
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
                return True, self.generate_sc2_order(obs, best_barrack.tag)
            else:
                # No place for mariners at the moment
                self.logger.info("All barracks are full at the moment")
                return True, None
        return True, None


class poAccumulateReserve(BasePipelineBuildTicket):
    """ Add the new units to reserve """
    def __init__(self):
        super().__init__()

    def __str__(self):
        s = super().__str__()

        if self.status_is_active():
            s += "Accumulate"
        return s

    def run(self, obs):
        self.logger.debug("Do nothing atm")

        self.mark_complete()
        return True, None


class poGenTransferReserve(BasePipelineBuildTicket):
    # Belongs to Sgt Peps
    fn_transfer_to_TF1 = None

    def __init__(self, fn_transfer_to_TF1):
        super().__init__()
        self.fn_transfer_to_TF1 = fn_transfer_to_TF1

    def __str__(self):
        s = super().__str__()

        if self.status_is_active():
            s += "Transfer"
        return s

    def run(self, obs):
        self.logger.debug("Reinforce TF1")
        self.fn_transfer_to_TF1(obs)

        self.mark_complete()
        return True, None
