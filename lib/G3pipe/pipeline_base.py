import logging
from lib.c01_obs_api import ObsAPI


class PipelineConventions(ObsAPI):
    """ Joint class parent for Pipeline and Orders """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Created <PipelineConventions>")


# ------------------------------------------------------------------------


class PipelineBase(PipelineConventions):
    """
    Promise class definition. Must not be called directly.
    Parent class for `Pipeline`
    """
    book: list = None  # Tickets
    new_building_metadata: dict = None
    new_building_made_promises: dict = None
    new_building_done_promises: dict = None
    order_counter: int = None
    base_top_left: bool = None

    def __init__(self):
        super().__init__()
        self.order_counter = 0
        self.book = []
        self.new_building_metadata = {}
        self.new_building_made_promises = {}
        self.new_building_done_promises = {}

    def add_order(self, new_ticket, blocks_whom_id: int = None):
        pass
