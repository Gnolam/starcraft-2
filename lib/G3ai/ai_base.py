import os
import logging

import pandas as pd
from pysc2.lib import units

from lib.q_table import QLearningTable
from lib.c01_obs_api import ObsAPI
from lib.G3pipe.pipeline import Pipeline


class aiBase(ObsAPI):
    agent_name = "L1"
    action_list = []
    action_container_class = None
    DQN_filename = None
    fh_decisions = None
    fh_state_csv = None
    fn_global_debug = None
    consistent_decision_agent = None
    logger = None
    decisions_hist = {}
    step_counter = 0
    game_num = None
    current_action = None
    DQN_log_suffix = None

    pipeline: Pipeline = None

    def __init__(self, cfg):
        super().__init__()
        self.logger = logging.getLogger(self.agent_name)
        self.logger.info(f"L1.init({self.agent_name})")

        self.cfg = cfg
        self.qtable = QLearningTable(actions=self.action_list,
                                     log_suffix=self.DQN_log_suffix)

        self.DQN_filename,\
            self.fh_decisions,\
            self.fh_state_csv,\
            self.fn_global_debug,\
            self.fn_global_state =\
            cfg.get_filenames(self.agent_name)

        self.read_global_state()
        self.new_game()

        self.logger.debug(f"Run number: {self.game_num}")

    def reset(self):
        self.logger.debug("reset()")
        self.new_game()

    def read_global_state(self):
        global_state = self.cfg.read_yaml_file(self.fn_global_state)
        self.game_num = int(global_state["run_number"])

    def save_global_state(self):
        self.cfg.write_yaml_file(self.fn_global_state,
                                 dict(run_number=self.game_num))

    def get_state(self, dummy):
        # This function is a place holder
        if 1 >= 1:
            self.logger.critical(
                'Incorrect function was called: L1::get_state()')
            raise Exception('Incorrect function was called: L1::get_state()')

    def new_game(self):
        self.logger.debug(f"new_game()")
        self.previous_state = None
        self.previous_action = None

        # Creating generic pipeline
        self.pipeline = Pipeline()

        # History of decisions for future discounting
        self.decisions_hist = {}
        self.step_counter = 0
        self.game_num += 1

    def save_DQN(self):
        self.logger.debug(f"save_DQN()")
        self.logger.debug('Record current learnings (%s): %s' %
                          (self.agent_name, self.DQN_filename))
        self.qtable.q_table.to_pickle(self.DQN_filename, 'gzip')

    def load_DQN(self):
        if os.path.isfile(self.DQN_filename):
            self.logger.info('Load previous learnings (%s)' % self.agent_name)
            self.qtable.q_table = pd.read_pickle(self.DQN_filename,
                                                 compression='gzip')
        else:
            self.logger.info('NO previous learnings located (%s)' %
                             self.agent_name)

    def log_state(self, s_message, should_print=True):
        if should_print and self.fh_state_csv is not None:
            self.fh_state_csv.write(s_message)

    def choose_next_action(self, obs) -> None:
        """ Picks the next action and updates the pipeline """
        state = str(self.get_state(obs))

        # Original 'best known' action based on Q-Table
        action, best_score = self.qtable.choose_action(state)
        self.logger.debug(f"Q-Action: '{action.upper()}'" +
                          f", score = '{best_score}'")

        next_state = 'terminal' if obs.last() else state

        # 'LEARN' should be across the WHOLE history
        # Q-Table should be updated to consume 'batch' history
        # Record decision for later 'batch' learning
        if self.previous_action is not None:
            self.decisions_hist[self.step_counter] = {
                'previous_state': self.previous_state,
                'previous_action': self.previous_action,
                'next_state': next_state
            }

        self.step_counter += 1
        self.previous_state = state
        self.previous_action = action

        self.logger.debug(
            f"step counter: {self.step_counter}, size of history: {len(self.decisions_hist)}"
        )

        if not obs.last():
            # Convert action:str -> new_ticket:PipelineTicket
            new_ticket = getattr(self, action)()
            # Add this new_ticket:PipelineTicket to pipeline
            self.pipeline.add_order(new_ticket)

    def step(self, obs):
        """ Core function to respond to game changes
        1. updates pipeline with new tickets if empty
        2. tries to resolve pipeline tickets

        Returns: tuple (order, )
            * SC2 order: issued by ticket in pipeline
            * None: if still waiting
        """

        self.logger.debug(f"{self.agent_name}: step()")

        if obs.first():
            self.logger.debug(f"SCP100: first observation")
            command_centres = self.get_my_units_by_type(
                obs, units.Terran.CommandCenter)
            self.pipeline.base_top_left = (command_centres[0].x < 32)

        # Pipeline is still _not_ finished, not a good time for the new action
        got_new_order = False
        if self.pipeline.is_empty():
            self.logger.debug(f"SCP101: pipeline IS empty")
            # Great, pipeline _is_ empty. What would be the next step?
            self.choose_next_action(obs)
            got_new_order = True
        else:
            self.logger.debug(f"SCP102: pipeline is NOT empty")

        if obs.last():  # and self.agent_name == 'bob':
            self.logger.debug(f"SCP103: last observation detected")
            logging.getLogger("res").info(
                f"Game: {self.game_num}. Outcome: {obs.reward}")

        # Returns None if still waiting or SC2 order
        return self.pipeline.run(obs), got_new_order

    def finalise_game(self, reward):
        # self.dump_decisions_hist()
        self.logger.debug(f"finalise_game")
        self.learn_from_game(reward)
        self.save_DQN()

    def learn_from_game(self, reward):
        reward_decay = .9

        self.logger.debug(
            f"{self.agent_name}: learn_from_game({self.decisions_hist})")

        for i in sorted(self.decisions_hist.keys(), reverse=True):
            previous_state = self.decisions_hist[i]['previous_state']
            previous_action = self.decisions_hist[i]['previous_action']

            next_state = self.decisions_hist[i]['next_state']

            self.qtable.learn(previous_state, previous_action, reward,
                              next_state)

            reward *= reward_decay

        return
