import logging


class PipelineBase:
    '''
    Promise' class definition. Must not be called directly
    '''
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Created")
        pass


class PipelineOrderBase(PipelineBase):
    '''
    Class to manage the execution of a single `PipelineOrder`'

    Contains the place holders for downstream classes
    '''

    status_complete = "COMPLETE"
    status_init = "INIT"
    status_blocked = "BLOCKED"

    order_id: int = None
    status: str = None
    depends_on = []

    parent_pipelene: PipelineBase = None

    class_name: str = 'NA'

    def __init__(self):
        super().__init__()

    def __str__(self):
        self.logger.debug(f"Hi from '{self.__class__.__name__}'")

    def link_to_pipeline(self, parent_pipeline: PipelineBase,
                         order_id: int) -> None:
        '''
        Secondary action, performed by Pipeline::add_order()
        '''
        self.parent_pipelene = parent_pipeline
        self.order_id = order_id
        self.logger.debug(
            f"Assgining ID:'{order_id}' received from '{parent_pipeline.__class__.__name__}'"
        )

    def is_complete(self) -> bool:
        return True if self.status == self.status_complete else False

    def run(self):
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
        pass
