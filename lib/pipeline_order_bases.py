class PipelineBase:
    # 'Promise' definition
    def __init__(self):
        pass

# ----------------------------------------------------------------------------


class PipelineOrderBase:
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

    def talk(self):
        print(f"Hi from '{self.__class__.__name__}'")

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
