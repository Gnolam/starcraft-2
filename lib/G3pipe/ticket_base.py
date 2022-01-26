import logging

from pysc2.lib.actions import build_queue
from lib.G3pipe.pipeline_base import PipelineBase
from lib.c01_obs_api import ObsAPI


class BasePipelineTicket(ObsAPI):

    # status: int = None
    depends_on_list = None
    blocks_whom_id: int = None
    pipelene: PipelineBase = None

    # Should be set
    base_top_left: bool = None

    # Constants
    OPENED = 2
    REQUESTED = 100
    IN_PROGRESS = 120
    COMPLETED = 150
    BLOCKED = 200
    INVALID = 400

    status_dict = {
        None: "N/A",
        OPENED: "OPENED",  #           Ticket is NOT blocked
        REQUESTED: "REQUESTED",  #     Build order was issued
        IN_PROGRESS: "IN_PROGRESS",  # Ticket is confirmed to start building
        COMPLETED: "COMPLETED",  #     Ticket was finished (for debug)
        BLOCKED: "BLOCKED",
        INVALID: "INVALID"
    }

    # Variables
    id: int = None
    current_status: int = None
    status_already_issued: bool = None

    def __init__(self):
        super().__init__()
        self.logger.debug("Creating '" + self.__class__.__name__ + "'")
        self.status_already_issued = False

    def check_if_valid(self):
        if self.current_status is None:
            raise Exception("Use of unassigned status value")
        if self.current_status not in self.status_dict:
            raise Exception(f"Unknown status: {self.current_status}")

    def str_status(self):
        self.check_if_valid()
        suffix = ""
        if self.is_alredy_issued():
            suffix += " (issued)"
        return self.status_dict[self.current_status]

    def mark_opened(self):
        self.set_status(self.OPENED)

    def is_opened(self):
        return self.get_status() == self.OPENED

    def mark_complete(self):
        self.set_status(self.COMPLETED)

    def is_completed(self):
        return self.get_status() == self.COMPLETED

    def mark_in_progress(self):
        self.set_status(self.IN_PROGRESS)

    def is_in_progress(self):
        return self.get_status() == self.IN_PROGRESS

    def mark_requested(self):
        self.set_status(self.REQUESTED)

    def is_requested(self):
        return self.get_status() == self.REQUESTED

    def mark_blocked(self):
        self.set_status(self.BLOCKED)

    def is_blocked(self):
        return self.get_status() == self.BLOCKED

    def mark_invalid(self):
        self.set_status(self.INVALID)

    def is_invalid(self):
        return self.get_status() == self.INVALID

    def set_status(self, new_status):
        if new_status is None:
            raise Exception(f"Cannot assign None status")
        if new_status not in [
                self.OPENED, self.IN_PROGRESS, self.BLOCKED, self.INVALID,
                self.REQUESTED, self.COMPLETED
        ]:
            raise Exception(f"Unknown new status: {new_status}")
        self.logger.debug(
            f"  Status for '{self.id}_{self.__class__.__name__}': " +
            f"'{self.status_dict[self.current_status]}' -> " +
            f"'{self.status_dict[new_status]}'")
        self.current_status = new_status

    def get_status(self):
        self.check_if_valid()
        return self.current_status

    def mark_as_issued(self) -> None:
        self.status_already_issued = True

    def is_alredy_issued(self) -> bool:
        return self.status_already_issued

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
        self.set_status(self.COMPLETED)

    def mark_in_progress(self):
        """Mark order as in progress"""
        if self.blocks_whom_id is not None:
            self.resign_as_blocker()
        self.set_status(self.IN_PROGRESS)

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
        #     blocked_order.set_status(self.OPEN)

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
