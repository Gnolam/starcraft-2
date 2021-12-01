import yaml
import os
import logging
import absl.logging
from configparser import ConfigParser, ExtendedInterpolation


class Config:
    # global_debug = False

    config = None
    project_path = None
    fname_DQN_econ = None
    fname_DQN_war = None
    fname_decisions_econ = None
    fname_decisions_war = None

    def __init__(self, config_file_name):
        self.config = ConfigParser(interpolation=ExtendedInterpolation())
        self.config.read(config_file_name)
        print(self.config.sections())

        self.run_id = self.config.get('Paths', 'run_id')
        config_log_file = self.config.get('Paths', 'log_definition')
        self.project_path = self.config.get('Paths', 'project')

        self.fix_ADSL_logging()
        self.init_logging(config_log_file)

        print("Set project path to:", self.project_path)
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path)

    def init_logging(self, logging_config_path):
        logging_config = self.read_yaml_file(logging_config_path)
        logging.config.dictConfig(logging_config)
        logging.getLogger("main").info(
            f"Logging system initiated with '{logging_config_path}'")

    def get_filenames(self, agent_name):
        fname_DQN = f'{self.project_path}/DQN_{agent_name}.gz'
        fname_decisions = f'{self.project_path}/decision_hist_{agent_name}.log'
        fname_csv = f'{self.project_path}/stats_{agent_name}.csv'
        fname_DQN_debug = f'{self.project_path}/DQN_{agent_name}.dbg'
        fname_state = f'{self.project_path}/global_state.yaml'
        return fname_DQN, fname_decisions, fname_csv, \
            fname_DQN_debug, fname_state

    def fix_ADSL_logging(self):
        absl.logging.set_stderrthreshold('info')
        absl.logging.set_verbosity('info')
        logging.root.removeHandler(absl.logging._absl_handler)
        absl.logging._warn_preinit_stderr = False

    def read_yaml_file(self, fname):
        print("read_yaml_file(", fname, ")")
        if not os.path.exists(fname):
            raise Exception(f".yaml file '{fname}' does not exist")
        with open(fname) as f:
            cfg = yaml.safe_load(f.read())
            f.close()
        return cfg

    def write_yaml_file(self, fname, data):
        with open(fname, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)
            outfile.close()
