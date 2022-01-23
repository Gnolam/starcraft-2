from lib.c01_obs_api import ObsAPI


class TicketStatus(ObsAPI):
    # Constants
    OPENED = 2
    REQUESTED = 100
    IN_PROGRESS = 120
    COMPLETED = 150
    BLOCKED = 200
    INVALID = 400

    status_dict = {
        None: "N/A",
        OPENED: "OPENED",  #           Ticket is NOT blocked
        REQUESTED: "REQUESTED",  #     Build order was issued
        IN_PROGRESS: "IN_PROGRESS",  # Ticket is confirmed to start building
        COMPLETED: "COMPLETED",  #     Ticket was finished (for debug)
        BLOCKED: "BLOCKED",
        INVALID: "INVALID"
    }

    # Variables
    id: int = None
    current_status: int = None
    status_already_issued: bool = None

    def __init__(self):
        super().__init__()
        self.status_already_issued = False

    def check_if_valid(self):
        if self.current_status is None:
            raise Exception("Use of unassigned status value")
        if self.current_status not in self.status_dict:
            raise Exception(f"Unknown status: {self.current_status}")

    def str_status(self):
        self.check_if_valid()
        suffix = ""
        if self.is_alredy_issued():
            suffix += " (issued)"
        return self.status_dict[self.current_status]

    def mark_opened(self):
        self.set_status(self.OPENED)

    def is_opened(self):
        return self.get_status() == self.OPENED

    def mark_complete(self):
        self.set_status(self.COMPLETED)

    def is_completed(self):
        return self.get_status() == self.COMPLETED

    def mark_in_progress(self):
        self.set_status(self.IN_PROGRESS)

    def is_in_progress(self):
        return self.get_status() == self.IN_PROGRESS

    def mark_requested(self):
        self.set_status(self.REQUESTED)

    def is_requested(self):
        return self.get_status() == self.REQUESTED

    def mark_blocked(self):
        self.set_status(self.BLOCKED)

    def is_blocked(self):
        return self.get_status() == self.BLOCKED

    def mark_invalid(self):
        self.set_status(self.INVALID)

    def is_invalid(self):
        return self.get_status() == self.INVALID

    def set_status(self, new_status):
        if new_status is None:
            raise Exception(f"Cannot assign None status")
        if new_status not in [
                self.OPENED, self.IN_PROGRESS, self.BLOCKED, self.INVALID,
                self.REQUESTED, self.COMPLETED
        ]:
            raise Exception(f"Unknown new status: {new_status}")
        self.logger.debug(
            f"  Status for '{self.id}_{self.__class__.__name__}': " +
            f"'{self.status_dict[self.current_status]}' -> " +
            f"'{self.status_dict[new_status]}'")
        self.current_status = new_status

    def get_status(self):
        self.check_if_valid()
        return self.current_status

    def mark_as_issued(self) -> None:
        self.status_already_issued = True

    def is_alredy_issued(self) -> bool:
        return self.status_already_issued
