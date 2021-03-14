from lib.pipeline_order_bases import PipelineBase, PipelineOrderBase


class Pipeline(PipelineBase):
    '''
    Class to manage the set of current `PipelineOrder`'s
    '''
    pipeline = []

    def __init__(self):
        print(f"{self.__class__.__name__}::Init()")

    def add_order(self, order: PipelineOrderBase):
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
