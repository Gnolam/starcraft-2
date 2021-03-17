from lib.G3.pipeline_order_bases import PipelineTicketBase


class poWaitResourceMinerals(PipelineTicketBase):
    def __init__(self, minerals_required: int):
        super().__init__()
        self.minerals_required = minerals_required

    def run(self, obs):
        # If minerals are available
        # then remove blocker and
        self.mark_complete()
        pass


class poBuildBarracks(PipelineTicketBase):
    def __init__(self):
        '''
        ???
        '''
        super().__init__()
        pass


class poBuildMariners(PipelineTicketBase):
    number_of_mariners_to_build: int = None

    def __init__(self, number_of_mariners_to_build: int):
        super().__init__()
        self.number_of_mariners_to_build = number_of_mariners_to_build

    def __str__(self):
        s = super().__str__()
        return s + f", {self.number_of_mariners_to_build} marines to build"

    def run(self, obs):
        self.logger.debug(f"~> Let's do something")
        bk1 = poBuildBarracks()
        minerals = poWaitResourceMinerals(50)
        self.add_dependency(self.parent_pipelene.add_order(bk1))
        self.add_dependency(self.parent_pipelene.add_order(minerals))

        bk1.assign_as_blocker(self.ID)
        minerals.assign_as_blocker(self.ID)

        self.status = self.status_blocked

        if self.status == self.status_complete:
            return {'New actions created': False, 'SC2 order assigned': None}
        return {'New actions created': True, 'SC2 order assigned': None}
