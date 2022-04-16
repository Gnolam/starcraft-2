from lib.ticket.base import TicketBase


class poAccumulateReserve(TicketBase):
    """ Add the new units to reserve """

    should_be_checked_for_retry = False

    def __str__(self):
        message = super().__str__()

        if self.is_opened():
            message += "Accumulate"
        return message

    def run(self, obs):
        self.logger.debug("Do nothing atm")

        self.mark_in_progress()
        return True, None


class poGenTransferReserve(TicketBase):
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
