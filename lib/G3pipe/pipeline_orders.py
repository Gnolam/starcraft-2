from lib.G3pipe.pipeline_order_bases import PipelineTicketBase
from lib.ticket_status import TicketStatus
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
        scv_tag, building_xy = self.build_with_scv_xy(obs, xy_options,
                                                      self.len_supply_depots)
        return actions.RAW_FUNCTIONS.Build_SupplyDepot_pt(
            "now", scv_tag, building_xy)

    def run(self, obs):
        # This class does not have any downstream dependencies

        self.get_len(obs)

        self.logger.debug(f"  > supply_depots={self.len_supply_depots} " +
                          f"minerals={obs.observation.player.minerals} " +
                          f"scvs={self.len_scvs}")

        if (self.len_supply_depots >= 4):
            self.logger.warn("Too many supply depos!")
            return False, None  # False - this order must be deleted

        # All conditions are met, generate an order and finish
        if (self.len_supply_depots < 4
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
            3: (20 + 9, 27 + 0)
        } if self.base_top_left else {
            0: (69 - 7, 77 - 0),
            1: (69 - 9, 77 - 2),
            2: (69 - 11, 77 - 4),
            3: (69 - 13, 77 - 2)
        }
        scv_tag, building_xy = self.build_with_scv_xy(obs, xy_options,
                                                      self.len_barrackses)
        return actions.RAW_FUNCTIONS.Build_SupplyDepot_pt(
            "now", scv_tag, building_xy)

    def run_init(self, obs):
        # This class depends on existence of a Suppy depos but...
        # supply depo will be requested by recruit marine... so -> skip
        pass

    def run(self, obs):
        self.get_len(obs)

        self.logger.debug(f"  > barracks={self.len_barrackses} " +
                          f"minerals={obs.observation.player.minerals} " +
                          f"scvs={self.len_scvs}")

        if (self.len_barrackses >= 5):
            self.logger.warn("Too many barrackses!")
            return False, None  # False - this order must be deleted

        # All conditions are met, generate an order and finish
        if (self.len_supply_depots > 0 and self.len_barrackses < 5
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
        return (
            s + f", {self.number_of_mariners_to_build} / " +
            f"{self.number_of_mariners_to_build_remaining} marines to build")

    def generate_sc2_order(self, obs, best_barrack_tag):
        return actions.RAW_FUNCTIONS.Train_Marine_quick(
            "now", best_barrack_tag)

    def run_init(self, obs):
        self.get_len(obs)
        if self.len_barrackses == 0:
            self.number_of_barracks_requested += 1
            self.parent_pipelene.add_order(poBuildBarracks(),
                                           blocks_whom_id=self.ID)
        if self.free_supply == 0:
            self.parent_pipelene.add_order(poBuildSupplyDepot(),
                                           blocks_whom_id=self.ID)
        if self.len_barrackses > 0:
            best_barrack = self.get_best_barrack(obs)
            if best_barrack.order_length > 3 and self.len_barrackses < 5:
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
        self.logger.debug(f"  > barracks={self.len_barrackses} " +
                          f"minerals={obs.observation.player.minerals} " +
                          f"free_supply={self.free_supply}")

        # All conditions are met, generate an order and finish
        if (self.len_barrackses > 0 and obs.observation.player.minerals >= 50
                and self.free_supply > 0):

            best_barrack = self.get_best_barrack(obs)
            if self.number_of_barracks_requested < 1 and best_barrack.order_length >= 3:
                # Request new Barrack if the queue is moderate length
                self.number_of_barracks_requested += 1
                self.parent_pipelene.add_order(poBuildBarracks(),
                                               blocks_whom_id=self.ID)
                return True, None

            # Request new Barrack if the queue is large length
            if self.number_of_barracks_requested < 2 and best_barrack.order_length >= 4:
                self.number_of_barracks_requested += 1
                self.parent_pipelene.add_order(poBuildBarracks(),
                                               blocks_whom_id=self.ID)
                return True, None

            # if there is still a place for a brave new marine?
            if best_barrack.order_length < 5:
                self.number_of_mariners_to_build_remaining -= 1
                if self.number_of_mariners_to_build_remaining <= 0:
                    self.mark_complete()
                return True, self.generate_sc2_order(obs, best_barrack.tag)
            else:
                # No place for mariners at the moment
                return True, None
