import logging


class PipelineConventions:
    '''
    Joint class parent for Pipeline and Orders
    '''
    status_complete = "COMPLETE"
    status_init = "INIT"
    status_ready = "READY"
    status_blocked = "BLOCKED"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Created")
        pass


# ------------------------------------------------------------------------


class PipelineBase(PipelineConventions):
    '''
    Promise' class definition. Must not be called directly.
    Parent class for `Pipeline`
    '''
    def add_order(self, order):
        pass


# ------------------------------------------------------------------------


class PipelineOrderBase(PipelineConventions):
    '''
    Class to manage the execution of a single `PipelineOrder`'

    Contains the place holders for downstream classes
    '''

    my_order_id: int = None
    status: str = None
    depends_on = None
    blocks_whom_id: int = None
    parent_pipelene: PipelineBase = None

    def __init__(self):
        super().__init__()
        self.status = self.status_init

    def __str__(self):
        extra_info = ""
        if self.depends_on is not None:
            if (len(self.depends_on)):
                extra_info += f", depends on '{self.depends_on}'"

        if self.blocks_whom_id is not None:
            extra_info += f", blocks '{self.blocks_whom_id}'"
        return f"'{self.__class__.__name__}', status: {self.status}" + extra_info

    def link_to_pipeline(self, parent_pipeline: PipelineBase,
                         order_id: int) -> None:
        '''
        Secondary action, performed by Pipeline::add_order()
        '''
        self.parent_pipelene = parent_pipeline
        self.my_order_id = order_id
        self.logger.debug(
            f"Assgining ID:'{order_id}' received from '{parent_pipeline.__class__.__name__}'"
        )

    def is_complete(self) -> bool:
        return True if self.status == self.status_complete else False

    def add_dependency(self, order_id: int) -> None:

        self.logger.debug(
            f"add_dependency({order_id}:'{self.parent_pipelene.who_is(order_id)}')"
        )
        if self.depends_on is None:
            self.depends_on = []
        self.depends_on.append(order_id)

    def remove_dependency(self, order_id: int) -> None:
        # ToDo: Verify first that such element exists
        self.logger.debug(
            f"remove_dependency({order_id}:'{self.parent_pipelene.who_is(order_id)}')"
        )
        if self.depends_on is None:
            raise Exception("No dependency is recorded")
        self.depends_on.remove(order_id)

    def assign_as_blocker(self, order_id: int) -> None:
        self.logger.debug(
            f"assign_as_blocker({order_id}:'{self.parent_pipelene.who_is(order_id)}')"
        )
        self.blocks_whom_id = order_id

    def resign_as_blocker(self) -> None:
        self.logger.debug(
            f"resign_as_blocker() (hint:blocks_whom_id={self.blocks_whom_id}:"
            + f"'{self.parent_pipelene.who_is(self.blocks_whom_id)}')")
        if self.blocks_whom_id is None:
            raise Exception("No blocked ID is specified")

        # ToDo: should be search by match with ID in dict
        blocked_order = self.parent_pipelene.pipeline[
            self.blocks_whom_id]['Order']
        blocked_order.remove_dependency(self.my_order_id)

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
