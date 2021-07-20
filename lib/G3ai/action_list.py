from lib.G3pipe.pipeline_orders import poTrainMarine


class ActionListBase(object):
    """ this class is a base class for action containers"""

    action_list = None

    def __init__(self, cfg=None):
        """ populate from all functions in IssueOrder, starting with pt_: 'pipeline ticket'  """
        super().__init__()
        self.action_list = [
            method_name for method_name in dir(self) if method_name[:2] == 'pt'
        ]


class BuildTicketsEcon(ActionListBase):
    def __init__(self, cfg=None):
        super().__init__()

    def pt_train_marines_2(self):
        return poTrainMarine(2)

    def pt_train_marines_4(self):
        return poTrainMarine(4)

    # def pt_train_marines_12(self):
    #     return poTrainMarine(12)

    # def pt_train_marines_16(self):
    #     return poTrainMarine(16)