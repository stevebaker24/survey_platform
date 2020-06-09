from pathlib import Path
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

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


def get_rag(source, seperate_by_field='trust_id', seperator=None, group_by=None, questions=None,
                    score_type='pos'):

    if isinstance(group_by, str):
        columns_for_scoring, columns_output = [group_by], [group_by]
        number_groups = 1
    elif isinstance(group_by, list):
        columns_for_scoring, columns_output = group_by.copy(), group_by.copy()
        number_groups = len(group_by)

    for question in questions.get_scored_questions():
        columns_for_scoring.append(question)
        columns_output.append(question + scoring_terms[score_type]['suffix'])

    if isinstance(source, Reporting):
        df = (source.df[source.df[seperate_by_field] == seperator])[columns_output]
    elif isinstance(source, Survey):
        df = (source.reporting.df[source.reporting.df[seperate_by_field] == seperator])[columns_output]
    else:
        df = (source[source[seperate_by_field] == seperator])[columns_for_scoring]
        df = calc_scores(df, questions, [score_type])[columns_output]

    # group by group_variable
    grouped = df.groupby(group_by).mean()

    # comparator
    comparator = df[columns_output].mean().to_frame().transpose()

    if number_groups > 1:
        multiindex = tuple(['  ' for i in range(number_groups-1)] + ['Organisation'])
        index = pd.MultiIndex.from_tuples([multiindex])
    elif number_groups == 1:
        index = pd.Index(['Organisation'])

    comparator = comparator.set_index(index)

    #combined
    combined = comparator.append(grouped)

    # append and output to csv
    combined.transpose().to_excel(output_path / f'{seperator}_output.xlsx')

    return output_path / f'{seperator}_output.xlsx'


def get_heatmap(reporting, questions):
    df = reporting.df[questions].replace({1: -2, 2: -1, 3: 0, 4: 1, 5: 2, 6: np.nan})

    corr_matrix = df.corr(method='spearman')

    # Bunch of stuff to prepare the mask to hde half of the results
    mask = np.zeros_like(corr_matrix)
    mask[np.tril_indices_from(mask)] = True
    np.logical_not(mask, out=mask)

    sns.heatmap(corr_matrix, cmap='RdBu', vmin=-1, vmax=1, annot=True, mask=mask)
    plt.show()


class Survey:

    def __init__(self, name, survey_type, questions_path, responses_path, sample_path):
        self.name = name
        self.survey_type = survey_type
        self.questions = Questions(questions_path)
        self.sample = Sample(sample_path)
        self.responses = Responses(responses_path)
        self.combined = Combined(self.sample, self.responses, self.questions)
        self.reporting = Reporting(self.combined, self.questions)


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

    def __init__(self, combined, questions):
        self.df = calc_scores(combined.df, questions, score_types=['pos', 'neu', 'neg'])
