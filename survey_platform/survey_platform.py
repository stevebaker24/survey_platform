import pandas as pd
import math

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
    df = df.copy()

    if score_types is None:
        score_types = ['pos']

    for question in questions.scored_questions:

        question_score_response_dict = question.score_responses
        scored_responses = question.scored_responses
        scored_columns = question.scored_columns

        qid = question.qid

        for score in score_types:
            score_column_header = f'{qid}{config.scoring_terms_dict[score]["suffix"]}'

            # drop if alreay in the output column set.
            if score_column_header in df.columns:
                print(score_column_header)
                df = df.drop(score_column_header, axis=1)

            if question.q_type == 'M':
                score_columns = question.score_columns[score]

                df.loc[df[scored_columns].sum(axis=1) > 0, score_column_header] = 0
                df.loc[df[score_columns].sum(axis=1) > 0, score_column_header] = 100

            if question.q_type == 'S':
                score_responses = question_score_response_dict[score]
                scored_column = scored_columns[0]

                df.loc[df[scored_column].isin(scored_responses), score_column_header] = 0
                df.loc[df[scored_column].isin(score_responses), score_column_header] = 100

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
