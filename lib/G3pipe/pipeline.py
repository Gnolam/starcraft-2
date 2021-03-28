from lib.G3pipe.pipeline_order_bases import PipelineBase, PipelineTicketBase
from lib.ticket_status import TicketStatus


class Pipeline(PipelineBase):
    '''
    Class to manage the set of current `PipelineTicket`'s
    '''
    order_counter: int = None

    # ToDO: should be added by lifecycle, when setting up the new game
    base_top_left: bool = None

    def __init__(self):
        super().__init__()
        self.order_counter = None

    def add_order(self,
                  new_ticket: PipelineTicketBase,
                  blocks_whom_id: int = None) -> int:
        """ Adds order to the pipeline and assigns it an order ID """
        if self.order_counter is None:
            self.order_counter = 0
        else:
            self.order_counter += 1

        self.logger.info(
            f"Adding '{new_ticket.__class__.__name__ }' to pipeline. ID:{self.order_counter}"
        )
        self.book.append(new_ticket)
        new_ticket.link_to_pipeline(parent_pipeline=self,
                                    ticket_id=self.order_counter)
        new_ticket.set_status(TicketStatus.INIT)
        new_ticket.base_top_left = self.base_top_left

        if blocks_whom_id is not None:
            self.book[blocks_whom_id].add_dependency(self.order_counter)

    def is_empty(self) -> bool:
        '''
        Returns True if current pipeline has all orders 'COMPLETE'
        '''
        pass

    def who_is(self, ticket_id: int) -> str:
        ''' Get simple representation of the ticket'''
        if ticket_id is None:
            raise Exception("who_is() received None as argument")
        if self.order_counter is None:
            raise Exception(
                "who_is() is called when no tickets are in the book")
        if ticket_id < 0 or ticket_id > self.order_counter:
            raise Exception(f"who_is({ticket_id}) is out of range " +
                            f"(0..{self.order_counter})")
        return str(ticket_id) + "_" + self.book[ticket_id].__class__.__name__

    def run(self, obs):
        """ Scans: through all the orders in the book and tries to run those, which are active """
        # ToDo:
        #    Check only tickets IDs, which were used during the last run:
        #    This it will be possible to
        #       1. Marine: add $ req.
        #       2. confim $, clean marine ticket
        #       3. Marine ticket generate order
        for ticket_ID in [
                ticket.ID for ticket in self.book
                if ticket.get_status() in [TicketStatus.ACTIVE]
        ]:
            print(self.who_is(ticket_ID))

        return None  # or SC2 order, if inything was resolved

    def __str__(self):
        ret = "  Current content of the pipeline gross book:\n    " + "-" * 40
        for ticket in self.book:
            ret += f"\n    ID:{ticket.ID}, {str(ticket)}"
        return ret
