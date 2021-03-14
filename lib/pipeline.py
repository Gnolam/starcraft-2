class PipelineBase:
    # 'Promise' definition
    def __init__(self):
        pass


# ----------------------------------------------------------------------------


class PipelineOrder:
    '''
    Class to manage the execution of a single `PipelineOrder`'

    Contains the place holders for downstream classes
    '''

    order_number: int = None
    status: str = None
    depends_on = []

    parent_pipelene: PipelineBase = None

    def __init__(self):
        '''
        To be called by either
        '''
        print(f"{self.__class__.__name__}::Init()")
        pass

    def link_to_pipeline(self, parent_pipeline: PipelineBase):
        self.parent_pipelene = parent_pipeline
        print(f"{self.__class__.__name__}::link() to " +
              parent_pipeline.__class__.__name__)
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


# ----------------------------------------------------------------------------


class poBuildBarracks(PipelineOrder):
    def __init__(self):
        '''
        Checks the presence
        '''
        super().__init__()
        pass


class poAddMariners(PipelineOrder):
    number_of_mariners_to_produce: int = None

    def __init__(self, number_of_mariners: int):
        '''
        Checks the presence
        '''
        super().__init__()
        self.number_of_mariners_to_produce = number_of_mariners
        # self.parent_pipelene.add_order(poBuildBarracks(parent_pipeline))
        pass


# ----------------------------------------------------------------------------


class Pipeline(PipelineBase):
    '''
    Class to manage the set of current `PipelineOrder`'s
    '''
    pipeline = []

    def __init__(self):
        print(f"{self.__class__.__name__}::Init()")

    def add_order(self, order: PipelineOrder):
        print(f"{self.__class__.__name__}::add_order() is adding '" +
              order.__class__.__name__ + "'")
        self.pipeline.append(order)
        order.link_to_pipeline(self)
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

    def talk(self):
        print(f"Hi from '{self.__class__.__name__}'")
