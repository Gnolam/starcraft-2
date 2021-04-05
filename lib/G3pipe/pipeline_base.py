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
    promise_supply_depot: bool = False

    def add_order(self, new_ticket, blocks_whom_id: int = None):
        pass
