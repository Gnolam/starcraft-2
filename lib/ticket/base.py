import logging
from enum import IntEnum

from pysc2.lib.actions import build_queue
from lib.pipeline.base import PipelineBase
from lib.c01_obs_api import ObsAPI


class TicketStatus(IntEnum):
    """
    - CREATED means that the ticket was just created and was not attended to yet
    - BLOCKED can be skipped if there are not dependencies or if they are already fulfilled
    - BLOCKED can be re-introduced before proceeding to REQUESTED
    - REQUESTED is used to indicate that SC2 build order was issued
                (can be skipped for non-building orders)
    - IN_PROGRESS
      - for unit order: indicates that order was not complete (e.g. 3 of 4 done)
      - for building order: indicates that the building process was confirmed
    - COMPLETED means that the order was confirmed to be fullfilled
      - for units: all units ordered
      - for building: its status is 100% complete
    - INVALID is irreversible and all dependencies should be marked INVALID as well
    """
    CREATED = 10
    BLOCKED = 20
    UNBLOCKED = 30
    REQUESTED = 40
    IN_PROGRESS = 50
    COMPLETED = 60
    INVALID = 404

    @classmethod
    def is_valid_value(cls, value):
        """Checks if the new value is valid"""
        return value in cls._value2member_map_


class TicketBase(ObsAPI):
    """ Base class for tickets: build and train """

    ticket_id: int = None
    current_status: TicketStatus = None
    depends_on_list: list = None
    blocks_whom_list: list = None
    pipelene: PipelineBase = None

    # Should be set
    base_top_left: bool = None

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating '%s'", self.__class__.__name__)
        self.current_status = TicketStatus.CREATED

    def str_status(self, status: TicketStatus = None):
        """User-friendly str() replacement"""
        if status is None:
            status = self.current_status
        return str(status).replace("TicketStatus.", "")

    def set_status(self, new_status: TicketStatus):
        """Change status of the ticket"""
        if not TicketStatus.is_valid_value(new_status):
            raise Exception(f"Unknown new status: {new_status}")
        self.logger.debug("  Change status for '%s'_%s: '%s' -> '%s'",
                          self.ticket_id, self.__class__.__name__,
                          self.str_status(), self.str_status(new_status))
        self.current_status = new_status

    def __str__(self):
        return (
            f"{self.ticket_id}_{self.__class__.__name__}, status: {self.str_status()}"
        )

    def link_to_pipeline(self, parent_pipeline: PipelineBase,
                         ticket_id: int) -> None:
        """ Secondary action, performed by Pipeline::add_order() """
        self.pipelene = parent_pipeline
        self.ticket_id = ticket_id
        self.logger.debug("Assgining ID: %s", str(ticket_id))

    def add_dependency(self, ticket_id: int) -> None:
        """ This ticket cannot be resolved until `ticket_id` is complete """
        self.logger.debug("add_dependency('%s')",
                          self.pipelene.who_is(ticket_id))
        if self.depends_on_list is None:
            self.depends_on_list = []
        self.depends_on_list.append(ticket_id)
        self.set_status(TicketStatus.BLOCKED)
        self.logger.debug("new status: %s", str(self))
        self.pipelene.book[ticket_id].assign_as_blocker(self.ticket_id)

    def remove_dependency(self, ticket_id: int) -> None:
        """ This ticket will no longer be dependant on `ticket_id`"""
        self.logger.debug("remove_dependency('%s')",
                          self.pipelene.who_is(ticket_id))
        if self.depends_on_list is None:
            raise Exception("depends_on is empty")
        elif ticket_id not in self.depends_on_list:
            raise Exception(f"{ticket_id} is not found " +
                            f"in the depends_on list: {self.depends_on_list}")
        else:
            self.depends_on_list.remove(ticket_id)
        if len(self.depends_on_list) == 0:
            self.set_status(TicketStatus.UNBLOCKED)

    def assign_as_blocker(self, ticket_id: int) -> None:
        """Mark this ticket as a blocker for `ticket_id`"""

        self.logger.debug("%s.assign_as_blocker(%s:'%s')",
                          self.pipelene.who_is(self.ticket_id), str(ticket_id),
                          self.pipelene.who_is(ticket_id))

        if self.blocks_whom_list is None:
            self.blocks_whom_list = []
        self.blocks_whom_list.append(ticket_id)
        self.pipelene.book[ticket_id].set_status(TicketStatus.BLOCKED)

    def mark_complete(self):
        """Mark order as complete"""
        self.set_status(TicketStatus.COMPLETED)
        self.resign_as_blocker()

    def mark_in_progress(self):
        """Mark order as in progress"""
        self.set_status(TicketStatus.IN_PROGRESS)

    def mark_invalid(self) -> None:
        "This ticket and ALL dependencies are now invalid"
        self.logger.debug("%s is declated invalid", str(self))
        self.set_status(TicketStatus.INVALID)

        if self.blocks_whom_list is not None:
            self.logger.debug("Invalidating dependancies")
            for blocked_ticket in self.blocks_whom_list:
                blocked_ticket.mark_invalid(self.ticket_id)
            # self.blocks_whom_list = []

    def resign_as_blocker(self) -> None:
        """Not a blocker anymore"""
        if self.blocks_whom_list is None:
            return
        self.logger.debug("%s.resign_as_blocker('%s')", str(self),
                          str(self.blocks_whom_list))
        for blocked_ticket in self.blocks_whom_list:
            blocked_ticket.remove_dependency(self.ticket_id)
        self.blocks_whom_list = []

    def str_ext(self):
        "Extended version of str(), includs dependencies and blockers"
        msg = str(self)
        if self.depends_on_list is not None:
            if len(self.depends_on_list) > 0:
                deps = [str(depends_on) for depends_on in self.depends_on_list]
            msg += f", depends on {deps}"

        if self.blocks_whom_list is not None:
            if len(self.blocks_whom_list) > 0:
                blocks = [
                    str(blocks_whom) for blocks_whom in self.blocks_whom_list
                ]
            msg += f", blocks {blocks}"

        return msg

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
