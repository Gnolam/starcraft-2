from lib.G3pipe.pipeline_orders import poTrainMarine, poAccumulateReserve, poGenTransferReserve


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
    """ a class containing the list of orders for the builder AI """
    def __init__(self, cfg=None):
        super().__init__()

    def pt_train_marines_2(self):
        return poTrainMarine(2)

    def pt_train_marines_4(self):
        return poTrainMarine(4)


class BuildTicketsWar(ActionListBase):

    fn_transfer_to_TF1 = None
    """ a class containing the list of orders for the General AI """
    def __init__(self, cfg=None):
        super().__init__()

    def pt_Gen_accumulate_reserve(self):
        return poAccumulateReserve()

    def pt_Gen_transfer_reserve(self):
        if self.fn_transfer_to_TF1 is None:
            raise Exception("fn_transfer_to_TF1 is not defined")
        return poGenTransferReserve(self.fn_transfer_to_TF1)

    def test_fn_transfer_to_TF1(self):
        if self.fn_transfer_to_TF1 is None:
            raise Exception("test: fn_transfer_to_TF1 is not defined")
