from lib.c01_obs_api import ObsAPI


class PipelineBase(ObsAPI):
    """
    Promise class definition. Must not be called directly.
    Parent class for `Pipeline`
    """
    book: list = None  # Tickets
    order_counter: int = None
    base_top_left: bool = None

    def __init__(self):
        super().__init__()
        self.order_counter = 0
        self.book = []

    def run(self, obs):
        pass

    def add_order(self, new_ticket, blocks_whom_id: int = None):
        pass
