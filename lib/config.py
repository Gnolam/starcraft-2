import yaml, os, logging

class Config:
    # global_debug = False

    cfg = None
    project_path = None
    fname_DQN_econ= None
    fname_DQN_war = None
    fname_decisions_econ = None
    fname_decisions_war = None


    def __init__(self, agent_config_path):
        # read the config file
        if not os.path.exists(agent_config_path):
            print("!!! Agent config file does not exist !!!")
            exit(-1)

        print("Reading agents config file:", agent_config_path)
        with open(agent_config_path) as f:
            self.run = yaml.safe_load(f.read())
            f.close()

        self.run_id = self.run.get("run_id")
        if not self.run_id:
            print("!!! Config file corrupted: 'run_id' is not present !!!")
            exit(-2)

        # init variables 
        self.project_path = f'runs/{self.run_id}' 

        print("Set project path to:", self.project_path)
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path)


    def init_logging(self, logging_config_path):
        if not os.path.exists(logging_config_path):
            print("!!! Logging config file does not exist !!!")
            exit(-3)

        print("Reading logging config file:", logging_config_path)
        with open(logging_config_path) as f:
            logging_config = yaml.safe_load(f.read())
            f.close()

        logging.config.dictConfig(logging_config)
        logging.getLogger("main").info(f"Logging system initiated with '{logging_config_path}'")


    def get_filenames(self, agent_name):
        fname_DQN = f'{self.project_path}/DQN_{agent_name}.gz'
        fname_decisions = f'{self.project_path}/decision_hist_{agent_name}.log'
        fname_csv = f'{self.project_path}/stats_{agent_name}.csv'
        fname_DQN_debug = f'{self.project_path}/DQN_{agent_name}.dbg'
        return fname_DQN,fname_decisions,fname_csv,fname_DQN_debug
