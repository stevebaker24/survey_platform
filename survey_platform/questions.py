import pandas as pd
import numpy as np
from openpyxl import load_workbook
from pathlib import Path

from .question import Question
from . import config


class Questions:

    def __init__(self, period_questions, **previous_period_questions):

        self._df = period_questions

        self._historic_dfs = previous_period_questions if previous_period_questions else None
        self._historic_indicies = self._get_historic_df_indicies() if previous_period_questions else None

        self._question_list = self._generate_question_list()

        # Properties to generate if requested
        self._scored_questions = None
        self._single_response_questions = None
        self._multi_response_questions = None
        self._text_response_questions = None
        self._all_question_columns = None
        self._questions_with_historic = None

    @classmethod
    def from_file(cls, questions_path):

        questions_path = Path(questions_path)
        kwargs_dict = {}
        test = questions_path.suffix.lower()

        if questions_path.suffix.lower() in config.EXCEL_EXTS:
            wb = load_workbook(questions_path)

            question_sheet_name = config.P_QUESTION_SHEET if len(wb.sheetnames) > 1 else wb.sheetnames[0]
            period_questions = pd.read_excel(questions_path, sheet_name=question_sheet_name)

            if len(wb.sheetnames) > 1:
                for sheet in wb.sheetnames:
                    if sheet[:2] == config.PERIOD_IDENTIFIER:
                        kwargs_dict[sheet] = pd.read_excel(questions_path, sheet_name=sheet)

        elif questions_path.suffix.lower() == '.csv':
            period_questions = pd.read_csv(questions_path, encoding='utf-8')

        return cls(period_questions, **kwargs_dict)

    @property
    def question_list(self):
        return self._question_list

    @property
    def scored_questions(self):
        if not self._scored_questions:
            self._scored_questions = [q for q in self._question_list if q.scored]
        return self._scored_questions

    @property
    def questions_with_historic(self):
        if not self._questions_with_historic:
            self._questions_with_historic = [q for q in self._question_list if len(q.historic_questions) > 0]
        return self._questions_with_historic

    @property
    def single_response_questions(self):
        if not self._single_response_questions:
            self._single_response_questions = self._create_type_lists(config.SINGLE_CODE)
        return self._single_response_questions

    @property
    def multi_response_questions(self):
        if not self._multi_response_questions:
            self._multi_response_questions = self._create_type_lists(config.MULTI_CODE)
        return self._multi_response_questions

    @property
    def text_response_questions(self):
        if not self._text_response_questions:
            self._text_response_questions = self._create_type_lists(config.TEXT_CODE)
        return self._text_response_questions

    @property
    def all_question_columns(self):
        if not self._all_question_columns:
            all_question_columns = [q.question_columns for q in self._question_list]
            self._all_question_columns = [item for sublist in all_question_columns for item in sublist]
        return self._all_question_columns

    def _create_maps(self, q_row, response_indices, score_indices):
        return {'response_options': self._create_map(q_row, response_indices),
                'score_map': self._create_map(q_row, score_indices)}

    @staticmethod
    def _create_map(q_row, indices):
        mydict = {}
        for i, x in enumerate(q_row[(indices[0]):(indices[-1]) + 1]):
            if isinstance(x, str) or not np.isnan(x):
                x = int(x) if isinstance(x, float) else x
                mydict[i] = x
        return mydict

    @staticmethod
    def _create_indicies(df, index_prefix):
        return [i for i, elem in enumerate(list(df.columns)) if index_prefix in elem[0:2]]

    def _get_score_response_indicies(self, df):
        return {'score_indices': self._create_indicies(df, config.HEAD_SCORE_PREFIX),
                'response_indices': self._create_indicies(df, config.HEAD_RESPONSE_PREFIX)}

    def _get_historic_df_indicies(self):
        historic_indicies_dict = {}
        for period, historic_df in self._historic_dfs.items():
            historic_indicies_dict[period] = self._get_score_response_indicies(historic_df)
        return historic_indicies_dict

    def _create_question(self, q_row, indices):
        maps = self._create_maps(q_row, indices['response_indices'], indices['score_indices'])
        return Question.from_questions_rows(q_row, maps['response_options'], maps['score_map'])

    def _create_historic_questions(self, question):
        for period, historic_df in self._historic_dfs.items():
            h_row = historic_df.loc[historic_df[config.HEAD_QVAR] == question.qid].squeeze()
            historic_qid = h_row[config.HEAD_PQVAR]

            if isinstance(historic_qid, str):
                if h_row[config.HEAD_PDIFF] == 1:
                    maps = self._create_maps(h_row, self._historic_indicies[period]['response_indices'],
                                             self._historic_indicies[period]['score_indices'])
                    question.add_historic_question(period, historic_qid, maps['response_options'], maps['score_map'])
                else:
                    question.add_historic_question(period, historic_qid)

    def _generate_question_list(self):
        indices = self._get_score_response_indicies(self._df)
        questions_list = []
        for index, q_row in self._df.iterrows():
            question_object = self._create_question(q_row, indices)

            if question_object.scored and self._historic_dfs:
                self._create_historic_questions(question_object)

            questions_list.append(question_object)

        return questions_list

    def _create_type_lists(self, q_type):
        return [q for q in self._question_list if q.q_type == q_type]

    def get_by_qid(self, qid):
        return next((q for q in self._question_list if q.qid == qid), None)

    def __iter__(self):
        return iter(self._question_list)

    def __len__(self):
        return len(self._question_list)
