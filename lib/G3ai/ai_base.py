import os
import logging
import uuid
import h2o

import pandas as pd
from pysc2.lib import units

from lib.AICore.q_table import QLearningTable
from lib.AICore.predictor_drf import DRFPredictor
from lib.c01_obs_api import ObsAPI
from lib.G3pipe.pipeline import Pipeline


class aiBase(ObsAPI):
    agent_name = "L1"
    action_list = []
    action_container_class = None
    dqn_filename = None
    fh_decisions = None
    fh_state_csv = None
    fn_global_debug = None
    consistent_decision_agent = None
    log = None
    decisions_hist = {}
    step_counter = 0
    game_num = None
    game_uuid = None
    current_action = None
    ai_log_suffix = None

    previous_state = None
    previous_action = None
    full_state = None

    use_dqn_only = True
    ai_dqn: QLearningTable = None
    ai_drf: DRFPredictor = None

    ai_prediction_method_name = None
    ai_prediction_method_min_run = None

    pipeline: Pipeline = None

    def __init__(self, cfg):
        super().__init__()
        self.log = logging.getLogger(self.agent_name)
        self.log.info(f"L1.init({self.agent_name})")

        os.makedirs(os.path.dirname("db/"), exist_ok=True)
        self.fn_db_results = "db/results.csv"
        self.fn_db_states = "db/states.csv"
        self.fn_db_decisions = "db/decisions.csv"

        self.cfg = cfg
        self.ai_dqn = QLearningTable(actions=self.action_list,
                                     log_suffix=self.ai_log_suffix)

        self.dqn_filename,\
            self.fh_decisions,\
            self.fh_state_csv,\
            self.fn_global_debug,\
            self.fn_global_state =\
            cfg.get_filenames(self.agent_name)

        self.read_global_state()
        self.new_game()

        self.log.debug(f"Run number: {self.game_num}")

    def init2(self):
        h2o.init()
        self.ai_drf = DRFPredictor(actions=self.action_list,
                                   log_suffix=self.ai_log_suffix,
                                   fn_db_results=self.fn_db_results,
                                   fn_db_states=self.fn_db_states,
                                   fn_db_decisions=self.fn_db_decisions)

    def reset(self):
        self.log.debug("reset()")
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
            self.log.critical('Incorrect function was called: L1::get_state()')
            raise Exception('Incorrect function was called: L1::get_state()')

    def new_game(self):
        self.log.debug(f"new_game()")
        self.previous_state = None
        self.previous_action = None

        # Assign unique ID to the game run
        self.game_uuid = uuid.uuid4()

        # Creating generic pipeline
        self.pipeline = Pipeline()

        # History of decisions for future discounting
        self.decisions_hist = {}
        self.step_counter = 0
        self.game_num += 1

    def save_dqn(self):
        self.log.debug("save_DQN()")
        self.log.debug('Record current learnings (%s): %s' %
                       (self.agent_name, self.dqn_filename))
        self.ai_dqn.q_table.to_pickle(self.dqn_filename, 'gzip')

    def load_dqn(self):
        if os.path.isfile(self.dqn_filename):
            self.log.info('Load previous learnings (%s)' % self.agent_name)
            self.ai_dqn.q_table = pd.read_pickle(self.dqn_filename,
                                                 compression='gzip')
        else:
            self.log.info('NO previous learnings located (%s)' %
                          self.agent_name)

    def choose_next_action(self, obs) -> None:
        """ Picks the next action and updates the pipeline """
        state = str(self.get_state(obs))

        # Original 'best known' action based on Q-Table
        if self.game_num < 20 or self.use_dqn_only:
            action, best_score = self.ai_dqn.choose_action(state)
            self.log.debug(f"Q-Action: '{action.upper()}'" +
                           f", score = '{best_score}'")
        else:
            # Once some info is collected, we can try the alternative prediction methods
            action, best_prob = self.ai_drf.choose_action(self.full_state)
            self.log.debug(f"DRF-Action: '{action.upper()}'" +
                           f", best_prob = '{best_prob}'")

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

        # Record action taken for the current state
        self.write_tidy_vector_to_file(self.fn_db_decisions,
                                       {"action": str(action)})

        self.step_counter += 1
        self.previous_state = state
        self.previous_action = action

        self.log.debug(
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

        self.log.debug(f"{self.agent_name}: step()")

        if obs.first():
            self.log.debug("SCP100: first observation")
            command_centres = self.get_my_units_by_type(
                obs, units.Terran.CommandCenter)
            self.pipeline.base_top_left = (command_centres[0].x < 32)

        # Pipeline is still _not_ finished, not a good time for the new action
        got_new_order = False
        if self.pipeline.is_empty():
            self.log.debug(f"SCP101: pipeline IS empty")
            # Great, pipeline _is_ empty. What would be the next step?
            self.choose_next_action(obs)
            got_new_order = True
        else:
            self.log.debug("SCP102: pipeline is NOT empty")
            self.log.debug(str(self.pipeline))

        if obs.last():  # and self.agent_name == 'bob':
            self.log.debug(f"SCP103: last observation detected")
            logging.getLogger("res").info(
                f"Game: {self.game_num}. Outcome: {obs.reward}")

        # Returns None if still waiting or SC2 order
        return self.pipeline.run(obs), got_new_order

    def write_tidy_vector_to_file(self,
                                  file_name: str,
                                  data_record: dict,
                                  prefix: str = "") -> None:
        """Record data in tidy .csv format
        - Game number (game_num)
        - UUID of the game
        - Label
        - Value


        Args:
            - file_name ([str]): File name to be updated
            - record ([dict]): Dictionary of values to be added
            - prefix ([str]): Data label prefix. E.g. "enemy_"

        Note:            
            Try-catch-retry is applied to allow for parallel runs
        """

        # Prepare the text to output
        out_text = ""

        # with open(file_name, "a+") as output_file:
        #     output_file.write("write_tidy_vector_to_file(" +
        #                       f"data_record = '{data_record}'," +
        #                       f"prefix = '{prefix}'' )")

        for data_key, data_value in data_record.items():
            label = prefix + data_key.replace("Terran.", "")
            out_text += f"{self.game_num},{self.step_counter},{self.game_uuid},{label},{data_value}\n"

        for attempt in range(10):
            try:
                with open(file_name, "a+") as output_file:
                    output_file.write(out_text)
            except:
                pass
            else:
                break
        else:
            raise Exception(f"Failed to save data into {file_name}")

    def finalise_game(self, reward):
        # self.dump_decisions_hist()
        self.log.debug(f"finalise_game ID = {self.game_uuid}")

        self.write_tidy_vector_to_file(self.fn_db_results, {"outcome": reward})

        self.learn_from_game(reward)
        self.save_dqn()

    def learn_from_game(self, reward):
        reward_decay = .9

        self.log.debug(
            f"{self.agent_name}: learn_from_game({self.decisions_hist})")

        for i in sorted(self.decisions_hist.keys(), reverse=True):
            previous_state = self.decisions_hist[i]['previous_state']
            previous_action = self.decisions_hist[i]['previous_action']

            next_state = self.decisions_hist[i]['next_state']

            self.ai_dqn.learn(previous_state, previous_action, reward,
                              next_state)

            reward *= reward_decay

        return
