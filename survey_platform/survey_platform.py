import pandas as pd
import math
import questions as qst
import question as sqst

import numpy as np

import config


def sanitise_for_path(string):
    return string.replace("/", "")


def sanitize_worksheet_name(worksheet_name):
    for char in [':', '\\', '/', '?', '*', '[', ']']:
        worksheet_name = worksheet_name.replace(char, '')
    return worksheet_name[:31]


def _input_filetype(path, index_col):
    extension = path.split('.')[-1]
    if extension == "csv":
        return pd.read_csv(path, index_col=index_col, low_memory=False)
    if extension == "tsv":
        return pd.read_csv(path, sep='\t', index_col=index_col, low_memory=False, encoding='utf-16')
    elif extension == "parquet":
        return pd.read_parquet(path, engine='pyarrow')
    if extension == "xlsx":
        return pd.read_excel(path, index_col=index_col)


def calc_scores(df, questions, score_types=None):
    """Calculate scores (pos/neu/neg) can accept questions object or list of question objects"""
    df = df.copy()

    if score_types is None:
        score_types = ['pos']

    if isinstance(questions, qst.Questions):
        questions = questions.scored_questions

    for question in questions:

        question_score_response_dict = question.score_responses
        scored_responses = question.scored_responses
        scored_columns = question.scored_columns

        qid = question.qid


        if isinstance(question, sqst.HistoricQuestion):
            output_qid = question.parent_question.qid
        else:
            output_qid = qid


        for score in score_types:
            score_column_header = f'{output_qid}{config.scoring_terms_dict[score]["suffix"]}'

            # drop if alreay in the output column set.
            if score_column_header in df.columns:
                df = df.drop(score_column_header, axis=1)

            if question.q_type == 'M':
                score_columns = question.score_columns[score]

                df.loc[df[scored_columns].sum(axis=1) > 0, score_column_header] = 0
                df.loc[df[score_columns].sum(axis=1) > 0, score_column_header] = 100

            if question.q_type == 'S':
                score_responses = question_score_response_dict[score]
                scored_column = scored_columns[0]

                scoremap = {x: (0 if x not in score_responses else 100) for x in scored_responses }
                df[score_column_header] = df[scored_column].map(scoremap)

        df.drop(question.question_columns, axis=1, inplace=True)

    return df


# Temporary
class Sample:

    def __init__(self, sample_path, indexcol):
        self.df = _input_filetype(sample_path, indexcol)

    def get_orgs(self):
        return self.df['Trust code'].unique().tolist()


class Responses:

    def __init__(self, responses_path, indexcol):
        self.df = _input_filetype(responses_path, indexcol)


class Combined:

    def __init__(self, sample, responses):
        self.df = sample.df.join(responses.df, how='left')


class Reporting:

    def __init__(self, combined, questions):
        self.df = calc_scores(combined.df, questions, score_types=['pos', 'neu', 'neg'])
