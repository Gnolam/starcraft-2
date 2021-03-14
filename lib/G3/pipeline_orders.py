from lib.G3.pipeline_order_bases import PipelineOrderBase


class poBuildBarracks(PipelineOrderBase):
    def __init__(self):
        '''
        ???
        '''
        super().__init__()
        pass


class poAddMariners(PipelineOrderBase):
    number_of_mariners_to_produce: int = None

    def __init__(self, number_of_mariners: int):
        '''
        ???
        '''
        super().__init__()
        self.number_of_mariners_to_produce = number_of_mariners
        pass
