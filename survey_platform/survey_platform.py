from pathlib import Path
import numpy as np
import pandas as pd

output_path = Path('C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/outputs')

scoring_terms = {'pos': {'value': 1, 'string': 'Positive', 'suffix': '_pos'},
                 'neu': {'value': 2, 'string': 'Neutral', 'suffix': '_neu'},
                 'neg': {'value': 3, 'string': 'Negative', 'suffix': '_neg'},
                 'ignore': {'value': 4, 'string': 'Ignore', 'suffix': None}}

ignore_value = scoring_terms['ignore']['value']
scored_terms = [i['value'] for i in scoring_terms.values()]
scored_terms.remove(ignore_value)


def _input_filetype(path, index_col):
    extension = path.split('.')[-1]
    if extension == "csv":
        return pd.read_csv(path, index_col=index_col)
    elif extension == "parquet":
        return pd.read_parquet(path, engine='pyarrow')


def calc_scores(df, questions, score_types=['pos']):
    for question in questions.get_scored_questions():
        question_score_response_dict = (questions.questionlist[question]).score_responses

        for score in score_types:
            score_column_header = question + scoring_terms[score]['suffix']
            score_responses = question_score_response_dict[score]

            df.loc[df[question].isin(scored_terms), score_column_header] = 0
            df.loc[df[question].isin(score_responses), score_column_header] = 100

    return df


def get_summary_csv(df, org, group_variable, questions, score_type=['pos']):
    columns_for_scoring = [group_variable]
    columns_output = [group_variable]

    for question in questions.get_scored_questions():
        columns_for_scoring.append(question)
        for score in score_type:
            columns_output.append(question + scoring_terms[score]['suffix'])

    df = (df[df['trust_id'] == org])[columns_for_scoring]

    df = calc_scores(df, questions, score_type)

    # group by group_variable
    grouped = df[columns_output].groupby(group_variable).mean()

    # comparator
    comparator = df[columns_output].mean().rename('Organisation')

    # append and output to csv
    grouped.append(comparator).to_csv(output_path / f'{org}_output.csv')

    return output_path / f'{org}_output.csv'


class Survey:

    def __init__(self, name, survey_type, questions_path, responses_path, sample_path):
        self.name = name
        self.survey_type = survey_type
        self.questions = Questions(questions_path)
        self.sample = Sample(sample_path)
        self.responses = Responses(responses_path)
        self.combined = Combined(self.sample, self.responses, self.questions)
        #self.reporting = Reporting(combined)


class Sample:

    def __init__(self, sample_path):
        self.df = _input_filetype(sample_path, 'sample_id')

    def get_orgs(self):
        return self.df['trust_id'].unique().tolist()


class Responses:

    def __init__(self, responses_path):
        self.df = _input_filetype(responses_path, 'respondent_id')


class Combined:

    def __init__(self, sample, responses, questions):
        self.df = sample.df.join(responses.df, how='left')
        self.questions = questions


class Questions:

    def __init__(self, question_path):
        self.df = pd.read_csv(question_path, index_col='qid')
        self.questionlist = self._generate_dict()
        self.scored_questions = [k for k, v in self.questionlist.items() if v.pos_scored == 1]

    def __iter__(self):
        return iter(self.questionlist.values())

    def __len__(self):
        return len(self.questionlist)

    def get_scored_questions(self):
        return self.scored_questions

    def _generate_dict(self):
        score_indices = [i for i, elem in enumerate(list(self.df.columns)) if 's_' in elem[0:2]]
        response_indices = [i for i, elem in enumerate(list(self.df.columns)) if 'r_' in elem[0:2]]

        return {row[0]: Question(row, score_indices, response_indices) for row in self.df.iterrows()}


class Question:

    def __init__(self, q_row, score_indices, response_indices):
        self.qid = q_row[0]
        self.q_text = q_row[1]['q_text']
        self.q_type = q_row[1]['q_type']
        self.pos_scored = q_row[1]['pos_scored']

        self.score_map = self.get_score_map(q_row[1], score_indices)
        self.responses = self.get_response_map(q_row[1], response_indices)
        self.score_responses = self.get_score_responses(q_row[1], score_indices)

    @staticmethod
    def get_score_map(q_row, score_indicies):
        mydict = {}
        for i, x in enumerate(q_row[(score_indicies[0]):(score_indicies[-1])]):
            if not np.isnan(x):
                mydict[i] = int(x)
        return mydict

    @staticmethod
    def get_score_responses(q_row, score_indicies):

        mydict = {'pos': [],
                  'neu': [],
                  'neg': [],
                  'ignore': []
                  }

        for i, x in enumerate(q_row[(score_indicies[0]):(score_indicies[-1])]):
            if x == scoring_terms['pos']['value']:
                mydict['pos'].append(i)
            elif x == scoring_terms['neu']['value']:
                mydict['neu'].append(i)
            elif x == scoring_terms['neg']['value']:
                mydict['neg'].append(i)
            elif x == scoring_terms['ignore']['value']:
                mydict['ignore'].append(i)

        return mydict

    @staticmethod
    def get_response_map(q_row, response_indices):
        mydict = {}
        for i, x in enumerate(q_row[(response_indices[0]):(response_indices[-1])]):
            if isinstance(x, str):
                mydict[i] = x
        return mydict


class Reporting:

    def __init__(self, df, questions):
        self.df = calc_scores(df, questions, score_types=['pos', 'neu', 'neg'])
