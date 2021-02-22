import logging
import pandas as pd
import numpy as np

# This class should be able to store history within itself
# then when save DQN (another function) it should load it again / save it
# Load again at the beginning of each round after init
# think about another game using it. All f()s should be contained here


class QLearningTable:
    def __init__(self,
                 actions,
                 learning_rate=0.01,
                 reward_decay=0.9,
                 e_greedy=0.9):
        self.actions = actions
        self.learning_rate = learning_rate
        self.reward_decay = reward_decay
        self.e_greedy = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, state):
        self.force_state_existence(state)
        state_action = self.q_table.loc[state, :]
        if np.random.uniform() < self.e_greedy:
            # if global_log_action:
            #     fh_decisions.write("<=>")
            best_score = np.max(state_action)
            action = np.random.choice(
                state_action[state_action == np.max(state_action)].index)
            best_score = f"best = {action}:{best_score} of\n{str(state_action)}"

        else:
            action = np.random.choice(self.actions)
            best_score = 'random'
            # if global_log_action:
            #     fh_decisions.write("<~>")
        return action, best_score

    def learn(self, s, a, r, s_, fn):
        self.force_state_existence(s_)
        q_predict = self.q_table.loc[s, a]

        if s_ != 'terminal':
            q_target = r + self.reward_decay * self.q_table.loc[s_, :].max()
        else:
            q_target = r

        error = q_target - q_predict
        self.q_table.loc[s, a] += self.learning_rate * error

        fh = open(fn, "a+")
        fh.write(
            f'Learning:\n  q_table.loc[{s}, {a}] = {q_predict}\n' +
            f'  self.q_table.loc[{s_}, :].max() = {q_target}\n' +
            f'   (new) self.q_table.loc[s, a] = {self.q_table.loc[s, a]}\n\n')
        fh.close()

    def declare_action_invalid(self, state, action):
        self.force_state_existence(state)
        self.q_table.loc[state, action] = -9999

    def force_state_existence(self, state):
        # logger = logging.getLogger("bob")
        if state not in self.q_table.index:
            self.q_table = self.q_table.append(
                pd.Series([0] * len(self.actions),
                          index=self.q_table.columns,
                          name=state))
            # state_action = self.q_table.loc[state, :]
            # logger.debug(f"state ({state}) is new:\n{state_action} ")
        else:
            # state_action = self.q_table.loc[state, :]
            # logger.debug(f"state ({state}) exists: {state_action} ")
            pass
