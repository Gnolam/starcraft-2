import logging
import pandas as pd
import numpy as np
import h2o
from h2o.estimators import H2ORandomForestEstimator

# from lib.c01_obs_api import get_enemy_unit_type_counts


class DRFPredictor:
    """
    Class for implementation of Random Forest predictor instead of default DQN
    """
    log = None
    actions = None
    model = None
    predictors = None

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

    def choose_action(self, full_state):
        """
        Chose action based on the current h2o model
        
        Currently DRF but could be any
        """

        if np.random.uniform() >= self.e_greedy:
            action = np.random.choice(self.actions)
            best_score = 'random'
            return action, best_score

        # Create the set of states, with all set of possible action
        df_state = pd.DataFrame([full_state], index=range(len(self.actions)))

        # Match the state vector columns with the set of columns of the 'full model'
        df_state_ext = df_state.reindex(columns=self.predictors, fill_value=0)

        # The 'missing' column chosen_action is filled with zeroes, but it should be a string
        df_state_ext[['chosen_action']] = df_state_ext[['chosen_action'
                                                        ]].astype(str)

        # Create the permutation of current state and possible future actions
        for i in range(len(self.actions)):
            df_state_ext.at[i, "chosen_action"] = self.actions[i]

        # Convert the state-action vector into H2O format
        hex_state = h2o.H2OFrame(df_state_ext)

        # Predict the expected outcomes for each action
        hex_pred = self.model.predict(hex_state)

        # Take only the probability to win column
        df_pred = hex_pred.as_data_frame()["win"]

        # Define the best change to win
        best_prob = np.max(df_pred)

        # Identify an action, which is corresponds to the highest
        # estimated probability to win
        best_action = self.actions[np.random.choice(
            df_pred[df_pred == best_prob].index)]

        comment = f"probability = {np.round(best_prob,3)*100}%"
        return best_action, comment

    def update(self):
        """
        POC
        - Static knowledge base
        - Requires pre-preprocessed .csv files (currently in `R/dplyr`)
        """
        self.log.info("Train the model")

        hex_final = h2o.import_file(path="db/dat_final.csv",
                                    header=1,
                                    destination_frame="hex_final")

        hex_final["outcome_adj"] = hex_final["outcome_adj"].asfactor()
        self.predictors = hex_final.names
        self.predictors.remove('outcome_adj')

        self.model = H2ORandomForestEstimator()

        self.model.train(x=self.predictors,
                         y="outcome_adj",
                         training_frame=hex_final)
        self.log.debug(f"performance: {str(self.model.confusion_matrix())}")
