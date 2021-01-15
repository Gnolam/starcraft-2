import pandas as pd
import numpy as np

class QLearningTable:
    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions
        self.learning_rate = learning_rate
        self.reward_decay = reward_decay
        self.e_greedy = reward_decay
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)
        if np.random.uniform() < self.e_greedy:
            # if global_log_action:
            #     fh_decisions.write("<=>")
            state_action = self.q_table.loc[observation, :]
            action = np.random.choice(
                state_action[state_action == np.max(state_action)].index)
        else:
            action = np.random.choice(self.actions)
            # if global_log_action:
            #     fh_decisions.write("<~>")
        return action

    def learn(self, s, a, r, s_, fn):
        self.check_state_exist(s_)
        q_predict = self.q_table.loc[s, a]

        if s_ != 'terminal':
            q_target = r + self.reward_decay * self.q_table.loc[s_, :].max()
        else:
            q_target = r

        error = q_target - q_predict
        self.q_table.loc[s, a] += self.learning_rate * error

        fh = open(fn, "a+")
        fh.write('Learning:\n  q_table.loc[%s, %s] = %s\n  self.q_table.loc[%s, :].max() = %s\n   (new) self.q_table.loc[%s, %s] = %s\n\n' %
                 (s, a, q_predict, s_, q_target, s, a, self.q_table.loc[s, a]))
        fh.close()

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            self.q_table = self.q_table.append(pd.Series([0] * len(self.actions),
                                                         index=self.q_table.columns,
                                                         name=state))
