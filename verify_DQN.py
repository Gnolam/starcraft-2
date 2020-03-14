import pandas as pd

file_from = 'DQNs/v25i_check_positive_only_reward_war.gz'
file_to = 'debug/dqn.csv'

DQN = pd.read_pickle(file_from, compression='gzip')

fh_DQN = open(file_to, "w")

for i in DQN.index:
    for c in DQN.columns:
        coef = DQN.loc[i, c]
        # print("%s %s %.8f " % (i, c, DQN.loc[i, c]))
        if coef != 0:
            fh_DQN.write("\"%s\",%s,%.8f\r" % (i, c, coef))

fh_DQN.close()

print("Job's done\n  From: '%s'\n  To:   '%s'\n" % (file_from, file_to))
