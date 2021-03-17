import logging


class PipelineConventions:
    """ Joint class parent for Pipeline and Orders """
    status_ready = "READY"
    status_blocked = "BLOCKED"
    status_complete = "COMPLETE"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Created")
        pass


# ------------------------------------------------------------------------


class PipelineBase(PipelineConventions):
    """
    Promise' class definition. Must not be called directly.
    Parent class for `Pipeline`
    """
    book = []  # Tickets

    def add_order(self, new_ticket):
        pass


# ------------------------------------------------------------------------


class PipelineTicketBase(PipelineConventions):
    '''
    Class to manage the execution of a single `PipelineTicket`'
    Contains the place holders for downstream classes
    '''

    ID: int = None
    status: str = None
    depends_on = None
    blocks_whom_id: int = None
    parent_pipelene: PipelineBase = None

    def __init__(self):
        super().__init__()
        self.status = self.status_ready

    def __str__(self):
        extra_info = ""
        if self.depends_on is not None:
            if (len(self.depends_on)):
                extra_info += f", depends on '{self.depends_on}'"

        if self.blocks_whom_id is not None:
            extra_info += (
                ", blocks " +
                f"{self.parent_pipelene.who_is(self.blocks_whom_id)}'")
        return f"'{self.__class__.__name__}', status: {self.status}" + extra_info

    def link_to_pipeline(self, parent_pipeline: PipelineBase,
                         ticket_id: int) -> None:
        """ Secondary action, performed by Pipeline::add_order() """
        self.parent_pipelene = parent_pipeline
        self.ID = ticket_id
        self.logger.debug(
            f"Assgining ID:'{ticket_id}' received from '{parent_pipeline.__class__.__name__}'"
        )

    # def is_complete(self) -> bool:
    #     return True if self.status == self.status_complete else False

    def add_dependency(self, ticket_id: int) -> None:
        """ This ticket cannot be resolved until `ticket_id` is complete """
        self.logger.debug(
            f"add_dependency('{self.parent_pipelene.who_is(ticket_id)}')")
        if self.depends_on is None:
            self.depends_on = []
        self.depends_on.append(ticket_id)

    def remove_dependency(self, ticket_id: int) -> None:
        # ToDo: Verify first that such element exists
        self.logger.debug(
            f"remove_dependency('{self.parent_pipelene.who_is(ticket_id)}')")
        if self.depends_on is None:
            raise Exception("depends_on is empty")
        elif ticket_id not in self.depends_on:
            raise Exception(f"{ticket_id} is not found " +
                            f"in the depends_on list: {self.depends_on}")
        else:
            self.depends_on.remove(ticket_id)

    def assign_as_blocker(self, ticket_id: int) -> None:
        self.logger.debug(f"assign_as_blocker({ticket_id}:" +
                          f"'{self.parent_pipelene.who_is(ticket_id)}')")
        if self.blocks_whom_id is not None:
            raise Exception(
                "Cannot assign block. Ticket is already blocking " +
                f"'{self.parent_pipelene.who_is(self.blocks_whom_id)}'")
        self.blocks_whom_id = ticket_id

    def mark_complete(self):
        if self.blocks_whom_id is None:
            self.resign_as_blocker()
        self.status = self.status_complete

    def resign_as_blocker(self) -> None:
        if self.blocks_whom_id is None:
            raise Exception("resign_as_blocker(): No blocked ID is specified")
        self.logger.debug(
            f"resign_as_blocker() (" +
            f"'{self.parent_pipelene.who_is(self.blocks_whom_id)}')")

        # ToDo: should be search by match with ID in dict
        blocked_order = self.parent_pipelene.book[self.blocks_whom_id]
        blocked_order.remove_dependency(self.ID)

        # Check if this item was the last blocker
        if len(blocked_order.depends_on) == 0:
            blocked_order.status = self.status_ready

        # Assume only 1 order can be blocked relationsip
        self.blocks_whom_id = None

    def run(self, obs):
        '''try to execute, add new orders and depenedncies later on

        Return: dictionary
        - _SC2 order assigned_:
          - `None`: no SC2 orders
          - `pysc2.lib.actions`: an order to be executed
        - *New actions created*: indicates that pipeline should be re-scanned

                ``asx``: __ghghg__
        '''
        if self.status == self.status_complete:
            return {'New actions created': False, 'SC2 order assigned': None}

        err_msg = 'This method should not be called directly. It is a placeholder only'
        self.logger.error(err_msg)
        raise Exception(f"{self.__class__.__name__}::run(): {err_msg}")
