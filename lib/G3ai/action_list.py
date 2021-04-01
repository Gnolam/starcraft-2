from lib.G3pipe.pipeline_orders import poTrainMarine


class BuildTicketsBase(object):
    """ this class is a base class for action containers"""
    # ToDo: populate from all functions in IssueOrder, starting with po_

    action_list = None

    def __init__(self, cfg=None):
        super().__init__()
        self.action_list = [
            method_name for method_name in dir(self) if method_name[:2] == 'pt'
        ]


class BuildTicketsEcon(BuildTicketsBase):
    def __init__(self, cfg=None):
        super().__init__()

    def pt_train_marines_2(self):
        return poTrainMarine(4)

    def pt_train_marines_4(self):
        return poTrainMarine(4)

    # def pt_train_marines_12(self):
    #     return poTrainMarine(12)

    # def pt_train_marines_16(self):
    #     return poTrainMarine(16)
