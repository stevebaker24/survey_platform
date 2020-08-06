from pathlib import Path
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import xlsxwriter

output_path = Path(r'C:\Users\steve.baker\Desktop\MAT Nonsense')

scoring_terms = {'pos': {'value': 1, 'string': 'Positive', 'suffix': '_pos'},
                 'neu': {'value': 2, 'string': 'Neutral', 'suffix': '_neu'},
                 'neg': {'value': 3, 'string': 'Negative', 'suffix': '_neg'},
                 'ignore': {'value': 4, 'string': 'Ignore', 'suffix': None}}

ignore_value = scoring_terms['ignore']['value']
scored_terms = [i['value'] for i in scoring_terms.values()]
scored_terms.remove(ignore_value)
suffixes = ['_pos', '_neu', '_neg']

suppression_threshold = 30

def _input_filetype(path, index_col):
    extension = path.split('.')[-1]
    if extension == "csv":
        return pd.read_csv(path, index_col=index_col)
    if extension == "tsv":
        return pd.read_csv(path, sep='\t', index_col=index_col)
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


def calc_scores(df, questions, score_types=['pos']):
    for question in questions.get_scored_questions():
        question_score_response_dict = question.score_responses
        scored_responses = question.scored_responses

        for score in score_types:
            score_column_header = question.qid + scoring_terms[score]['suffix']
            score_responses = question_score_response_dict[score]

            df.loc[df[question.qid].isin(scored_responses), score_column_header] = 0
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


def get_frequency_table(source, questions, sheet_breakdown_fields=[], file_breakdown_field=None, file_breakdown_values=[]):

    if len(file_breakdown_values) == 0 and file_breakdown_field != None:
        file_breakdown_values = source[file_breakdown_field].unique().tolist()

    if file_breakdown_field == None:
        file_breakdown_values = ['Total']

    for file_breakdown_value in file_breakdown_values:
        if file_breakdown_field == None:
            breakdown_file_df = source
        else:
            breakdown_file_df = source[source[file_breakdown_field] == file_breakdown_value]

        workbook = xlsxwriter.Workbook(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output' + '\\' +  file_breakdown_value.replace("/", "") + '_freq.xlsx')

        question_format = workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_color': '#4d4639'})
        header_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'bold': True, 'text_wrap': True, 'border': 1, 'border_color': 'white',
             'font_name': 'Arial', 'font_color': 'white', 'bg_color': '#5b4173'})
        value_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#4d4639', 'font_name': 'Arial',
             'font_color': '#4d4639'})
        value_total_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#4d4639',
             'font_name': 'Arial', 'font_color': '#4d4639'})
        percent_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#4d4639', 'font_name': 'Arial',
             'font_color': '#4d4639', 'num_format': '0.0'})
        option_format = workbook.add_format(
            {'border': 1, 'border_color': '#4d4639', 'valign': 'vcenter', 'text_wrap': True, 'font_name': 'Arial',
             'font_color': '#4d4639'})
        option_total_format = workbook.add_format(
            {'bold': True, 'border': 1, 'border_color': '#4d4639', 'valign': 'vcenter', 'text_wrap': True,
             'font_name': 'Arial', 'font_color': '#4d4639'})
        subtitle_format = workbook.add_format(
            {'valign': 'vcenter', 'font_name': 'Arial', 'font_color': '#4d4639', 'bold': True})

        if len(sheet_breakdown_fields) == 0:
            sheet_breakdown_fields.append('Total')

        for sheet_breakdown_field in sheet_breakdown_fields:
            worksheet = workbook.add_worksheet(sheet_breakdown_field)

            worksheet.hide_gridlines(2)

            worksheet.set_column('A:A', 1)
            worksheet.set_column('B:B', 50)
            worksheet.set_column('C:Z', 12.29)

            worksheet.set_row(0, 90)

            worksheet.insert_image('B1', r'C:\Users\steve.baker\Desktop\MAT Nonsense\picker.png', {'y_offset': 20, 'x_offset': 2})

            row = 1
            worksheet.write(row, 1, '{SURVEY NAME}', subtitle_format)
            row = 2
            worksheet.write(row, 1, '{FREETEXT TABLES}', subtitle_format)

            row += 3
            column = 2

            if sheet_breakdown_field == 'Total':
                sheet_breakdown_values = ['Total']
            else:
                sheet_breakdown_values = breakdown_file_df[sheet_breakdown_field].unique().tolist()
                sheet_breakdown_values = ['Total'] + sheet_breakdown_values

            for index_sheet_breakdown_value, sheet_breakdown_value in enumerate(sheet_breakdown_values):
                # filter to breakdown_value only
                if sheet_breakdown_value == 'Total' or sheet_breakdown_field == 'Total':
                    breakdown_sheet_value_df = breakdown_file_df
                else:
                    breakdown_sheet_value_df = breakdown_file_df[breakdown_file_df[sheet_breakdown_field] == sheet_breakdown_value]

                # iterate through the questions
                for question in questions.questions_dict.values():
                    q_type = question.q_type

                    if q_type not in ['S', 'M']:
                        continue

                    qid = question.online_qid
                    q_text = question.q_text
                    q_response_options = question.responses

                    if question.scored == 1:
                        scored = True
                        score_map = question.score_map
                        score_responses = question.score_responses
                        if len(score_responses['ignore']) != 0:
                            targeted = True
                        else:
                            targeted = False
                    else:
                        scored = False

                    if q_type == 'M':
                        q_text = f'{q_text} (Multi-response)'
                        qids = []
                        for option in q_response_options:
                            qids.append(f'{qid}_{option}')
                        breakdown_value_total_responses = len(breakdown_sheet_value_df[qids].dropna(how='all'))

                    elif q_type == 'S':
                        breakdown_value_total_responses = (breakdown_sheet_value_df[qid].notnull()).sum()


                    # question title
                    if scored:
                        q_text = f'{q_text} (Scored Question)'


                    if index_sheet_breakdown_value == 0:
                        worksheet.write(row, 1, f"{qid}: {q_text}", question_format)

                    row += 2

                    worksheet.merge_range(row, column, row, column + 1, sheet_breakdown_value, header_format)

                    row += 1

                    if index_sheet_breakdown_value == 0:
                        worksheet.write(row, 1, 'Option', header_format)

                    worksheet.write(row, column, 'Count', header_format)
                    worksheet.write(row, column + 1, '%', header_format)

                    row += 1

                    breakdown_value_total_percent = 0

                    for option_number in q_response_options:
                        if index_sheet_breakdown_value == 0:
                            response_option = q_response_options[option_number]

                            if scored:
                                if option_number in score_responses['pos']:
                                    response_option = f'{response_option} (Positive)'
                                if option_number in score_responses['neu']:
                                    response_option = f'{response_option} (Neutral)'
                                if option_number in score_responses['neg']:
                                    response_option = f'{response_option} (Negative)'
                                if option_number in score_responses['ignore']:
                                    response_option = f'{response_option} (Excluded)'

                            worksheet.write(row, 1, response_option, option_format)

                        if breakdown_value_total_responses < 11:
                            count_option_responses = '*'
                            response_percent = '*'
                            breakdown_value_total_percent = '*'
                        else:
                            if q_type == 'M':
                                count_option_responses = (breakdown_sheet_value_df[f'{qid}_{option_number}'] == 1).sum()
                            elif q_type == 'S':
                                count_option_responses = (breakdown_sheet_value_df[qid] == option_number).sum()

                            response_percent_noround = (count_option_responses / breakdown_value_total_responses) * 100
                            response_percent = round(response_percent_noround, 1)

                            if q_type == 'M':
                                breakdown_value_total_percent = 'N/A'
                            elif q_type == 'S':
                                breakdown_value_total_percent += response_percent_noround

                        worksheet.write(row, column, count_option_responses, value_format)
                        worksheet.write(row, column + 1, response_percent, percent_format)

                        row += 1

                        worksheet.write(row, column + 1, breakdown_value_total_percent, value_total_format)

                        if index_sheet_breakdown_value == 0:
                            worksheet.write(row, 1, 'Total', option_total_format)

                    if breakdown_value_total_responses < 11:
                        worksheet.write(row, column, '*', value_total_format)
                    else:
                        worksheet.write(row, column, breakdown_value_total_responses, value_total_format)

                    row += 3

                    if scored:
                        if targeted:
                            if q_type == 'M':
                                q_text = f'{q_text} (Multi-response)'
                                qids = []
                                for option in q_response_options:
                                    qids.append(f'{qid}_{option}')
                                breakdown_value_total_responses = len(breakdown_sheet_value_df[qids].dropna(how='all'))

                            elif q_type == 'S':
                                breakdown_value_total_responses = (breakdown_sheet_value_df[qid].notnull()).sum()
                                breakdown_value_total_responses = breakdown_value_total_responses - (breakdown_sheet_value_df[qid] == 4).sum()

                            # question title
                            if scored:
                                q_text = f'{q_text} (Scored Question)'

                            if index_sheet_breakdown_value == 0:
                                worksheet.write(row, 1, f"{qid}: {q_text}", question_format)

                            row += 2

                            worksheet.merge_range(row, column, row, column + 1, sheet_breakdown_value, header_format)

                            row += 1

                            if index_sheet_breakdown_value == 0:
                                worksheet.write(row, 1, 'Option', header_format)

                            worksheet.write(row, column, 'Count', header_format)
                            worksheet.write(row, column + 1, '%', header_format)

                            row += 1

                            breakdown_value_total_percent = 0

                            for option_number in q_response_options:
                                if index_sheet_breakdown_value == 0:
                                    response_option = q_response_options[option_number]

                                    if scored:
                                        if option_number in score_responses['pos']:
                                            response_option = f'{response_option} (Positive)'
                                        if option_number in score_responses['neu']:
                                            response_option = f'{response_option} (Neutral)'
                                        if option_number in score_responses['neg']:
                                            response_option = f'{response_option} (Negative)'
                                        if option_number in score_responses['ignore']:
                                            response_option = f'{response_option} (Excluded)'
                                            continue

                                    worksheet.write(row, 1, response_option, option_format)

                                if breakdown_value_total_responses < 11:
                                    count_option_responses = '*'
                                    response_percent = '*'
                                    breakdown_value_total_percent = '*'
                                else:
                                    if q_type == 'M':
                                        count_option_responses = (
                                                    breakdown_sheet_value_df[f'{qid}_{option_number}'] == 1).sum()
                                    elif q_type == 'S':
                                        count_option_responses = (breakdown_sheet_value_df[qid] == option_number).sum()

                                    response_percent_noround = (
                                                                           count_option_responses / breakdown_value_total_responses) * 100
                                    response_percent = round(response_percent_noround, 1)

                                    if q_type == 'M':
                                        breakdown_value_total_percent = 'N/A'
                                    elif q_type == 'S':
                                        breakdown_value_total_percent += response_percent_noround

                                worksheet.write(row, column, count_option_responses, value_format)
                                worksheet.write(row, column + 1, response_percent, percent_format)

                                row += 1

                                worksheet.write(row, column + 1, breakdown_value_total_percent, value_total_format)

                                if index_sheet_breakdown_value == 0:
                                    worksheet.write(row, 1, 'Total', option_total_format)

                            if breakdown_value_total_responses < 11:
                                worksheet.write(row, column, '*', value_total_format)
                            else:
                                worksheet.write(row, column, breakdown_value_total_responses, value_total_format)

                            row += 3


                column = column + 2
                row = 5

        workbook.close()


def get_freetext(source, questions, sheet_breakdown_fields=['Total'], file_breakdown_field=None, file_breakdown_values=[]):
    if len(file_breakdown_values) == 0 and file_breakdown_field != None:
        file_breakdown_values = source[file_breakdown_field].unique().tolist()

    if file_breakdown_field == None:
        file_breakdown_values = ['Total']

    for file_breakdown_value in file_breakdown_values:
        if file_breakdown_field == None:
            breakdown_file_df = source
        else:
            breakdown_file_df = source[source[file_breakdown_field] == file_breakdown_value]

        workbook = xlsxwriter.Workbook(
            r'C:\Users\steve.baker\Desktop\MAT Nonsense\output' + '\\' + file_breakdown_value.replace("/", "") + '_text.xlsx')

        for sheet_breakdown_field in sheet_breakdown_fields:

            if sheet_breakdown_field == 'Total':
                no_breakdown = True
            else:
                no_breakdown = False


            if no_breakdown:
                if len(breakdown_file_df) < 30:
                    supp = True
                else:
                    supp = False
            else:
                group = breakdown_file_df[[sheet_breakdown_field, 'Trust code']].groupby(sheet_breakdown_field).count()
                suppress_list = group.index[group['Trust code'] < 30].tolist()


            worksheet = workbook.add_worksheet(sheet_breakdown_field)

            column = 0

            for i, question in enumerate(questions.text_response_questions):



                qid = question.online_qid
                q_text = question.q_text

                if no_breakdown:
                    columns = []
                else:
                    columns = [sheet_breakdown_field]

                columns.append(qid)

                if no_breakdown:
                    worksheet.write(0, column, qid)
                else:
                    worksheet.write(0, column, sheet_breakdown_field)
                    worksheet.write(0, column+1, qid)

                row = 1

                question_df = breakdown_file_df[columns].dropna()
                number_of_responses = len(question_df)

                for response in question_df.iterrows():
                    if no_breakdown:
                        if supp:
                            worksheet.write(row, column, '*')
                        else:
                            worksheet.write(row, column, response[1][0])

                    else:
                        if response[1][0] in suppress_list:
                            worksheet.write(row, column, response[1][0])
                            worksheet.write(row, column+1, '*')
                        else:
                            worksheet.write(row, column, response[1][0])
                            worksheet.write(row, column+1, response[1][1])
                    row += 1

                if no_breakdown:
                    column = column + 1
                else:
                    column = column + 2


        workbook.close()


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

    def __init__(self, sample_path, indexcol):
        self.df = _input_filetype(sample_path, indexcol)

    def get_orgs(self):
        return self.df['Trust code'].unique().tolist()


class Responses:

    def __init__(self, responses_path, indexcol):
        self.df = _input_filetype(responses_path, indexcol)


class Combined:

    def __init__(self, sample, responses):
        self.df = sample.df.join(responses.df.set_index('PRN'), how='left')


class Questions:

    def __init__(self, question_path):
        self.df = pd.DataFrame()
        self.catergory_dict = {}
        self.questions_dict = {}
        self.scored_questions = []
        self.single_response_questions = []
        self.multi_response_questions = []
        self.text_response_questions = []

        extension = question_path.split('.')[-1]
        if extension == 'csv':
            self.df = pd.read_csv(question_path)
        elif extension == 'xlsx':
            self.df = pd.read_excel(question_path, sheet_name='Question Info')

        self._generate_question_lists()


    def __iter__(self):
        return iter(self.questions_dict.values())

    def __len__(self):
        return len(self.questions_dict)

    def get_scored_questions(self):
        return self.scored_questions

    def _generate_question_lists(self):
        score_indices = [i for i, elem in enumerate(list(self.df.columns)) if 'S_' in elem[0:2]]
        response_indices = [i for i, elem in enumerate(list(self.df.columns)) if 'R_' in elem[0:2]]

        for row in self.df.iterrows():
            question_object = Question(row, score_indices, response_indices)

            self.questions_dict[row[1]['QVAR']] = question_object

            if row[1]['CATEGORY'] in self.catergory_dict.keys():
                self.catergory_dict[row[1]['CATEGORY']].append(question_object)
            else:
                self.catergory_dict[row[1]['CATEGORY']] = [question_object]

            if row[1]['SCORED'] == 1:
                self.scored_questions.append(question_object)

            if row[1]['TYPE'] == 'S':
                self.single_response_questions.append(question_object)
            elif row[1]['TYPE'] == 'M':
                self.multi_response_questions.append(question_object)


            elif row[1]['TYPE'] == 'F':
                self.text_response_questions.append(question_object)

        return None

class Question:

    def __init__(self, q_row, score_indices, response_indices):
        self.row = q_row
        self.qid = q_row[1]['QVAR']
        self.q_sort_int = q_row[0]
        self.q_text = q_row[1]['QTEXT_FULL']
        self.q_pos_text = q_row[1]['QTEXT_POSTEXT']
        self.q_type = q_row[1]['TYPE']
        self.scored = q_row[1]['SCORED']
        self.category = q_row[1]['CATEGORY']
        self.online_qid = q_row[1]['ONLINE_QID']
        self.paper_qid = q_row[1]['PAPER_QID']

        self.score_map = self.get_score_map(q_row[1], score_indices)
        self.responses = self.get_response_map(q_row[1], response_indices)
        self.score_responses = self.get_score_responses(q_row[1], score_indices)
        self.scored_responses = self.get_scored_responses(q_row[1], score_indices)


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
    def get_scored_responses(q_row, score_indicies):

        mylist = []

        for i, x in enumerate(q_row[(score_indicies[0]):(score_indicies[-1])]):
            if x == scoring_terms['pos']['value']:
                mylist.append(i)

            elif x == scoring_terms['neu']['value']:
                mylist.append(i)

            elif x == scoring_terms['neg']['value']:
                mylist.append(i)

        return mylist

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
