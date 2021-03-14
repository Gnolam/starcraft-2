from lib.G3.pipeline_order_bases import PipelineOrderBase


class poBuildBarracks(PipelineOrderBase):
    def __init__(self):
        '''
        ???
        '''
        super().__init__()
        pass


class poBuildMariners(PipelineOrderBase):
    number_of_mariners_to_build: int = None

    def __init__(self, number_of_mariners_to_build: int):
        '''
        ???
        '''
        super().__init__()
        self.number_of_mariners_to_build = number_of_mariners_to_build
        pass
