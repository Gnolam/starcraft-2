class TicketStatus:
    # Constants
    INIT = 0
    ACTIVE = 1
    DONE = 100
    BLOCKED = 200

    current_status: int = None

    # Functions
    def check_if_valid(self):
        if self.current_status is None:
            raise Exception("Use of unassigned status value")

    def str_status(self):
        self.check_if_valid()
        if self.current_status == self.INIT:
            return "INIT"
        if self.current_status == self.ACTIVE:
            return "ACTIVE"
        if self.current_status == self.DONE:
            return "DONE"
        if self.current_status == self.BLOCKED:
            return "BLOCKED"
        raise Exception(f"Unknown status: {self.current_status}")

    def set_status(self, new_status):
        if new_status not in [self.INIT, self.ACTIVE, self.DONE, self.BLOCKED]:
            raise Exception(f"Unknown status: {new_status}")
        self.current_status = new_status

    def get_status(self):
        self.check_if_valid()
        return self.current_status
