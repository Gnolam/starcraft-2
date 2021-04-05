from lib.G3pipe.ticket_base import BasePipelineTicket
from pysc2.lib import actions, units
# ----------------------------------------------------------------------------


class BasePipelineBuildTicket(BasePipelineTicket):
    def __init__(self):
        super().__init__()

    sc2_building_ID = None

    new_building_metadata = {
        "Barrack": {
            "is_building_promised_tag": "is_barrack_promised",
            "class_name": "poBuildBarracks",
            "max_building": 5
        },
        "SupplyDepot": {
            "is_building_promised_tag": "is_supply_depo_promised",
            "class_name": "poBuildSupplyDepot",
            "max_building": 4
        },
    }

    def new_building_should_build(self, obs) -> tuple:
        if 1 >= 1:
            self.report_invalid_method()
        return True, "Fake msg"

    def new_building_request_if_needed(self, obs, metadata_key) -> bool:
        """ Generalised function for constructing buildings """
        self.get_len(obs)

        build_class_name = self.new_building_metadata[metadata_key][
            "class_name"]
        sc2_building_ID = eval(f"{build_class_name}.sc2_building_ID")
        is_building_promised = self.get_new_building_promise(metadata_key)

        len_building_all = len(self.get_my_units_by_type(obs, sc2_building_ID))
        len_building_100 = len(
            self.get_my_completed_units_by_type(obs, sc2_building_ID))
        is_building_in_progress = (len_building_all != len_building_100)

        if is_building_promised:
            if is_building_in_progress:
                # promise was fulfilled, invalidate promise
                self.logger.debug(
                    f"Promise was fulfilled for '{metadata_key}'")
                self.set_new_building_promise(metadata_key, False)
            else:
                self.logger.debug(f"'{metadata_key}' was already promised." +
                                  "Construction has not started yet")
                return

        # No ready building atm
        if len_building_100 == 0:
            # Yes, it was already promised
            # No ready buildings and no promised, we need to do something about it
            self.logger.debug(f"Requesting first {metadata_key}: " +
                              f"(len_building_100 = {len_building_100}")
            self.set_new_building_promise(metadata_key, True)
            self.parent_pipelene.add_order(eval(f"{build_class_name}()"))
            return

        should_build, should_build_msg = self.new_building_should_build(obs)

        if should_build:
            self.logger.debug(f"Requesting new {metadata_key}: " +
                              f"({should_build_msg})")
            self.set_new_building_promise(metadata_key, True)
            self.parent_pipelene.add_order(eval(f"{build_class_name}()"))
        else:
            self.logger.debug(f"No need to build the {metadata_key}: " +
                              f"({should_build_msg})")

    def set_new_building_promise(self, metadata_key: str,
                                 new_value: bool) -> None:
        promise_var = self.new_building_metadata[metadata_key][
            "is_building_promised_tag"]
        self.logger.debug(
            "Set promise for " +
            f"'{metadata_key}'('{promise_var}') -> {str(new_value)}")
        promise_var = self.new_building_metadata[metadata_key][
            "is_building_promised_tag"]
        self.parent_pipelene.new_building_metadata[promise_var] = new_value

    def get_new_building_promise(self, metadata_key: str) -> bool:
        promise_var = self.new_building_metadata[metadata_key][
            "is_building_promised_tag"]
        if promise_var not in self.parent_pipelene.new_building_metadata:
            # Create new record
            self.parent_pipelene.new_building_metadata[promise_var] = False
            self.logger.debug("Init promise for " +
                              f"'{metadata_key}'('{promise_var}') -> False")
            return False
        else:
            # Previous record located
            return self.parent_pipelene.new_building_metadata[promise_var]


# ----------------------------------------------------------------------------


class poBuildSupplyDepot(BasePipelineBuildTicket):
    """ Requests and waits till the Supply Depot is constructed """

    sc2_building_ID = units.Terran.SupplyDepot

    def __init__(self):
        super().__init__()

    def new_building_should_build(self, obs) -> bool:
        self.get_len(obs)
        if self.len_supply_depots_100 < 1:
            return True, "No complete Supply Depots"
        return self.free_supply < 5, f"free_supply ({self.free_supply}) < 5"

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
        self.logger.info("SC2: Build 'Supply Depo'")
        scv_tag, building_xy = self.build_with_scv_xy(
            obs, xy_options, self.len_supply_depots_100)
        return actions.RAW_FUNCTIONS.Build_SupplyDepot_pt(
            "now", scv_tag, building_xy)

    def run(self, obs):
        # This class does not have any downstream dependencies

        self.get_len(obs)

        self.logger.debug(f"  > minerals={obs.observation.player.minerals} " +
                          f"scvs={self.len_scvs}")

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

    def new_building_should_build(self, obs) -> bool:
        self.get_len(obs)
        if self.len_barracks_100 < 1:
            return True, "No complete barracks"
        order_length = self.get_best_barrack(obs).order_length
        return order_length > 3, f"order_length ({order_length}) > 3"

    def generate_sc2_order(self, obs):
        # ToDo: should be loaded via map config
        xy_options = {
            0: (20 + 7, 20 + 0),
            1: (20 + 9, 27 + 4),
            2: (20 + 7, 27 + 4),
            3: (20 + 9, 27 + 0),
            4: (20 + 1, 27 + 0)
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

    def run_init(self, obs):
        self.new_building_request_if_needed(obs, "SupplyDepot")

    def run(self, obs):
        self.get_len(obs)

        self.logger.debug(f"  > barracks={self.len_barracks} " +
                          f"minerals={obs.observation.player.minerals} " +
                          f"scvs={self.len_scvs}")

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

    def run_init(self, obs):
        self.get_len(obs)

        # Only the 1st Barrack should be auto-constructed
        if self.len_barracks == 0:
            self.number_of_barracks_requested += 1
            self.parent_pipelene.add_order(poBuildBarracks(),
                                           blocks_whom_id=self.ID)

    def run(self, obs):
        if self.number_of_mariners_to_build_remaining <= 0:
            err_msg = ("number_of_mariners_to_build_remaining: " +
                       str(self.number_of_mariners_to_build_remaining) +
                       ". This function should not have been called")
            self.logger.error(err_msg)
            raise Exception(f"{self.__class__.__name__}::run(): {err_msg}")

        self.get_len(obs)

        self.new_building_request_if_needed(obs, "SupplyDepot")
        self.new_building_request_if_needed(obs, "Barrack")

        self.logger.debug(f"  > barracks_100={self.len_barracks_100} " +
                          f"minerals={obs.observation.player.minerals} " +
                          f"free_supply={self.free_supply} ")

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
