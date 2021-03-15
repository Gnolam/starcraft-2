import logging
from lib.G3.pipeline_order_bases import PipelineBase, PipelineTicketBase


class Pipeline(PipelineBase):
    '''
    Class to manage the set of current `PipelineTicket`'s
    '''
    order_counter: int = None

    def __init__(self):
        super().__init__()
        self.order_counter = -1

    def add_order(self, order: PipelineTicketBase) -> int:
        '''
        Adds order to the pipeline and assigns it an order ID
        '''
        self.order_counter += 1
        self.logger.info(
            f"Adding '{order.__class__.__name__ }' to pipeline. ID:{self.order_counter}"
        )
        self.pipeline.append({'ID': self.order_counter, 'Order': order})
        order.link_to_pipeline(parent_pipeline=self,
                               order_id=self.order_counter)
        return self.order_counter

    def is_empty(self) -> bool:
        '''
        Returns True if current pipeline has all orders 'COMPLETE'
        '''
        pass

    def who_is(self, order_id: int) -> str:
        return self.pipeline[order_id]["Order"].__class__.__name__

    def run(self):
        '''Scans: through all the orders in the book and tries to run those, which are active

        '''
        pass

    def talk(self):
        print(f"Hi from '{self.__class__.__name__}'")

    def __str__(self):
        ret = "  Current content of the pipeline gross book:\n    " + "-" * 40
        for ticket in self.pipeline:
            ID = ticket['ID']
            cur_order = ticket['Order']
            ret += f"\n    ID:{ID}, {str(cur_order)}"
        return ret