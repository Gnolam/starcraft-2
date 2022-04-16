"""
Implementation of Pipeline class

- to be merged with PipelineBase

"""

from lib.ticket.base import TicketStatus, TicketBase
from lib.pipeline.base import PipelineBase


class Pipeline(PipelineBase):
    '''
    Class to manage the set of current `PipelineTicket`'s
    '''
    def add_order(self,
                  new_ticket: TicketBase,
                  blocks_whom_id: int = None) -> int:
        """ Adds order to the pipeline and assigns it an order ID """
        self.logger.info("Adding '%s' to pipeline. ID: %s",
                         new_ticket.__class__.__name__,
                         str(self.order_counter))
        self.book.append(new_ticket)
        new_ticket.link_to_pipeline(parent_pipeline=self,
                                    ticket_id=self.order_counter)
        new_ticket.base_top_left = self.base_top_left

        if blocks_whom_id is not None:
            self.book[blocks_whom_id].add_dependency(self.order_counter)

        # Set ID for the next order
        self.order_counter += 1

    def is_empty(self) -> bool:
        "Returns True if current pipeline has no active orders"
        pipeline_is_empty = len([
            ticket.id for ticket in self.book if ticket.current_status not in
            [TicketStatus.COMPLETED, TicketStatus.INVALID]
        ]) == 0
        self.logger.debug("is_empty(): %s, %s", str(pipeline_is_empty),
                          str(self))
        return pipeline_is_empty

    def get_executable_tickets_list(self) -> list:
        "Provides the list of tickets sutiable for run() loop"
        return [
            ticket.id for ticket in self.book if ticket.current_status in
            [TicketStatus.CREATED, TicketStatus.UNBLOCKED]
        ]

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
        return str(self.book[ticket_id])

    def run(self, obs):
        """ Scans: through all the orders in the book and tries to run those, which are active """
        #    Check only tickets IDs, which were used during the last run:
        #    This it will be possible to
        #       1. Marine: add $ req.
        #       2. confim $, clean marine ticket
        #       3. Marine ticket generate order

        self.logger.debug("CP21: ~> run()")

        self.get_len(obs)
        self.logger.debug("Stat: ")
        self.logger.debug(f"  Mins:{obs.observation.player.minerals}" +
                          f", SCVs:{self.len_scvs}" +
                          f", Free:{self.free_supply}")

        self.logger.debug(
            f"  SDs:({str(self.len_supply_depots_100)}/{str(self.len_supply_depots)})"
            + f", Bks:({str(self.len_barracks_100)}/{str(self.len_barracks)})")

        should_iterate = True

        # Verify that list of active did not change between runs
        # init with ACTIVE list so run does not scan twice throught them
        # if nothing happens
        last_iteration_ticket_ids = self.get_executable_tickets_list()

        while should_iterate:
            # Run all tickets with executable status

            # Debug display status
            self.logger.debug("List of tickets for the loop:")
            for ticket_id in last_iteration_ticket_ids:
                self.logger.debug("    %s", self.who_is(ticket_id))

            for ticket_id in last_iteration_ticket_ids:
                current_ticket = self.book[ticket_id]
                self.logger.debug("looking into %s", str(current_ticket))
                is_valid, sc2_order = current_ticket.run(obs)
                if not is_valid:
                    # this will also invalidate all dependencies
                    current_ticket.mark_invalid()
                elif sc2_order is not None:
                    # The SC2 was issued, ignore the rest of the tickets
                    # should mark tiket complete - no, e.g poTrainMarine has it conditional
                    self.logger.debug("ticket '%s' has generated an order",
                                      str(current_ticket))
                    return sc2_order

            # Current list of tickets
            current_ticket_ids = self.get_executable_tickets_list()

            # Should iterate if the list of tickets have changed.
            # Reduction in the list should be checked as well
            count_new_ids = len(
                set(current_ticket_ids) - set(last_iteration_ticket_ids))
            count_gone_ids = len(
                set(last_iteration_ticket_ids) - set(current_ticket_ids))
            should_iterate = count_new_ids + count_gone_ids > 0
            self.logger.debug("End of loop results:")

            self.logger.debug("  new:  %s", str(count_new_ids))
            self.logger.debug("  gone: %s", str(count_gone_ids))
            last_iteration_ticket_ids = current_ticket_ids

        return None  # or SC2 order, if inything was resolved

    def __str__(self):
        ret = "\n  Current content of the pipeline gross book:\n    " + "-" * 40
        for ticket in self.book:
            ret += f"\n     {ticket.str_ext()}"
        return ret

    def retry_orders_if_needed(self, obs):
        """Returns SC2 order is any of the active tickets should be resumed"""

        self.logger.debug("Check if retries are required")
        ill_designed_tickets = [
            str(ticket) for ticket in self.book
            if ticket.should_be_checked_for_retry is None
        ]

        if len(ill_designed_tickets) > 0:
            raise Exception("The following tickets have non-defined " +
                            "`should_be_checked_for_retry` property:" +
                            str(ill_designed_tickets))

        # Scan through all pipeline tickets, select only active onces
        active_eligible_tickets = [
            ticket for ticket in self.book
            if ticket.is_opened() and ticket.should_be_checked_for_retry is
            True and ticket.is_alredy_issued()
        ]

        for active_ticket in active_eligible_tickets:
            sc2_order = active_ticket.retry_action_if_needed(obs)
            if sc2_order is not None:
                self.logger.warning("!!! Retry was required for %s !!!",
                                    str(active_ticket))
                return sc2_order
            else:
                self.logger.debug("CP444: %s  is under execution",
                                  str(active_ticket))
        return None