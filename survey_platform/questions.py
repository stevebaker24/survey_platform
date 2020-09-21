class Questions:

    def __init__(self, question_path):
        self.df = pd.read_excel(question_path, sheet_name='Question Info')

        self.hist_dfs = {}
        for period in survey_periods:
            if period != 'P':
                self.hist_dfs[period] = pd.read_excel(question_path, sheet_name=period)

        self.questions_dict = {}
        for period in survey_periods:
            self.questions_dict[period] = []

        self.catergory_dict = {}
        # self.questions_dict = {}

        self.scored_questions = []

        self.single_response_questions = []
        self.multi_response_questions = []
        self.text_response_questions = []

        self._generate_question_lists()

        # self._columns_to_score = self._get_columns_to_score()

    def get_questions (self, period='P'):
        return self.questions_dict[period]

    def __iter__(self):
        return iter(self.questions_dict['P'])

    def __len__(self):
        return len(self.questions_dict['P'])


    # def _get_columns_to_score(self):
    #     columns = []
    #     for question in self.scored_questions:
    #         columns = columns + question.question_columns
    #     return columns

    def get_all_question_columns(self, period='P'):
        question_columns = []
        for question in self.questions_dict[period]:
            question_columns.append(question.get_question_columns())
        #flatten the list of lists
        return [item for sublist in question_columns for item in sublist]

    def _generate_question_lists(self):
        score_indices = [i for i, elem in enumerate(list(self.df.columns)) if 'S_' in elem[0:2]]
        response_indices = [i for i, elem in enumerate(list(self.df.columns)) if 'R_' in elem[0:2]]

        historic_score_indicies = [i for i, elem in enumerate(list(self.hist_dfs[list(self.hist_dfs.keys())[0]].columns)) if 'S_' in elem[0:2]]
        historic_response_indicies = [i for i, elem in enumerate(list(self.hist_dfs[list(self.hist_dfs.keys())[0]].columns)) if 'R_' in elem[0:2]]


        for row in self.df.iterrows():

            row = row[1]
            qid = row['QVAR']

            question_hist_rows = {}
            for period in self.hist_dfs:
                df = self.hist_dfs[period]
                series = (df.loc[df['QVAR']==qid]).iloc[0]
                if isinstance(series['PQVAR'], float) and np.isnan(series['PQVAR']):
                    pass
                else:
                    question_hist_rows[period] = series

            #generate_question_object
            question_object = Question(row, score_indices, response_indices, historic_score_indicies, historic_response_indicies, question_hist_rows)

            # self.questions_dict[question_object.get_qid()] = question_object

            if question_object.category in self.catergory_dict.keys():
                self.catergory_dict[question_object.category].append(question_object)
            else:
                self.catergory_dict[question_object.category] = [question_object]


            if question_object.scored == 1:
                self.scored_questions.append(question_object)

            self.questions_dict['P'].append(question_object)
            for period in question_hist_rows:
                self.questions_dict[period].append(question_object)

            if question_object.q_type == 'S':
                self.single_response_questions.append(question_object)
            elif question_object.q_type == 'M':
                self.multi_response_questions.append(question_object)
            elif question_object.q_type == 'F':
                self.text_response_questions.append(question_object)



        return None