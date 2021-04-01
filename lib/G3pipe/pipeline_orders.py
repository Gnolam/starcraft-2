from lib.G3pipe.ticket_base import PipelineTicketBase
from pysc2.lib import actions, units

# ----------------------------------------------------------------------------


class poBuildSupplyDepot(PipelineTicketBase):
    """ Requests and waits till the Supply Depot is constructed """
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
        self.logger.info("SC2: Build 'Supply Depo'")
        scv_tag, building_xy = self.build_with_scv_xy(
            obs, xy_options, self.len_supply_depots_100)
        return actions.RAW_FUNCTIONS.Build_SupplyDepot_pt(
            "now", scv_tag, building_xy)

    def run(self, obs):
        # This class does not have any downstream dependencies

        self.get_len(obs)

        self.logger.debug(f"  > supply_depots={self.len_supply_depots_100} " +
                          f"minerals={obs.observation.player.minerals} " +
                          f"scvs={self.len_scvs}")

        if (self.len_supply_depots_100 >= 4):
            self.logger.warn("Too many supply depos!")
            return False, None  # False - this order must be deleted

        # All conditions are met, generate an order and finish
        if (self.len_supply_depots_100 < 4
                and obs.observation.player.minerals >= 100
                and self.len_scvs > 0):
            self.mark_complete()
            return True, self.generate_sc2_order(obs)
        return True, None


# ----------------------------------------------------------------------------


class poBuildBarracks(PipelineTicketBase):
    """ Requests and waits till the Barracks is constructed """
    def __init__(self):
        super().__init__()

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
                                                      self.len_barrackses)
        return actions.RAW_FUNCTIONS.Build_Barracks_pt("now", scv_tag,
                                                       building_xy)

    def run_init(self, obs):
        self.get_len(obs)
        if self.len_supply_depots_100 == 0:
            self.parent_pipelene.add_order(poBuildSupplyDepot(),
                                           blocks_whom_id=self.ID)

    def run(self, obs):
        self.get_len(obs)

        self.logger.debug(f"  > barracks={self.len_barrackses} " +
                          f"minerals={obs.observation.player.minerals} " +
                          f"scvs={self.len_scvs}")

        if (self.len_barrackses >= 5):
            self.logger.warn("Too many barrackses!")
            return False, None  # False - this order must be deleted

        # All conditions are met, generate an order and finish
        if (self.len_supply_depots_100 > 0 and self.len_barrackses < 5
                and obs.observation.player.minerals >= 150
                and self.len_scvs > 0):
            self.mark_complete()
            return True, self.generate_sc2_order(obs)
        return True, None


# ----------------------------------------------------------------------------


class poTrainMarine(PipelineTicketBase):
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

    def if_need_new_barrack(self, obs):
        if (self.len_barrackses_100 > 0
                and obs.observation.player.minerals >= 50
                and self.free_supply > 0):

            best_barrack_order_length = self.get_best_barrack(obs).order_length
            dbg_msg = (
                f"Request new barrack (#{self.number_of_barracks_requested}): "
                +
                f"best_barrack.order_length ({best_barrack_order_length}) > 3"
                + f" and len_barrackses_100 ({self.len_barrackses_100}) < 5")

            # Request new Barrack if the queue is moderate length
            if self.number_of_barracks_requested < 1 and best_barrack_order_length >= 3:
                self.number_of_barracks_requested += 1
                self.logger.debug(dbg_msg)
                self.parent_pipelene.add_order(
                    poBuildBarracks())  # blocks_whom_id=self.ID)
                return True

            # Request new Barrack if the queue is large length
            if self.number_of_barracks_requested < 2 and best_barrack_order_length >= 4:
                self.number_of_barracks_requested += 1
                self.logger.debug(dbg_msg)
                self.parent_pipelene.add_order(
                    poBuildBarracks())  # , blocks_whom_id=self.ID)
                return True
            return False

    def run_init(self, obs):
        self.get_len(obs)

        # Only the 1st Barrack should be auto-constructed
        if self.len_barrackses == 0:
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
        supply_depots_in_progress = not (self.len_supply_depots
                                         == self.len_supply_depots_100)
        self.logger.debug(
            f"  > barracks_100={self.len_barrackses_100} " +
            f"minerals={obs.observation.player.minerals} " +
            f"free_supply={self.free_supply} " +
            f"wait for SD = {str(supply_depots_in_progress)} " +
            f"SDs:({self.len_supply_depots}/{self.len_supply_depots_100})")

        # Inherited from run_init()
        if self.free_supply == 0 and (not supply_depots_in_progress):
            self.parent_pipelene.add_order(poBuildSupplyDepot(),
                                           blocks_whom_id=self.ID)

        # All conditions are met, generate an order and finish
        if (self.len_barrackses_100 > 0
                and obs.observation.player.minerals >= 50
                and self.free_supply > 0):

            if self.if_need_new_barrack(obs):
                return True, None

            best_barrack = self.get_best_barrack(obs)

            # if there is still a place for a brave new marine?
            if best_barrack.order_length < 5:
                self.number_of_mariners_to_build_remaining -= 1
                if self.number_of_mariners_to_build_remaining <= 0:
                    self.mark_complete()
                return True, self.generate_sc2_order(obs, best_barrack.tag)
            else:
                # No place for mariners at the moment
                return True, None
        return True, None
