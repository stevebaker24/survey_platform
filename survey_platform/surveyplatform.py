from pathlib import Path

from survey_platform import config

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import xlsxwriter


def create_worksheet_name(worksheet_name):
    for char in [':', '\\', '/', '?', '*', '[', ']']:
        worksheet_name = worksheet_name.replace(char, '')
        return worksheet_name[:31]

def _input_filetype(path, index_col):
    extension = path.split('.')[-1]
    if extension == "csv":
        return pd.read_csv(path, index_col=index_col)
    if extension == "tsv":
        return pd.read_csv(path, sep='\t', index_col=index_col, encoding='utf-16')
    elif extension == "parquet":
        return pd.read_parquet(path, engine='pyarrow')
    if extension == "xlsx":
        return pd.read_excel(path, index_col=index_col)


#this should for part of a module to import
def z_test(pos_n_two, scorable_n_two, pos_n_one, scorable_n_one):
    p1 = (pos_n_one + 1) / (scorable_n_one + 2)
    p2 = (pos_n_two + 1) / (scorable_n_two + 2)

    nominator = (p1 - p2)

    denominator1 = (p1 * (1 - p1)) / (scorable_n_one + 2)
    denominator2 = (p2 * (1 - p2)) / (scorable_n_two + 2)
    denominator = math.sqrt(denominator1 + denominator2)

    return nominator / denominator


### multi respinse options questions.

def calc_scores(df, questions, score_types=['pos'], period='P'):
    for question in questions.scored_questions:

        question_score_response_dict = question.get_score_responses(period=period)
        scored_responses = question.get_scored_responses(period=period)
        scored_columns = question.get_scored_columns(period=period)


        current_qid = question.get_qid('P')
        #qid = question.get_qid(period)


        for score in score_types:
            score_column_header = current_qid + scoring_terms_dict[score]['suffix']

            #drop if alreay in the output column set.
            if score_column_header in df.columns:
                print(score_column_header)
                df = df.drop(score_column_header, axis=1)

            if question.q_type == 'M':
                score_columns = question.get_score_columns(period)[score]

                df.loc[df[scored_columns].sum(axis=1) > 0, score_column_header] = 0
                df.loc[df[score_columns].sum(axis=1) > 0, score_column_header] = 100

            if question.q_type == 'S':
                score_responses = question_score_response_dict[score]
                scored_column = scored_columns[0]

                df.loc[df[scored_column].isin(scored_responses), score_column_header] = 0
                df.loc[df[scored_column].isin(score_responses), score_column_header] = 100

    return df





class Sample:

    def __init__(self, sample_path, indexcol):
        self.df = _input_filetype(sample_path, indexcol)

    def get_orgs(self):
        return self.df['Trust code'].unique().tolist()


class Responses:

    def __init__(self, responses_path, indexcol, period=None, questions=None, breakdown_field=None, breakdown_field_values=None, master_breakdown_field=None):
        self.df = _input_filetype(responses_path, indexcol)


class Combined:

    def __init__(self, sample, responses):
        self.df = sample.df.join(responses.df, how='left')


class Reporting:

    def __init__(self, combined, questions):
        self.df = calc_scores(combined.df, questions, score_types=['pos', 'neu', 'neg'])
