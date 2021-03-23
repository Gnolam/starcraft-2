class TicketStatus(object):
    # Constants
    INIT = 0
    ACTIVE = 1
    COMPLETE = 100
    BLOCKED = 200

    status_dict = {
        INIT: "INIT",
        ACTIVE: "ACTIVE",
        COMPLETE: "COMPLETE",
        BLOCKED: "BLOCKED"
    }

    current_status: int = None

    def __init__(self):
        super().__init__()
        print("~> TicketStatus::__init__()")

    # Functions
    def check_if_valid(self):
        if self.current_status is None:
            raise Exception("Use of unassigned status value")

    def str_status(self):
        self.check_if_valid()
        if self.current_status not in self.status_dict:
            raise Exception(f"Unknown status: {self.current_status}")
        return self.status_dict[self.current_status]

    def set_status(self, new_status):
        if new_status not in [
                self.INIT, self.ACTIVE, self.COMPLETE, self.BLOCKED
        ]:
            raise Exception(f"Unknown status: {new_status}")
        self.current_status = new_status

    def get_status(self):
        self.check_if_valid()
        return self.current_status
