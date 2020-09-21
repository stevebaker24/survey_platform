class Question:

    def __init__(self, q_row, score_indices, response_indices, historic_score_indicies, historic_response_indicies, historic_rows):
        self._qid = {'P': q_row['QVAR']}

        self.q_text = q_row['QTEXT_FULL']
        self.q_pos_text = q_row['QTEXT_POSTEXT']
        self.q_type = q_row['TYPE']
        self.scored = True if q_row['SCORED'] == 1 else False
        self.category = q_row['CATEGORY']
        self.online_qid = q_row['ONLINE_QID']
        self.paper_qid = q_row['PAPER_QID']

        #map of response text to each response option
        self._responses = {'P': self._create_response_map(q_row, response_indices)}

        #map of score for each response option
        self._score_map = {'P': self._create_score_map(q_row, score_indices)}
        # all scored responses
        self._scored_responses = {'P': self._create_scored_responses(self._score_map['P'])}
        # responses whos result contributes to a particular score
        self._score_responses = {'P': self._create_score_responses(self._score_map['P'])}


        #all columns which belong to this question
        self._question_columns = {'P': self._create_question_columns(self._qid['P'], self.q_type, self._responses['P'])}
        # columns which are invovled in scoring (excluding ignore)
        self._score_columns_dict= {'P': self._screate_score_columns_dict(self._qid['P'], self.q_type, self._score_responses['P'])}
        # columns whos result contributes to a particular score
        self._scored_columns = {'P': self._create_scored_columns(self._qid['P'], self.q_type, self._scored_responses['P'])}

        self.targeted = True if len(self._score_responses['P']['ignore']) > 0 else False

        self.has_historic = True if len(historic_rows) > 0 else False

        if self.has_historic:
            for period in historic_rows:
                historical_row = historic_rows[period]

                if historical_row['PDIFF'] == 1:
                    my_row = historical_row
                    using_response_indices = historic_response_indicies
                    using_score_indicies = historic_score_indicies
                else:
                    my_row = q_row
                    using_response_indices = response_indices
                    using_score_indicies = score_indices

                self._qid[period] = historical_row['PQVAR']

                self._responses[period] = self._create_response_map(my_row, using_response_indices)
                self._score_map[period] = self._create_score_map(my_row, using_score_indicies)

                self._scored_responses[period] = self._create_scored_responses(self._score_map[period])
                self._score_responses[period] = self._create_score_responses(self._score_map[period])

                self._question_columns[period] = self._create_question_columns(self._qid[period], self.q_type, self._responses[period])
                self._scored_columns[period] = self._create_scored_columns(self._qid[period], self.q_type, self._scored_responses[period])

                self._score_columns_dict[period] = self._screate_score_columns_dict(self._qid[period], self.q_type, self._score_responses[period])

    #getters
    def get_qid(self, period='P'):
        return self._qid[period]

    def get_responses(self, period='P'):
        return self._responses[period]

    def get_score_map(self, period='P'):
        return self._score_map[period]

    def get_scored_responses(self, period='P'):
        return self._scored_responses[period]

    def get_score_responses(self, period='P'):
        return self._score_responses[period]

    def get_question_columns(self, period='P'):
        return self._question_columns[period]

    def get_score_columns(self, period='P'):
        return self._score_columns_dict[period]

    def get_scored_columns(self, period='P'):
        return self._scored_columns[period]



    @staticmethod
    def _create_response_map(q_row, response_indices):
        mydict = {}
        for i, x in enumerate(q_row[(response_indices[0]):(response_indices[-1])+1]):
            if isinstance(x, str):
                mydict[i] = x
        return mydict

    @staticmethod
    def _create_score_map(q_row, score_indicies):
        mydict = {}
        for i, x in enumerate(q_row[(score_indicies[0]):(score_indicies[-1])+1]):
            if not np.isnan(x):
                mydict[i] = int(x)
        return mydict

    @staticmethod
    def _create_score_responses(score_map):
        mydict = {'pos': [],
                  'neu': [],
                  'neg': [],
                  'ignore': []
                  }

        for scoring_term in scoring_terms_dict:
            for response_option in score_map:
                # add to correct value
                if score_map[response_option] == scoring_terms_dict[scoring_term]['value']:
                    mydict[scoring_term].append(response_option)

        return mydict

    @staticmethod
    def _create_scored_responses(score_map):
        mylist = []
        for response_option in score_map:
            # if not an ignore vale
            if score_map[response_option] != scoring_ignore_value:
                mylist.append(response_option)
        return mylist

    @staticmethod
    def _create_question_columns(qid, q_type, responses):
        mylist=[]
        if q_type == 'M':
            for option in responses:
                mylist.append(f'{qid}_{option}')
        elif q_type in ['S', 'F']:
            mylist.append(qid)
        return mylist

    @staticmethod
    def _create_scored_columns(qid, q_type, scored_responses):
        mylist = []
        if q_type == 'M':
            for response_option in scored_responses:
                mylist.append(f'{qid}_{response_option}')
        elif q_type == 'S':
            mylist.append(qid)
        return mylist

    @staticmethod
    def _screate_score_columns_dict(qid, q_type, score_responses):
        score_columns = {'pos': [],
                         'neu': [],
                         'neg': [],
                         'ignore': []}

        if q_type == 'M':
            for score_type in score_responses:
                for x in score_responses[score_type]:
                    score_columns[score_type].append(f'{qid}_{x}')

        return score_columns

