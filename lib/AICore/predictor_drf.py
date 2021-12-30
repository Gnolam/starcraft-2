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

        self.log.debug("Load .csv")
        #  col_integer(),
        # col_integer(),
        # col_character(),
        # col_character(),
        # col_character()
        decision_db = pd.read_csv(self.fn_db_decisions,
                                  names=[
                                      'run_num', 'step_num', 'run_hash_id',
                                      'to_delete', 'chosen_action'
                                  ],
                                  dtype={
                                      'run_num': np.int32,
                                      'step_num': np.int32,
                                      'run_hash_id': str,
                                      'to_delete': str,
                                      'chosen_action': str
                                  },
                                  header=None)

        state_db = pd.read_csv(self.fn_db_states,
                               names=[
                                   'run_num', 'step_num', 'run_hash_id',
                                   'feature_name', 'feature_value'
                               ],
                               dtype={
                                   'run_num': np.int32,
                                   'step_num': np.int32,
                                   'run_hash_id': str,
                                   'feature_name': str,
                                   'feature_value': np.int32
                               },
                               header=None)

        results_db = pd.read_csv(self.fn_db_results,
                                 names=[
                                     'run_num', 'step_num', 'run_hash_id',
                                     'to_delete', 'outcome'
                                 ],
                                 dtype={
                                     'run_num': np.int32,
                                     'step_num': np.int32,
                                     'run_hash_id': str,
                                     'to_delete': str,
                                     'outcome': np.int32
                                 },
                                 header=None)

        self.log.debug("Adjust result value")
        # mutate(outcome_adj = if_else(outcome >= 0, "win", "loss")) %>%
        # results_db.loc[results_db['outcome'] >= 0, 'outcome'] = 1
        # results_db.loc[results_db['outcome'] < 0, 'outcome'] = 0
        results_db['outcome_adj'] = np.where(results_db['outcome'] == -1,
                                             'loss', 'win')

        self.log.debug("Delete columns")
        # del results_db['outcome']
        del results_db['to_delete']
        del decision_db['to_delete']

        # summary = str(
        #     results_db[["run_num", "step_num", "outcome",
        #                 "outcome_adj"]].describe())
        self.log.debug(f"Resulting results_db\n{results_db.head()}")
