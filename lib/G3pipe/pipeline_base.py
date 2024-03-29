import logging
from lib.c01_obs_api import ObsAPI


class PipelineConventions(ObsAPI):
    """ Joint class parent for Pipeline and Orders """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)


# ------------------------------------------------------------------------


class PipelineBase(PipelineConventions):
    """
    Promise class definition. Must not be called directly.
    Parent class for `Pipeline`
    """
    book: list = None  # Tickets
    new_building_made_promises: dict = None
    new_building_done_promises: dict = None
    order_counter: int = None
    base_top_left: bool = None

    def __init__(self):
        super().__init__()
        self.order_counter = 0
        self.book = []
        self.new_building_made_promises = {}
        self.new_building_done_promises = {}

    def run(self, obs):
        pass

    def add_order(self, new_ticket, blocks_whom_id: int = None):
        pass

    def promise_make(self, promise_var: str) -> None:
        self.logger.debug(f"  Promise {promise_var}")
        self.new_building_made_promises[promise_var] = True

    def promise_resolve(self, promise_var: str) -> None:
        # It was already True
        if promise_var in self.new_building_done_promises:
            if self.new_building_done_promises[promise_var]:
                return
        # Recently ticked promise
        self.logger.debug(f"  Declare resolved {promise_var}")
        self.new_building_done_promises[promise_var] = True

    def promise_check(self, promise_var: str) -> bool:
        if promise_var not in self.new_building_made_promises:
            # Create new record
            self.new_building_made_promises[promise_var] = False
            # self.logger.debug(f"  init '{promise_var}' -> False")
            return False
        else:
            # Previous record located
            return self.new_building_made_promises[promise_var]