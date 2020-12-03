import config


class Question:

    def __init__(self, qid, text=None, pos_text=None, q_type='S', scored=False, category=None, online_qid=None,
                 paper_qid=None, response_options=None, score_map=None):

        self.qid = qid
        self.text = text if text else f'Question text for {self.qid}'
        self.pos_text = pos_text if pos_text else f'Question pos text for {self.qid}'
        self.q_type = q_type
        self.scored = scored
        self.category = category
        self.online_qid = online_qid
        self.paper_qid = paper_qid
        self.response_options = response_options
        self.score_map = score_map
        self.historic_questions = {}

        # Properties to generate if requested
        self._scored_responses_list = None
        self._score_responses_dict = None
        self._question_columns = None
        self._scored_columns_list = None
        self._score_columns_dict = None
        self._targeted_options = None

    @classmethod
    def from_questions_rows(cls, q_row, response_options, score_map):
        qid = q_row[config.HEAD_QVAR]

        def _check_exists(header):
            return q_row[header] if header in q_row.index else None

        text = _check_exists(config.HEAD_QTEXTFULL)
        q_type = _check_exists(config.HEAD_QTYPE)
        pos_text = _check_exists(config.HEAD_POSTEXT)
        category = _check_exists(config.HEAD_CATEGORY)
        online_qid = _check_exists(config.HEAD_ONLINEQID)
        paper_qid = _check_exists(config.HEAD_PAPERQID)
        scored = _check_exists(config.HEAD_SCORED) == 1

        return cls(qid, text, pos_text, q_type, scored, category, online_qid, paper_qid, response_options, score_map)

    @property
    def targeted_options(self):
        if not self._targeted_options:
            self._targeted_options = self._score_responses_dict['ignore']
        return self._targeted_options

    @property
    def scored_responses(self):
        if not self._scored_responses_list:
            self._scored_responses_list = self._create_scored_responses_list()
        return self._scored_responses_list

    @property
    def score_responses(self):
        if not self._score_responses_dict:
            self._score_responses_dict = self._create_score_responses_dict()
        return self._score_responses_dict

    @property
    def question_columns(self):
        if not self._question_columns:
            self._question_columns = self._create_question_columns()
        return self._question_columns

    @property
    def scored_columns(self):
        if not self._scored_columns_list:
            self._scored_columns_list = self._create_scored_columns_list()
        return self._scored_columns_list

    @property
    def score_columns(self):
        if not self._score_columns_dict:
            self._score_columns_dict = self._create_score_columns_dict()
        return self._score_columns_dict

    @property
    def targeted(self):
        if not self._score_responses_dict:
            self._score_responses_dict = self._create_score_responses_dict()
        return len(self._score_responses_dict['ignore']) > 0

    @property
    def historic_periods(self):
        return list(self.historic_questions.keys())

    def has_historic(self):
        return bool(self.historic_questions)

    def option_score(self, option_number):
        for score_type in self.score_responses.keys():
            if option_number in self.score_responses[score_type]:
                return score_type

    def option_score_string(self, option_number):
        return config.scoring_terms_dict[self.option_score(option_number)]['string']

    def add_historic_question(self, period, qid, response_options=None, score_map=None):
        self.historic_questions[period] = HistoricQuestion(qid, self, response_options, score_map)

    def _create_score_responses_dict(self):
        score_responses = {x: [] for x in config.scoring_terms_dict.keys()}

        for scoring_term in score_responses.keys():
            for response_option in self.score_map:
                # add to correct value
                if self.score_map[response_option] == config.scoring_terms_dict[scoring_term]['value']:
                    score_responses[scoring_term].append(response_option)

        return score_responses

    def _create_scored_responses_list(self):
        return [x for x in self.score_map if self.score_map[x] != config.scoring_ignore_value]

    def _create_scored_columns_list(self):
        mylist = []
        if self.scored:
            if self.q_type == config.MULTI_CODE:
                for response_option in self.scored_responses:
                    mylist.append(f'{self.qid}_{response_option}')
            elif self.q_type == config.SINGLE_CODE:
                mylist.append(self.qid)
        return mylist

    def _create_score_columns_dict(self):
        score_columns = {x: [] for x in config.scoring_terms_dict.keys()}
        if self.q_type == config.MULTI_CODE:
            for score_type in self.score_responses:
                for x in self.score_responses[score_type]:
                    score_columns[score_type].append(f'{self.qid}_{x}')
        return score_columns

    def _create_question_columns(self):
        mylist = []
        if self.q_type == config.MULTI_CODE:
            for option in self.response_options:
                mylist.append(f'{self.qid}_{option}')
        elif self.q_type in [config.SINGLE_CODE, config.TEXT_CODE]:
            mylist.append(self.qid)
        return mylist


class HistoricQuestion(Question):
    def __init__(self, qid, parent_question: Question, response_options, score_map):
        super().__init__(qid, response_options, score_map)
        self.qid = qid

        self.parent_question = parent_question

        self.q_type = self.parent_question.q_type
        self.scored = self.parent_question.scored

        self.response_options = response_options if response_options else self.parent_question.response_options
        self.score_map = score_map if score_map else self.parent_question.score_map

        if score_map:
            self._scored_responses_list = super()._create_scored_responses_list()
            self._score_responses_dict = super()._create_score_responses_dict()
            self._question_columns = super()._create_question_columns()
            self._scored_columns_list = super()._create_scored_columns_list()
            self._score_columns_dict = super()._create_score_columns_dict()
        else:
            self._scored_responses_list = self.parent_question.scored_responses
            self._score_responses_dict = self.parent_question.score_responses
            self._question_columns = self.parent_question.question_columns
            self._scored_columns_list = self.parent_question.scored_columns
            self._score_columns_dict = self.parent_question.score_columns
