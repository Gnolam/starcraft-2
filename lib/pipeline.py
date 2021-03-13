class PipelineBase:
    # 'Promise' definition
    def __init__(self):
        pass


#----------------------------------------------------------


class PipelineOrder:
    '''
    Class to manage the execution of a single `PipelineOrder`'

    Contains the place holders for downstream classes
    '''

    order_number: int = None
    status: str = None
    depends_on = []

    parent_pipelene: PipelineBase = None

    def __init__(self, parent_pipeline: PipelineBase):
        '''
        To be called by either
        '''
        self.parent_pipelene = parent_pipeline
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


#----------------------------------------------------------


class poBuildBarracks(PipelineOrder):
    def __init__(self, parent_pipeline: PipelineBase):
        '''
        Checks the presence
        '''
        super().__init__(parent_pipeline)
        self.parent_pipelene.add_order(PipelineOrder(parent_pipeline))
        pass


class poAddMariners(PipelineOrder):
    def __init__(self, parent_pipeline: PipelineBase, number_of_mariners: int):
        '''
        Checks the presence
        '''
        super().__init__(parent_pipeline)
        self.parent_pipelene.add_order(poBuildBarracks(parent_pipeline))
        pass


#----------------------------------------------------------


class Pipeline(PipelineBase):
    '''
    Class to manage the set of current `PipelineOrder`'s
    '''
    pipeline = []

    def add_order(self, order: PipelineOrder):
        self.pipeline.append(order)
        pass

    def remove_order(self, order_id: int):
        # ToDo: check that there are no other orders, which have this order as dependency
        pass

    def run(self):
        '''
            Run

            runs the
        '''
        pass
