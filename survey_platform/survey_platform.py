from pathlib import Path
import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None

scoring_terms = {'pos': {'value': 1, 'string': 'Positive', 'suffix': '_pos'},
                 'neu': {'value': 2, 'string': 'Neutral', 'suffix': '_neu'},
                 'neg': {'value': 3, 'string': 'Negative', 'suffix': '_neg'},
                 'ignore': {'value': 4, 'string': 'Ignore', 'suffix': None}}

ignore_value = scoring_terms['ignore']['value']
scored_terms = [i['value'] for i in scoring_terms.values()]
scored_terms.remove(ignore_value)


def input_filetype(path, index_col):
    extension = path.split('.')[-1]
    if extension == "csv":
        return pd.read_csv(path, index_col=index_col)
    elif extension == "parquet":
        return pd.read_parquet(path, engine='pyarrow')


class Survey:

    def __init__(self, name, survey_type, questions, responses, sample):
        self.name = name
        self.survey_type = survey_type
        self.questions = Questions(questions)
        self.sample = Sample(sample)
        self.responses = Responses(responses)
        self.combined = Combined(self.sample, self.responses, self.questions)


class Questions:

    def __init__(self, question_path):
        self.df = pd.read_csv(question_path, index_col='qid')

        self.score_indices = [i for i, elem in enumerate(list(self.df.columns)) if 's_' in elem[0:2]]
        self.response_indices = [i for i, elem in enumerate(list(self.df.columns)) if 'r_' in elem[0:2]]

        self.questionlist = {}
        for row in self.df.iterrows():
            self.questionlist[row[0]] = Question(row, self.score_indices, self.response_indices)

    def __iter__(self):
        return iter(self.questionlist.values())

    def __len__(self):
        return len(self.questionlist)

    def get_scored_questions(self):
        return (self.df[self.df['pos_scored'] == 1]).index.tolist()


class Question:

    def __init__(self, q_row, score_indices, response_indices):
        self.qid = q_row[0]
        self.q_text = q_row[1]['q_text']
        self.q_type = q_row[1]['q_type']
        self.pos_scored = q_row[1]['pos_scored']

        self.score_map = self.__get_score_map(q_row[1], score_indices)
        self.responses = self.__get_response_map(q_row[1], response_indices)
        self.score_responses = self.__get_score_responses(q_row[1], score_indices)

    @staticmethod
    def __get_score_map(q_row, score_indicies):
        mydict = {}
        for i, x in enumerate(q_row[(score_indicies[0]):(score_indicies[-1])]):
            if not np.isnan(x):
                mydict[i] = int(x)
        return mydict

    @staticmethod
    def __get_score_responses(q_row, score_indicies):

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
    def __get_response_map(q_row, response_indices):
        mydict = {}
        for i, x in enumerate(q_row[(response_indices[0]):(response_indices[-1])]):
            if isinstance(x, str):
                mydict[i] = x
        return mydict


class Sample:

    def __init__(self, sample_path):
        self.index_col = 'sample_id'
        self.df = input_filetype(sample_path, self.index_col)
        # pd.read_csv(sample_path, index_col='sample_id')

    def get_num_samples(self):
        return len(self.df)


class Responses:

    def __init__(self, responses_path):
        self.index_col = 'respondent_id'
        self.df = input_filetype(responses_path, self.index_col)

        # self.df = pd.read_csv(responses_path, index_col='respondent_id')

    def get_num_responses(self):
        return len(self.df)


class Combined:

    def __init__(self, sample, responses, questions):
        self.df = sample.df.join(responses.df, how='left')
        self.questions = questions

    def calc_scores(self, summarydf, score_types):
        for question in self.questions.get_scored_questions():
            question_score_response_dict = (self.questions.questionlist[question]).score_responses

            for score in score_types:
                score_column_header = question + scoring_terms[score]['suffix']
                score_responses = question_score_response_dict[score]

                summarydf.loc[summarydf[question].isin(scored_terms), score_column_header] = 0
                summarydf.loc[summarydf[question].isin(score_responses), score_column_header] = 100

        return summarydf

    def get_orgs(self):
        return self.df['trust_id'].unique().tolist()

    def get_summary(self, trust, group_variable, score_type=['pos']):

        columns_summary = [group_variable]
        columns = [group_variable]

        for question in self.questions.get_scored_questions():
            columns_summary.append(question)
            for score in score_type:
                columns.append(question + scoring_terms[score]['suffix'])

        summarydf = self.df[self.df['trust_id'] == trust]
        summarydf = self.calc_scores(summarydf[columns_summary], score_type)

        output_path = Path('C:/Users/steve.baker/PycharmProjects/python-scripts/myproject/app/static/outputs')

        # comparator
        comparator = summarydf[columns].mean().rename('Organisation')

        # groupby
        grouped = summarydf[columns].groupby(group_variable).mean()

        # output to csv
        grouped.append(comparator).to_csv(output_path / f'{trust}_output.csv')

        return output_path / (trust + '_output.csv')
