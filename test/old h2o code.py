        self.log.debug("DRF: Update")

        hex_results = h2o.import_file(
            path=self.fn_db_results,
            col_names=[
                "run_num", "step_num", "run_hash_id", "to_delete", "outcome"
            ],
            col_types=["numeric", "numeric", "uuid", "enum", "numeric"],
            header=-1,
            destination_frame="results")

        hex_decision = h2o.import_file(
            path=self.fn_db_decisions,
            col_names=[
                'run_num', 'step_num', 'run_hash_id', 'to_delete',
                'chosen_action'
            ],
            col_types=["numeric", "numeric", "uuid", "enum", "enum"],
            header=-1,
            destination_frame="decision")

        hex_state = h2o.import_file(
            path=self.fn_db_states,
            col_names=[
                'run_num', 'step_num', 'run_hash_id', 'feature_name',
                'feature_value'
            ],
            col_types=["numeric", "numeric", "uuid", "enum", "numeric"],
            header=-1,
            destination_frame="state")

        hex_results["outcome_adj"] = (hex_results["outcome"] == -1).ifelse(
            'loss', 'win')

        ###########################

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
        del results_db['outcome']
        del results_db['to_delete']
        del decision_db['to_delete']

        # summary = str(
        #     results_db[["run_num", "step_num", "outcome",
        #                 "outcome_adj"]].describe())
        self.log.debug(f"[CP01]: Resulting results_db\n{results_db.head()}")

        # filter(run_num >= 10)
        state_db[(state_db['run_num'] >= 50)]

        state_db = self.transform_id(state_db)
        # state_db['run_id'] = state_db[[
        #     'run_num', 'step_num', 'run_hash_id'
        # ]].apply(lambda row: '-'.join(row.values.astype(str)), axis=1)

        # del state_db['run_num']
        # del state_db['step_num']
        # del state_db['run_hash_id']

        self.log.debug(f"[CP02]: Resulting state_db\n{state_db.head()}")

        

        h2o.import_file(
            path=fn_db_results,
            col_names=[
                "run_num", "step_num", "run_hash_id", "to_delete",
                "chosen_action"
            ],
            col_types=["Numeric", "Numeric", "UUID", "Enum", "Enum"],
            header=-1,
            parse_type="CSV",
            destination_frame="fn_db_results")

        state_wide = h2o.H2OFrame(state_db).pivot(value='feature_value',
                                                  index='run_id',
                                                  column='feature_name')

        self.log.debug("[CP03]: Dump the pivoted frame")
        h2o.export_file(state_wide,
                        "logs/state_wide_03.csv",
                        quote_header=False)

        self.log.debug("[CP04]: Dump the pivoted frame")
        state_wide[state_wide.isna()] = 0
        h2o.export_file(state_wide,
                        "logs/state_wide_04.csv",
                        quote_header=False)

        self.log.debug("[CP09]: End of update()")



    def transform_id(self, df):
        df['run_id'] = df[['run_num', 'step_num', 'run_hash_id']].apply(
            lambda row: '-'.join(row.values.astype(str)), axis=1)
        del df['run_num']
        del df['step_num']
        del df['run_hash_id']

        return df