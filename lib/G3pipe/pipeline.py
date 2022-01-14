from lib.G3pipe.ticket_status import TicketStatus
from lib.G3pipe.pipeline_base import PipelineBase
from lib.G3pipe.ticket_base import BasePipelineTicket


class Pipeline(PipelineBase):
    '''
    Class to manage the set of current `PipelineTicket`'s
    '''
    def __init__(self):
        super().__init__()

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
        new_ticket.mark_opened()
        new_ticket.base_top_left = self.base_top_left

        if blocks_whom_id is not None:
            self.book[blocks_whom_id].add_dependency(self.order_counter)

        # Set ID for the next order
        self.order_counter += 1

    def is_empty(self) -> bool:
        """ Returns True if current pipeline has no active orders """
        pipeline_is_empty = len(
            [ticket.id for ticket in self.book if ticket.is_opened()]) == 0
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
        #    Check only tickets IDs, which were used during the last run:
        #    This it will be possible to
        #       1. Marine: add $ req.
        #       2. confim $, clean marine ticket
        #       3. Marine ticket generate order

        self.logger.debug("CP21: ~> run()")

        active_ticket_ids = [
            ticket.id for ticket in self.book if ticket.is_opened()
        ]

        fulfilled_list = [
            promise_var for promise_var in self.new_building_done_promises
            if self.new_building_done_promises[promise_var] is True
        ]
        if len(fulfilled_list) > 0:
            self.logger.debug("Clearing fulfilled promises:")
            for promise_var in fulfilled_list:
                self.logger.debug(
                    f"  Clearing promise records for '{promise_var}'")
                self.new_building_made_promises[promise_var] = False
                self.new_building_done_promises[promise_var] = False

        # Debug display status
        self.logger.debug("List of active tickets:")
        for ticket_id in active_ticket_ids:
            self.logger.debug(" " * 4 + self.who_is(ticket_id))

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
        last_iteration_ticket_ids = current_ticket_ids = [
            ticket.id for ticket in self.book if ticket.is_opened()
        ]

        while should_iterate:
            # Run all tickets with ACTIVE status
            for ticket in [
                    ticket for ticket in self.book if ticket.is_opened()
            ]:
                self.logger.debug("looking into " + self.who_is(ticket.id))
                is_valid, sc2_order = ticket.run(obs)
                if not is_valid:
                    ticket.mark_invalid()
                elif sc2_order is not None:
                    # The SC2 was issued, ignore the rest of the tickets
                    # should mark tiket complete - no, e.g poTrainMarine has it conditional
                    self.logger.debug("ticket '" + str(ticket) +
                                      "' has generated an order")
                    return sc2_order

            # Current list of tickets
            current_ticket_ids = [
                ticket.id for ticket in self.book if ticket.is_opened()
            ]

            # Should iterate if the list of tickets have changed.
            # Reduction in the list should be checked as well
            count_new_ids = len(
                set(current_ticket_ids) - set(last_iteration_ticket_ids))
            count_gone_ids = len(
                set(last_iteration_ticket_ids) - set(current_ticket_ids))
            should_iterate = count_new_ids + count_gone_ids > 0
            self.logger.debug("End of loop results:")

            self.logger.debug("  new:  " + str(count_new_ids))
            self.logger.debug("  gone: " + str(count_gone_ids))
            last_iteration_ticket_ids = current_ticket_ids

        return None  # or SC2 order, if inything was resolved

    def __str__(self):
        ret = "\n  Current content of the pipeline gross book:\n    " + "-" * 40
        for ticket in self.book:
            ticket_str = str(ticket)
            if not ticket.is_opened():
                ticket_str = ticket_str.replace("'", " ")
            ret += f"\n     {ticket_str}"
        ret += f"\n  * Promises current  = {str(self.new_building_made_promises)}"
        ret += f"\n  * Promises resolved = {str(self.new_building_done_promises)}"
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
                self.logger.warning("!!! Retry was required for " +
                                    str(active_ticket) + "!!!")
                return sc2_order
            else:
                self.logger.debug("CP444: " + str(active_ticket) +
                                  " is under execution")
        return None
