from lib.G3pipe.pipeline_base import PipelineConventions


class TicketStatus(PipelineConventions):
    # Constants
    ACTIVE = 2
    COMPLETE = 100
    BLOCKED = 200
    INVALID = 400

    status_dict = {
        None: "N/A",
        ACTIVE: "ACTIVE",
        COMPLETE: "COMPLETE",
        BLOCKED: "BLOCKED",
        INVALID: "INVALID"
    }

    # Variables
    ID: int = None
    current_status: int = None

    def __init__(self):
        super().__init__()

    def check_if_valid(self):
        if self.current_status is None:
            raise Exception("Use of unassigned status value")
        if self.current_status not in self.status_dict:
            raise Exception(f"Unknown status: {self.current_status}")

    def str_status(self):
        self.check_if_valid()
        return self.status_dict[self.current_status]

    def set_status(self, new_status):
        if new_status is None:
            raise Exception(f"Cannot assign None status")
        if new_status not in [
                self.ACTIVE, self.COMPLETE, self.BLOCKED, self.INVALID
        ]:
            raise Exception(f"Unknown new status: {new_status}")
        self.logger.debug(f"'{self.ID}_{self.__class__.__name__}': " +
                          "Changing status '" +
                          self.status_dict[self.current_status] + "' -> '" +
                          self.status_dict[new_status] + "'")
        self.current_status = new_status

    def get_status(self):
        self.check_if_valid()
        return self.current_status

    def status_is_active(self):
        return self.get_status() == self.ACTIVE
