import json

class config:
    # logging.basicConfig(format='%(asctime)-15s %(message)s') #/
    # log = logging.FileHandler('%s/main.log' % project_path)
    # logger = logging.getLogger()
    # logger.setLevel("INFO") #

    # fh_econ_state_csv = None
    # fh_econ_decisions = '%s/econ_decisions.log' % project_path

    # fh_war_state_csv = None
    # fh_war_decisions = open('%s/war_decisions.log' % project_path, "w")
    # fh_war_decisions.write("Hi there!")
    # fh_war_decisions.close()
    # fh_war_decisions = '%s/war_decisions.log' % project_path

    # global_debug = False

    # fn_global_debug = '%s/global.log' % project_path

    cfg = None
    bob_file = None

    def init(self, file_name):
        # read and validate the config file
        # init variables 
        # create file handlers
        # provide functions for debug output
        #   - functions will check themselves if they should dump anything based on json settings

    #def read_config(self, file_name):

    #def get_file_names(self):