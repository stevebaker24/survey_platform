from pathlib import Path
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import xlsxwriter

output_path = Path('C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/outputs')

scoring_terms = {'pos': {'value': 1, 'string': 'Positive', 'suffix': '_pos'},
                 'neu': {'value': 2, 'string': 'Neutral', 'suffix': '_neu'},
                 'neg': {'value': 3, 'string': 'Negative', 'suffix': '_neg'},
                 'ignore': {'value': 4, 'string': 'Ignore', 'suffix': None}}

ignore_value = scoring_terms['ignore']['value']
scored_terms = [i['value'] for i in scoring_terms.values()]
scored_terms.remove(ignore_value)
suppression_threshold = 1000

def _input_filetype(path, index_col):
    extension = path.split('.')[-1]
    if extension == "csv":
        return pd.read_csv(path, index_col=index_col)
    elif extension == "parquet":
        return pd.read_parquet(path, engine='pyarrow')


def calc_scores(df, questions, score_types=['pos']):
    for question in questions.get_scored_questions():
        question_score_response_dict = question.score_responses

        for score in score_types:
            score_column_header = question.qid + scoring_terms[score]['suffix']
            score_responses = question_score_response_dict[score]

            df.loc[df[question.qid].isin(scored_terms), score_column_header] = 0
            df.loc[df[question.qid].isin(score_responses), score_column_header] = 100

    return df


def get_rag(source,
            seperate_by_field='trust_id',
            seperator=None,
            group_by=None,
            questions=None,
            score_type='pos'):

    #check for single layer or multi group by
    if isinstance(group_by, str):
        columns_for_scoring, columns_output = [group_by], [group_by]
        number_groups = 1
    elif isinstance(group_by, list):
        columns_for_scoring, columns_output = group_by.copy(), group_by.copy()
        number_groups = len(group_by)

    #iteratre trough questions to select columns and theme mapping
    topic_dict = {}
    for question in questions.get_scored_questions():
        topic_dict[question.qid + scoring_terms[score_type]['suffix']] = questions.questions_dict[question.qid].theme

        columns_for_scoring.append(question.qid)
        columns_output.append(question.qid + scoring_terms[score_type]['suffix'])

    # check type of input, either reporting, survey or just a df
    if isinstance(source, Reporting):
        df = (source.df[source.df[seperate_by_field] == seperator])[columns_output]
    elif isinstance(source, Survey):
        df = (source.reporting.df[source.reporting.df[seperate_by_field] == seperator])[columns_output]
    else:
        df = (source[source[seperate_by_field] == seperator])[columns_for_scoring]
        df = calc_scores(df, questions, [score_type])[columns_output]


    #unpivot data
    melteddf = df.melt(id_vars=group_by)

    #map on the question topics
    melteddf['topic'] = melteddf['variable'].map(topic_dict)

    #main frame
    df_main = melteddf.pivot_table(index=['topic', 'variable'],
                                     columns=group_by ,
                                     values='value',
                                     aggfunc=['count', np.sum],
                                     margins=True)

    #by theme subtotals
    df_theme = df_main.groupby('topic').sum().drop('All') # no need for all on both when combining
    df_theme['newcolumn'] = df_theme.index #for alphabetical sorting
    df_theme = df_theme.set_index('newcolumn', append=True)
    #append
    hello = df_main.append(df_theme).sort_index()

    #calculate mean
    hi = hello['sum']/hello['count']

    # suppression
    suppression_mask = hello['count'] < suppression_threshold
    hi = hi.mask(suppression_mask)

    # write to excel
    writer = pd.ExcelWriter(output_path/f'{seperator}_RAG.xlsx', engine='xlsxwriter')
    hi.replace(np.nan, '*').to_excel(writer, sheet_name='Sheet1')
    worksheet = writer.sheets['Sheet1']
    writer.save()

    return output_path / f'{seperator}_RAG.xlsx'

def get_freq_tables(trust, combined, questions):
    df = combined[combined['trust_id'] == trust]

    for question in questions.single_response_questions:
        print(df[question.qid].value_counts().sort_index())

    #currently does not include vlaues which have no responses...

def get_freetext(trust, combined, questions):
    df = combined[combined['trust_id'] == trust]

    for question in questions.text_response_questions:
        print(df[question.qid].dropna().reset_index(drop=True))

    # currently does not include vlaues which have no responses...

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
        #self.reporting = Reporting(self.combined, self.questions)


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


class Questions:

    def __init__(self, question_path):
        self.df = pd.read_csv(question_path)
        self.theme_dict = {}
        self.questions_dict = {}
        self.scored_questions = []
        self.single_response_questions = []
        self.multi_response_questions = []
        self.text_response_questions = []
        self._generate_question_lists()

    def __iter__(self):
        return iter(self.questions_dict.values())

    def __len__(self):
        return len(self.questions_dict)

    def get_scored_questions(self):
        return self.scored_questions

    def _generate_question_lists(self):
        score_indices = [i for i, elem in enumerate(list(self.df.columns)) if 's_' in elem[0:2]]
        response_indices = [i for i, elem in enumerate(list(self.df.columns)) if 'r_' in elem[0:2]]

        for row in self.df.iterrows():
            question_object = Question(row, score_indices, response_indices)

            self.questions_dict[row[1]['qid']] = question_object

            if row[1]['theme'] in self.theme_dict.keys():
                self.theme_dict[row[1]['theme']].append(question_object)
            else:
                self.theme_dict[row[1]['theme']] = [question_object]

            if row[1]['scored'] == 1:
                self.scored_questions.append(question_object)

            if row[1]['q_type'] == 's':
                self.single_response_questions.append(question_object)
            elif row[1]['q_type'] == 'm':
                self.multi_response_questions.append(question_object)
            elif row[1]['q_type'] == 't':
                self.text_response_questions.append(question_object)

        return None

class Question:

    def __init__(self, q_row, score_indices, response_indices):
        self.row = q_row
        self.qid = q_row[1]['qid']
        self.q_sort_int = q_row[0]
        self.q_text = q_row[1]['q_text']
        self.q_pos_text = q_row[1]['pos_text']
        self.q_type = q_row[1]['q_type']
        self.scored = q_row[1]['scored']
        self.theme = q_row[1]['theme']

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
        # can use dict comprehension with conditional but might be too long. Can also use generator. 
        # {i: int(x) for for i, x in enumerate(q_row[(score_indicies[0]):(score_indicies[-1])])

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
