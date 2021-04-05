from lib.G3pipe.ticket_status import TicketStatus
from lib.G3pipe.pipeline_base import PipelineBase
from lib.G3pipe.ticket_base import BasePipelineTicket


class Pipeline(PipelineBase):
    '''
    Class to manage the set of current `PipelineTicket`'s
    '''
    order_counter: int = None

    # ToDO: should be added by lifecycle, when setting up the new game
    base_top_left: bool = None

    def __init__(self):
        super().__init__()
        self.order_counter = 0
        self.book = []
        self.new_building_metadata = {}

    def add_order(self,
                  new_ticket: BasePipelineTicket,
                  blocks_whom_id: int = None) -> int:
        """ Adds order to the pipeline and assigns it an order ID """
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

        # Set ID for the next order
        self.order_counter += 1

    def is_empty(self) -> bool:
        """ Returns True if current pipeline has no active orders """
        pipeline_is_empty = len([
            ticket.ID for ticket in self.book
            if ticket.get_status() in [TicketStatus.ACTIVE, TicketStatus.INIT]
        ]) == 0
        self.logger.debug(str(pipeline_is_empty) + str(self))
        return pipeline_is_empty

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

        active_ticket_IDs = [
            ticket.ID for ticket in self.book
            if ticket.get_status() in [TicketStatus.ACTIVE, TicketStatus.INIT]
        ]

        # Debug display status
        self.logger.debug("Tickets in the book for run():")
        for ticket_ID in active_ticket_IDs:
            self.logger.debug(f"  {ticket_ID}. " + self.who_is(ticket_ID))

        should_iterate = True

        # Verify that list of active did not change between runs
        # init with ACTIVE list so run does not scan twice throught them
        # if nothing happens
        last_iteration_ticket_IDs = current_ticket_IDs = [
            ticket.ID for ticket in self.book
            if ticket.get_status() in [TicketStatus.ACTIVE]
        ]

        while should_iterate:
            # run_init() for all INIT tickets
            # transfer status INIT -> ACTIVE
            for ticket in [
                    ticket for ticket in self.book
                    if ticket.get_status() == TicketStatus.INIT
            ]:
                self.logger.debug(f"run_init({self.who_is(ticket.ID)})")
                ticket.set_status(TicketStatus.ACTIVE)
                ticket.run_init(obs)

            # Run all tickets with ACTIVE status
            for ticket in [
                    ticket for ticket in self.book
                    if ticket.get_status() == TicketStatus.ACTIVE
            ]:
                self.logger.debug(f"ticket={str(ticket)}")
                is_valid, sc2_order = ticket.run(obs)
                if not is_valid:
                    ticket.set_status(TicketStatus.INVALID)
                elif sc2_order is not None:
                    # The SC2 was issued, ignore the rest of the tickets
                    return sc2_order

            # Current list of tickets
            current_ticket_IDs = [
                ticket.ID for ticket in self.book if ticket.get_status() in
                [TicketStatus.INIT, TicketStatus.ACTIVE]
            ]

            # Should iterate if the list of tickets have changed.
            # Reduction in the list should be checked as well
            count_new_IDs = len(
                set(current_ticket_IDs) - set(last_iteration_ticket_IDs))
            count_gone_IDs = len(
                set(last_iteration_ticket_IDs) - set(current_ticket_IDs))
            should_iterate = count_new_IDs + count_gone_IDs > 0
            self.logger.debug(
                f"new IDs: {count_new_IDs}, gone IDs: {count_gone_IDs}")
            last_iteration_ticket_IDs = current_ticket_IDs

        return None  # or SC2 order, if inything was resolved

    def __str__(self):
        ret = "\n  Current content of the pipeline gross book:\n    " + "-" * 40
        for ticket in self.book:
            ret += f"\n    ID:{ticket.ID}, {str(ticket)}"
        return ret
