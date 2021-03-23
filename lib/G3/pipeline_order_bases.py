import logging
from lib.ticket_status import TicketStatus
from lib.c01_obs_api import ObsAPI


class PipelineConventions(object):
    """ Joint class parent for Pipeline and Orders """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Created")
        print("~> PipelineConventions::__init__()")


# ------------------------------------------------------------------------


class PipelineBase(PipelineConventions):
    """
    Promise' class definition. Must not be called directly.
    Parent class for `Pipeline`
    """
    book = []  # Tickets

    def add_order(self, new_ticket, blocks_whom_id: int = None):
        pass


# ------------------------------------------------------------------------


class PipelineTicketBase(TicketStatus, ObsAPI, PipelineConventions):
    '''
    Class to manage the execution of a single `PipelineTicket`'
    Contains the place holders for downstream classes
    '''

    ID: int = None
    # status: int = None
    depends_on_list = None
    blocks_whom_id: int = None
    parent_pipelene: PipelineBase = None

    # Should be set
    base_top_left: bool = None
    is_order_issued: bool = False

    def __init__(self):
        super().__init__()
        self.logger.debug(f"Creating '{self.__class__.__name__}'")

    def __str__(self):
        extra_info = ""
        if self.depends_on_list is not None:
            if (len(self.depends_on_list)):
                deps = [
                    self.parent_pipelene.who_is(depends_on)
                    for depends_on in self.depends_on_list
                ]
                extra_info += f", depends on {deps}"

        if self.blocks_whom_id is not None:
            extra_info += (
                ", blocks " +
                f"{self.parent_pipelene.who_is(self.blocks_whom_id)}'")
        return f"'{self.__class__.__name__}', status: {self.str_status()}" + extra_info

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
        if self.depends_on_list is None:
            self.depends_on_list = []
        self.depends_on_list.append(ticket_id)

    def remove_dependency(self, ticket_id: int) -> None:
        # ToDo: Verify first that such element exists
        self.logger.debug(
            f"remove_dependency('{self.parent_pipelene.who_is(ticket_id)}')")
        if self.depends_on_list is None:
            raise Exception("depends_on is empty")
        elif ticket_id not in self.depends_on_list:
            raise Exception(f"{ticket_id} is not found " +
                            f"in the depends_on list: {self.depends_on_list}")
        else:
            self.depends_on_list.remove(ticket_id)

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
        self.set_status(TicketStatus.COMPLETE)

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
        if len(blocked_order.depends_on_list) == 0:
            blocked_order.set_status(TicketStatus.ACTIVE)

        # Assume only 1 order can be blocked relationsip
        self.blocks_whom_id = None

    def generate_sc2_order(self, obs):
        """ Helps isolating logic for placing an order
        
        All preconditions must be held in `self.run()`. 
        Should be called from `self.run()`

        Returns: pysc2.lib - actions
        """
        err_msg = 'This method should not be called directly. It is a placeholder only'
        self.logger.error(err_msg)
        raise Exception(f"{self.__class__.__name__}::run(): {err_msg}")

    def run_init(self, obs):
        """ Checks the preconditions and creates downstream tickets.
        Can be left empty if no action is required
        """
        pass

    def run(self, obs):
        '''try to execute, add new orders and depenedncies later on

            : obs : SC2 obs (observation) object

                    - Check if all conditions are fulfilled.
                    - Should handle the situation where previously submitted
                        order (e.g. build supply depos building) was requested
                        but may have not been fulfilled
                    - should issue SC2 Orders
                    - should wait till the order is executed before
                      * reporting complete -> removing upward dependencies

        '# ToDo: make sure that if 'complete' then the dependency is removed

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
        # return None
        # if self.get_status() == TicketStatus.DONE:
        #     return {'New actions created': False, 'SC2 order assigned': None}

        err_msg = 'This method should not be called directly. It is a placeholder only'
        self.logger.error(err_msg)
        raise Exception(f"{self.__class__.__name__}::run(): {err_msg}")
