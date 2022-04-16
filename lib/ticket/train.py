from lib.ticket.base_build import BuildTicketBase


class poTrainMarine(BuildTicketBase):
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
