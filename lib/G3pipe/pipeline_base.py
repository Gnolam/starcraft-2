import logging
from lib.c01_obs_api import ObsAPI


class PipelineBase(ObsAPI):
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
        self.reset_promises()

    def run(self, obs):
        pass

    def add_order(self, new_ticket, blocks_whom_id: int = None):
        pass

    def reset_promises(self) -> None:
        self.new_building_made_promises = {}
        self.new_building_done_promises = {}

    def make_promise(self, promise_var: str) -> None:
        self.logger.debug(f"  Promise {promise_var}")
        self.new_building_made_promises[promise_var] = True

    def resolve_promise(self, promise_var: str) -> None:
        if promise_var in self.new_building_done_promises:
            if self.new_building_done_promises[promise_var]:
                self.logger.debug(
                    "  The promise has been already resolved earlier")
                return

        # Recently ticked promise
        self.logger.debug(f"  Declare resolved {promise_var}")
        self.new_building_done_promises[promise_var] = True

    def is_promised(self, promise_var: str) -> bool:
        if promise_var not in self.new_building_made_promises:
            # Create new record
            self.new_building_made_promises[promise_var] = False
            return False
        else:
            # Previous record located
            return self.new_building_made_promises[promise_var]