from lib.G3.pipeline_order_bases import PipelineOrderBase


class poBuildBarracks(PipelineOrderBase):
    def __init__(self):
        '''
        ???
        '''
        super().__init__()
        pass


class poBuildMariners(PipelineOrderBase):
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
        bk2 = poBuildBarracks()
        self.add_dependency(self.parent_pipelene.add_order(bk1))
        self.add_dependency(self.parent_pipelene.add_order(bk2))

        bk1.assign_as_blocker(self.my_order_id)
        bk2.assign_as_blocker(self.my_order_id)

        self.status = self.status_blocked

        if self.status == self.status_complete:
            return {'New actions created': False, 'SC2 order assigned': None}
        return {'New actions created': True, 'SC2 order assigned': None}
