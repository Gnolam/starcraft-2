import logging
import pandas as pd
import numpy as np

# from lib.c01_obs_api import get_enemy_unit_type_counts


class DRFPredictor:
    """
    Class for implementation of Random Forest predictor instead of default DQN
    """
    log = None
    actions = None
    model = None

    fn_db_results = None
    fn_db_states = None
    fn_db_decisions = None

    def __init__(self,
                 actions,
                 log_suffix=None,
                 fn_db_results=None,
                 fn_db_states=None,
                 fn_db_decisions=None,
                 e_greedy=0.9):

        if log_suffix is not None:
            self.log = logging.getLogger(f"DRF_{log_suffix}")
            self.log.info("DRF init")
        # else:
        #     raise Exception("Log system is not initialized")

        self.actions = actions
        self.e_greedy = e_greedy

        self.fn_db_results = fn_db_results
        self.fn_db_states = fn_db_states
        self.fn_db_decisions = fn_db_decisions

    def choose_action(self, full_state: dict):
        """
        ToDo:
         1. get the state vector, compatible with H2O DRF. Which function to call to make it compatible with Save?
         2. iterate through all the possible actions to get the highest probability
        """

        if np.random.uniform() < self.e_greedy:
            best_score = np.max(state_action)
            action = np.random.choice(
                state_action[state_action == np.max(state_action)].index)
            best_score = f"best = {action}:{best_score} of\n{str(state_action)}"

        else:
            action = np.random.choice(self.actions)
            best_score = 'random'
        return action, best_score

    def update(self):
        """
        ToDo: load data from stored files, train DRF object       
        """

        self.log.debug("DRF: Update")

        df = pd.read_csv(self.fn_db_decisions,
                         names=[
                             'run_num', 'step_num', 'run_hash_id', 'to_delete',
                             'chosen_action'
                         ],
                         header=None)
