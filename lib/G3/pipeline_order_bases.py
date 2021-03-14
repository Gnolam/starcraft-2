import logging


class PipelineBase:
    '''
    Promise' class definition. Must not be called directly
    '''
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Init()")
        pass


class PipelineOrderBase(PipelineBase):
    '''
    Class to manage the execution of a single `PipelineOrder`'

    Contains the place holders for downstream classes
    '''

    order_id: int = None
    status: str = None
    depends_on = []

    parent_pipelene: PipelineBase = None

    class_name: str = 'NA'

    def __init__(self):
        super().__init__()

    def __str__(self):
        self.logger.debug(f"Hi from '{self.__class__.__name__}'")

    def link_to_pipeline(self, parent_pipeline: PipelineBase, order_id: int):
        self.parent_pipelene = parent_pipeline
        self.order_id = order_id
        self.logger.debug(
            f"Assgining ID:'{order_id}' received from '{parent_pipeline.__class__.__name__}'"
        )
        pass

    def is_complete(self) -> bool:
        '''
        Placehoder. returns true if the order is complete
        '''
        pass

    def run(self):
        '''
        try to execute, add new orders and depenedncies later on
        '''
        pass
