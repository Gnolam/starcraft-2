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

    pipeline: Pipeline = None

    def __init__(self, cfg):
        super().__init__()
        self.logger = logging.getLogger(self.agent_name)
        self.logger.info(f"L1.init({self.agent_name})")

        self.cfg = cfg
        self.qtable = QLearningTable(self.action_list)

        # Creating generic pipeline
        self.pipeline = Pipeline()

        self.DQN_filename,\
            self.fh_decisions,\
            self.fh_state_csv,\
            self.fn_global_debug,\
            self.fn_global_state =\
            cfg.get_filenames(self.agent_name)

        self.agent_cfg = cfg.run_cfg.get(self.agent_name)
        self.read_global_state()
        self.new_game()

        self.logger.debug(f"Run number: {self.game_num}")
        self.consistent_decision_agent =\
            cfg.run_cfg.get(self.agent_name).get("consistent")
        self.logger.debug(
            f'consistent_decision_agent: {self.consistent_decision_agent}')

    def reset(self):
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
        self.base_top_left = None
        self.previous_state = None
        self.previous_action = None

        # History of decisions for future discounting
        self.decisions_hist = {}
        self.step_counter = 0
        self.game_num += 1

    def save_DQN(self):
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

    def step(self, obs):
        command_centres =\
            self.get_my_units_by_type(obs, units.Terran.CommandCenter)

        if obs.first():
            self.base_top_left = (command_centres[0].x < 32)
            self.pipeline.base_top_left = self.base_top_left
        state = str(self.get_state(obs))

        # Original 'best known' action based on Q-Table
        action, best_score = self.qtable.choose_action(state)

        self.logger.debug(f"Q-Action: '{action.upper()}'" +
                          f", score = '{best_score}'")

        next_state = 'terminal' if obs.last() else state

        if obs.last():  # and self.agent_name == 'bob':
            logging.getLogger("res").info(
                f"Game: {self.game_num}. Outcome: {obs.reward}")

        # 'LEARN' should be across the WHOLE history
        # Q-Table should be updated to consume 'batch' history
        # Record decision for later 'batch' learning
        # ToDo: add Q-Table coef here instead of reward
        if self.previous_action is not None:
            self.decisions_hist[self.step_counter] = {
                'previous_state': self.previous_state,
                'previous_action': self.previous_action,
                'reward': obs.reward,
                'next_state': next_state
            }

        self.step_counter += 1

        self.previous_state = state
        self.previous_action = action

        # return self.pipeline.run(obs)

        # action_res = getattr(self,
                             action)(obs, check_action_availability_only=False)
        # return action_res

    def finalise_game(self):
        # self.dump_decisions_hist()
        self.learn_from_game()
        self.save_DQN()

    def learn_from_game(self):
        reward = None
        reward_decay = .9

        for i in sorted(self.decisions_hist.keys(), reverse=True):
            previous_state = self.decisions_hist[i]['previous_state']
            previous_action = self.decisions_hist[i]['previous_action']

            # Only the final reward (-1 or +1) should be taken into account
            if reward is None:
                reward = self.decisions_hist[i]['reward']
            next_state = self.decisions_hist[i]['next_state']

            fh = open(self.fn_global_debug, "a+")
            fh.write('[%s]: Apply learning for step %s with reward %s\n " + \
                " Action: %s\n  States (%s -> %s)\n' %
                     (self.agent_name, i, reward, previous_action,
                      previous_state, next_state))
            fh.close()

            self.qtable.learn(previous_state,
                              previous_action,
                              reward,
                              next_state,
                              fn=self.fn_global_debug)

            reward *= reward_decay
        return
