import logging
from lib.c01_obs_api import ObsAPI


class PipelineConventions(object):
    """ Joint class parent for Pipeline and Orders """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Created <PipelineConventions>")


# ------------------------------------------------------------------------


class PipelineBase(PipelineConventions):
    """
    Promise' class definition. Must not be called directly.
    Parent class for `Pipeline`
    """
    book = []  # Tickets

    def add_order(self, new_ticket, blocks_whom_id: int = None):
        pass
