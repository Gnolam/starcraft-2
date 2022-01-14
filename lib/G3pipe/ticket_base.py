import logging

from pysc2.lib.actions import build_queue
from lib.G3pipe.ticket_status import TicketStatus
from lib.G3pipe.pipeline_base import PipelineBase


class BasePipelineTicket(TicketStatus):
    '''
    Class to manage the execution of a single `PipelineTicket`'
    Contains the place holders for downstream classes
    '''

    # status: int = None
    depends_on_list = None
    blocks_whom_id: int = None
    pipelene: PipelineBase = None

    # Should be set
    base_top_left: bool = None

    def __init__(self):
        super().__init__()
        self.logger.debug("Creating '" + self.__class__.__name__ + "'")

    def __str__(self):
        extra_info = ""
        if self.depends_on_list is not None:
            if len(self.depends_on_list) > 0:
                deps = [
                    self.pipelene.who_is(depends_on)
                    for depends_on in self.depends_on_list
                ]
                extra_info += f", depends on {deps}"

        if self.blocks_whom_id is not None:
            extra_info += (", blocks " +
                           f"'{self.pipelene.who_is(self.blocks_whom_id)}'")
        return (
            f"{self.id}_{self.__class__.__name__}, status: {self.str_status()}"
            + extra_info)

    def link_to_pipeline(self, parent_pipeline: PipelineBase,
                         ticket_id: int) -> None:
        """ Secondary action, performed by Pipeline::add_order() """
        self.pipelene = parent_pipeline
        self.id = ticket_id
        self.logger.debug("Assgining ID:" + str(ticket_id))

    def add_dependency(self, ticket_id: int) -> None:
        """ This ticket cannot be resolved until `ticket_id` is complete """
        self.logger.debug(
            f"add_dependency('{self.pipelene.who_is(ticket_id)}')")
        if self.depends_on_list is None:
            self.depends_on_list = []
        self.depends_on_list.append(ticket_id)
        self.mark_blocked()
        self.logger.debug("new status: " + str(self))
        self.pipelene.book[ticket_id].assign_as_blocker(self.id)

    def remove_dependency(self, ticket_id: int) -> None:
        """ This ticket will no longer be dependant on `ticket_id`"""
        self.logger.debug(
            f"remove_dependency('{self.pipelene.who_is(ticket_id)}')")
        if self.depends_on_list is None:
            raise Exception("depends_on is empty")
        elif ticket_id not in self.depends_on_list:
            raise Exception(f"{ticket_id} is not found " +
                            f"in the depends_on list: {self.depends_on_list}")
        else:
            self.depends_on_list.remove(ticket_id)
        if len(self.depends_on_list) == 0:
            self.mark_opened()

    def assign_as_blocker(self, ticket_id: int) -> None:
        """Mark this ticket as a blocker for `ticket_id`"""
        self.logger.debug(
            f"{self.pipelene.who_is(self.id)}.assign_as_blocker({ticket_id}:" +
            f"'{self.pipelene.who_is(ticket_id)}')")
        if self.blocks_whom_id is not None:
            raise Exception(
                "Cannot assign block. Ticket is already blocking " +
                f"'{self.pipelene.who_is(self.blocks_whom_id)}'")
        self.blocks_whom_id = ticket_id

    def mark_complete(self):
        """Mark order as complete"""
        if self.blocks_whom_id is not None:
            self.resign_as_blocker()
        self.set_status(TicketStatus.COMPLETED)

    def mark_in_progress(self):
        """Mark order as in progress"""
        if self.blocks_whom_id is not None:
            self.resign_as_blocker()
        self.set_status(TicketStatus.IN_PROGRESS)

    def resign_as_blocker(self) -> None:
        """Not a blocker anymore"""
        if self.blocks_whom_id is None:
            raise Exception("resign_as_blocker(): No blocked ID is specified")
        self.logger.debug(
            f"{self.pipelene.who_is(self.id)}.resign_as_blocker(" +
            f"'{self.pipelene.who_is(self.blocks_whom_id)}')")

        self.pipelene.book[self.blocks_whom_id].remove_dependency(self.id)

        # Note: Is implemented in remove_dependency()
        # # Check if this item was the last blocker
        # if len(blocked_order.depends_on_list) == 0:
        #     blocked_order.set_status(TicketStatus.OPEN)

        # Assume only 1 order can be blocked relationsip
        self.blocks_whom_id = None

    def run_init(self, obs):
        """ Checks the preconditions and creates downstream tickets.
        Can be left empty if no action is required
        """

    def run(self, obs):
        ''' Executes an order

            - Check if all conditions are fulfilled.
            - Issue an SC2 Order if all requiremnets are satisfied
            - Once SC2 Order is issues then mark self complete

        Arguments:
            - `obs` : SC2 obs (observation) object
        Returns:
            - (valid, order): tuple
                - valid: bool: is order valid? If _false_ then it should be
                deleted as impossible to execute
                - order: an SC2 order. `None` by default.
                if SC2 order is present then stop proceccing any other order

        Note:
            - adding new orders and depenedncies are left for run_init()
            - Should NOT handle the situation where previously submitted
                order (e.g. build supply depos building) was requested
                but may have not been fulfilled
            - should NOT wait till the order is executed before
                * reporting complete -> removing upward dependencies


        Return: 1 value
        - _SC2 order assigned_:
          - `None`: no SC2 orders
          - `pysc2.lib.actions`: an order to be executed

        Obsolete idea
        Return: dictionary
        - _SC2 order assigned_:
          - `None`: no SC2 orders
          - `pysc2.lib.actions`: an order to be executed
        - *New actions created*: indicates that pipeline should be re-scanned

                ``asx``: __ghghg__
        '''
        self.report_invalid_method()
