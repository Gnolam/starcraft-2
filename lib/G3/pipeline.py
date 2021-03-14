import logging
from lib.G3.pipeline_order_bases import PipelineBase, PipelineOrderBase


class Pipeline(PipelineBase):
    '''
    Class to manage the set of current `PipelineOrder`'s
    '''
    pipeline = []
    order_counter: int = None

    def __init__(self):
        super().__init__()
        self.order_counter = 0

    def add_order(self, order: PipelineOrderBase) -> int:
        '''
        Adds order to the pipeline and assigns it an order ID
        '''
        self.order_counter += 1
        self.logger.info(
            f"Adding '{order.__class__.__name__ }' to pipeline. ID:{self.order_counter}"
        )
        order.link_to_pipeline(parent_pipeline=self,
                               order_id=self.order_counter)
        return self.order_counter

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
