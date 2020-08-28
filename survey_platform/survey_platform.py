from pathlib import Path

from survey_platform import config

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import xlsxwriter

#temp stuff
suppression_threshold = 30
suppression_framework = 'patient'

survey_periods = {
    'P': '2020',
    'P-1': '2019',
    'P-2': '2018',
    'P-3': '2017',
    'P-4': '2016'
}

#setup
output_path = Path(config.output_path)

scoring_terms_dict = config.scoring_terms_dict
scoring_ignore_value = scoring_terms_dict['ignore']['value']

scored_values = [scoring_terms_dict[i]['value'] for i in scoring_terms_dict if i != 'ignore']
score_suffixes = [scoring_terms_dict[i]['suffix'] for i in scoring_terms_dict if i != 'ignore']

def add(a, b):
    return a + b

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
    for question in questions.scored_questions:
        topic_dict[question.get_qid() + scoring_terms_dict[score_type]['suffix']] = questions.questions_dict[question.get_qid()].category

        columns_for_scoring.append(question.get_qid())
        columns_output.append(question.get_qid() + scoring_terms_dict[score_type]['suffix'])

    # check type of input, either reporting, survey or just a df
    if isinstance(source, Reporting):
        df = (source.df[source.df[seperate_by_field] == seperator])[columns_output]
    elif isinstance(source, Survey):
        df = (source.reporting.df[source.reporting.df[seperate_by_field] == seperator])[columns_output]
    else:
        df = (source[source[seperate_by_field] == seperator])[columns_for_scoring]
        df = calc_scores(df, questions, [score_type])[columns_output]


    df_mean = df.groupby(group_by).mean().transpose()
    df_count = df.groupby(group_by).count().transpose()

    # suppression
    suppression_mask = df_count < 11
    df_mean_suppressed = df_mean.mask(suppression_mask)

    overall_df_mean = df_mean_suppressed.mean(axis=1).rename('Overall')
    overall_df_count = df_count.sum(axis=1).rename('Overall')

    combined_df_mean_suppressed = df_mean_suppressed.join(overall_df_mean)
    combined_df_count = df_count.join(overall_df_count)



    # write to excel
    writer = pd.ExcelWriter(output_path/f'{seperator}_RAG_{group_by}.xlsx', engine='xlsxwriter')
    (combined_df_mean_suppressed/100).replace(np.nan, '*').to_excel(writer, sheet_name='Sheet1')
    worksheet = writer.sheets['Sheet1']
    writer.save()

    return output_path / f'{seperator}_RAG_{group_by}.xlsx'


def get_frequency_table(source, questions, suppression_threshold, sheet_breakdown_fields=[], file_breakdown_field=None, file_breakdown_values=[]):

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
            worksheet.write(row, 1, 'Picker New Mother Experiecne of Care Survey 2020', subtitle_format)
            row = 2
            worksheet.write(row, 1, 'Frequency Tables Report', subtitle_format)

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
                targeted_questions = []

                for question in questions.questions_dict.values():
                    q_type = question.q_type

                    if q_type not in ['S', 'M']:
                        continue

                    qid = question.qid
                    q_text = question.q_text
                    q_response_options = question.responses

                    scored = question.scored

                    if scored:
                        score_map = question.score_map
                        score_responses = question.score_responses
                        if question.targeted:
                            targeted_questions.append(question)

                    def calcualte_breakdown_value_total_responses(q_type, q_text, q_response_options, breakdown_sheet_value_df):
                        #calculate total vaue for the breakdown
                        if q_type == 'M':
                            qids = []
                            for option in q_response_options:
                                qids.append(f'{qid}_{option}')
                            breakdown_value_total_responses = len(breakdown_sheet_value_df[qids].dropna(how='all'))

                        elif q_type == 'S':
                            breakdown_value_total_responses = (breakdown_sheet_value_df[qid].notnull()).sum()

                        return breakdown_value_total_responses

                    breakdown_value_total_responses = calcualte_breakdown_value_total_responses(q_type, q_text, q_response_options, breakdown_sheet_value_df)

                    #if the first of the breakdowns
                    if index_sheet_breakdown_value == 0:

                        if q_type == 'M':
                            q_text = f'{q_text} (Multi-response)'
                        if scored:
                            q_text = f'{q_text} (Scored Question)'

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

                        if breakdown_value_total_responses < suppression_threshold:
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

                    if breakdown_value_total_responses < suppression_threshold:
                        worksheet.write(row, column, '*', value_total_format)
                    else:
                        worksheet.write(row, column, breakdown_value_total_responses, value_total_format)

                    row += 3






                worksheet.write(row, 1, 'Targeted Questions', question_format)
                row += 3







                for question in targeted_questions:
                    q_type = question.q_type

                    if q_type not in ['S', 'M']:
                        continue

                    qid = question.qid
                    q_text = question.q_text
                    q_response_options = question.responses

                    scored = question.scored

                    if scored:
                        score_map = question.score_map
                        score_responses = question.score_responses
                        q_text = f'{q_text} (Scored Question)'
                        scored_responses = question.scored_responses


                    #calculate total vaue for the breakdown
                    if q_type == 'M':
                        q_text = f'{q_text} (Multi-response)'
                        qids = question.scored_columns
                        breakdown_value_total_responses = len(breakdown_sheet_value_df[qids].dropna(how='all'))

                    elif q_type == 'S':
                        breakdown_value_total_responses = breakdown_sheet_value_df[qid].isin(scored_responses).sum()

                    #if the first of the breakdowns
                    if index_sheet_breakdown_value == 0:
                        worksheet.write(row, 1, f"{qid} Targeted: {q_text}", question_format)

                    row += 2

                    worksheet.merge_range(row, column, row, column + 1, sheet_breakdown_value, header_format)

                    row += 1

                    if index_sheet_breakdown_value == 0:
                        worksheet.write(row, 1, 'Option', header_format)

                    worksheet.write(row, column, 'Count', header_format)
                    worksheet.write(row, column + 1, '%', header_format)

                    row += 1

                    breakdown_value_total_percent = 0

                    for option_number in scored_responses:
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
                                    continue


                            worksheet.write(row, 1, response_option, option_format)

                        if breakdown_value_total_responses < suppression_threshold:
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

                    if breakdown_value_total_responses < suppression_threshold:
                        worksheet.write(row, column, '*', value_total_format)
                    else:
                        worksheet.write(row, column, breakdown_value_total_responses, value_total_format)

                    row += 3


                column = column + 2
                row = 5

        workbook.close()


def get_freetext(source, questions, sheet_breakdown_fields=['Total'], file_breakdown_field=None, file_breakdown_values=[], suppression_threshold=None, suppression_framework=None):
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

            no_breakdown = True if sheet_breakdown_field == 'Total' else False

            suppress_list=[]
            if suppression_framework == 'pateint':
                if no_breakdown:
                    supp = true if len(breakdown_file_df) < suppression_threshold else False
                else:
                    group = breakdown_file_df[[sheet_breakdown_field, file_breakdown_field]].groupby(sheet_breakdown_field).count()
                    suppress_list = group.index[group[file_breakdown_field] < suppression_threshold].tolist()


            worksheet = workbook.add_worksheet(sheet_breakdown_field)

            column = 0

            for i, question in enumerate(questions.text_response_questions):


                qid = question.qid
                q_text = question.q_text
                header = f'{question.qid} - {q_text}'



                if no_breakdown:
                    columns = []
                else:
                    columns = [sheet_breakdown_field]

                columns.append(qid)

                if no_breakdown:
                    worksheet.write(0, column, header)
                else:
                    worksheet.write(0, column, sheet_breakdown_field)
                    worksheet.write(0, column+1, header)

                row = 1

                question_df = breakdown_file_df[columns].sort_values(by=[sheet_breakdown_field])\
                                                        .dropna()

                if suppression_framework == 'staff':
                    if no_breakdown:
                        supp = true if len(question_df) < suppression_threshold else False

                    else:
                        group = question_df.groupby(sheet_breakdown_field).count()
                        suppress_list = group.index[group[qid] < suppression_threshold].tolist()

                number_of_responses = len(question_df)

                for response in question_df.iterrows():

                    group = response[1][0]
                    response_text = response[1][1]

                    if no_breakdown:
                        if supp:
                            worksheet.write(row, column, '{COMMENT SUPPRESSED}')
                        else:
                            worksheet.write(row, column, group)

                    else:
                        if group in suppress_list:
                            worksheet.write(row, column, group)
                            worksheet.write(row, column+1, '{COMMENT SUPPRESSED}')
                        else:
                            worksheet.write(row, column, group)
                            worksheet.write(row, column+1, response_text)
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

    def __init__(self, responses_path, indexcol, period=None, questions=None, breakdown_field=None, breakdown_field_values=None, master_breakdown_field=None):
        self.df = _input_filetype(responses_path, indexcol)
        # if period is None:
        #     self.df = _input_filetype(responses_path, indexcol)
        #
        # else:
        #     df = _input_filetype(responses_path, indexcol)
        #
        #     # rename historic questions
        #     p_questions = questions.get_questions('P')
        #     period_questions = questions.get_questions(period)
        #
        #     p_question_columns = [question.get_question_columns('P') for question in p_questions]
        #     p_question_columns = [item for sublist in p_question_columns for item in sublist]
        #
        #     period_question_columns = [question.get_question_columns(period) for question in period_questions]
        #     period_question_columns = [item for sublist in period_question_columns for item in sublist]
        #
        #     # identify columns which could be ambiguous and drop from df
        #     for column in df.columns:
        #         if (column in p_question_columns) and (column not in period_question_columns):
        #             df = df.drop(column, axis=1)
        #
        #     #reaplce column header:
        #     for question in period_questions:
        #         if question.get_qid(period) != question.get_qid('P'):
        #
        #             for i, column in enumerate(question.get_question_columns(period)):
        #                 replacement_column = question.get_question_columns("P")[i]
        #                 df.columns = df.columns.str.replace(f'^{column}$', f'{replacement_column}')
        #
        #     self.df = df

class Combined:

    def __init__(self, sample, responses):
        self.df = sample.df.join(responses.df.set_index('PRN'), how='left')


class Questions:

    def __init__(self, question_path):
        self.df = pd.read_excel(question_path, sheet_name='Question Info')

        self.hist_dfs = {}
        for period in survey_periods:
            if period != 'P':
                self.hist_dfs[period] = pd.read_excel(question_path, sheet_name=period)

        self.questions_dict = {}
        for period in survey_periods:
            self.questions_dict[period] = []

        self.catergory_dict = {}
        # self.questions_dict = {}

        self.scored_questions = []

        self.single_response_questions = []
        self.multi_response_questions = []
        self.text_response_questions = []

        self._generate_question_lists()

        # self._columns_to_score = self._get_columns_to_score()

    def get_questions (self, period='P'):
        return self.questions_dict[period]

    def __iter__(self):
        return iter(self.questions_dict['P'])

    def __len__(self):
        return len(self.questions_dict['P'])


    # def _get_columns_to_score(self):
    #     columns = []
    #     for question in self.scored_questions:
    #         columns = columns + question.question_columns
    #     return columns

    def _generate_question_lists(self):
        score_indices = [i for i, elem in enumerate(list(self.df.columns)) if 'S_' in elem[0:2]]
        response_indices = [i for i, elem in enumerate(list(self.df.columns)) if 'R_' in elem[0:2]]

        historic_score_indicies = [i for i, elem in enumerate(list(self.hist_dfs[list(self.hist_dfs.keys())[0]].columns)) if 'S_' in elem[0:2]]
        historic_response_indicies = [i for i, elem in enumerate(list(self.hist_dfs[list(self.hist_dfs.keys())[0]].columns)) if 'R_' in elem[0:2]]


        for row in self.df.iterrows():

            row = row[1]
            qid = row['QVAR']

            question_hist_rows = {}
            for period in self.hist_dfs:
                df = self.hist_dfs[period]
                series = (df.loc[df['QVAR']==qid]).iloc[0]
                if isinstance(series['PQVAR'], float) and np.isnan(series['PQVAR']):
                    pass
                else:
                    question_hist_rows[period] = series

            #generate_question_object
            question_object = Question(row, score_indices, response_indices, historic_score_indicies, historic_response_indicies, question_hist_rows)

            # self.questions_dict[question_object.get_qid()] = question_object

            if question_object.category in self.catergory_dict.keys():
                self.catergory_dict[question_object.category].append(question_object)
            else:
                self.catergory_dict[question_object.category] = [question_object]


            if question_object.scored == 1:
                self.scored_questions.append(question_object)

            self.questions_dict['P'].append(question_object)
            for period in question_hist_rows:
                self.questions_dict[period].append(question_object)

            if question_object.q_type == 'S':
                self.single_response_questions.append(question_object)
            elif question_object.q_type == 'M':
                self.multi_response_questions.append(question_object)
            elif question_object.q_type == 'F':
                self.text_response_questions.append(question_object)



        return None

class Question:

    def __init__(self, q_row, score_indices, response_indices, historic_score_indicies, historic_response_indicies, historic_rows):
        self._qid = {'P': q_row['QVAR']}

        self.q_text = q_row['QTEXT_FULL']
        self.q_pos_text = q_row['QTEXT_POSTEXT']
        self.q_type = q_row['TYPE']
        self.scored = True if q_row['SCORED'] == 1 else False
        self.category = q_row['CATEGORY']
        self.online_qid = q_row['ONLINE_QID']
        self.paper_qid = q_row['PAPER_QID']

        #map of response text to each response option
        self._responses = {'P': self._create_response_map(q_row, response_indices)}

        #map of score for each response option
        self._score_map = {'P': self._create_score_map(q_row, score_indices)}
        # all scored responses
        self._scored_responses = {'P': self._create_scored_responses(self._score_map['P'])}
        # responses whos result contributes to a particular score
        self._score_responses = {'P': self._create_score_responses(self._score_map['P'])}


        #all columns which belong to this question
        self._question_columns = {'P': self._create_question_columns(self._qid['P'], self.q_type, self._responses['P'])}
        # columns which are invovled in scoring (excluding ignore)
        self._score_columns_dict= {'P': self._screate_score_columns_dict(self._qid['P'], self.q_type, self._score_responses['P'])}
        # columns whos result contributes to a particular score
        self._scored_columns = {'P': self._create_scored_columns(self._qid['P'], self.q_type, self._scored_responses['P'])}

        self.targeted = True if len(self._score_responses['P']['ignore']) > 0 else False

        self.has_historic = True if len(historic_rows) > 0 else False

        if self.has_historic:
            for period in historic_rows:
                historical_row = historic_rows[period]

                if historical_row['PDIFF'] == 1:
                    my_row = historical_row
                    using_response_indices = historic_response_indicies
                    using_score_indicies = historic_score_indicies
                else:
                    my_row = q_row
                    using_response_indices = response_indices
                    using_score_indicies = score_indices

                self._qid[period] = historical_row['PQVAR']

                self._responses[period] = self._create_response_map(my_row, using_response_indices)
                self._score_map[period] = self._create_score_map(my_row, using_score_indicies)

                self._scored_responses[period] = self._create_scored_responses(self._score_map[period])
                self._score_responses[period] = self._create_score_responses(self._score_map[period])

                self._question_columns[period] = self._create_question_columns(self._qid[period], self.q_type, self._responses[period])
                self._scored_columns[period] = self._create_scored_columns(self._qid[period], self.q_type, self._scored_responses[period])

                self._score_columns_dict[period] = self._screate_score_columns_dict(self._qid[period], self.q_type, self._score_responses[period])

    #getters
    def get_qid(self, period='P'):
        return self._qid[period]

    def get_responses(self, period='P'):
        return self._responses[period]

    def get_score_map(self, period='P'):
        return self._score_map[period]

    def get_scored_responses(self, period='P'):
        return self._scored_responses[period]

    def get_score_responses(self, period='P'):
        return self._score_responses[period]

    def get_question_columns(self, period='P'):
        return self._question_columns[period]

    def get_score_columns(self, period='P'):
        return self._score_columns_dict[period]

    def get_scored_columns(self, period='P'):
        return self._scored_columns[period]



    @staticmethod
    def _create_response_map(q_row, response_indices):
        mydict = {}
        for i, x in enumerate(q_row[(response_indices[0]):(response_indices[-1])+1]):
            if isinstance(x, str):
                mydict[i] = x
        return mydict

    @staticmethod
    def _create_score_map(q_row, score_indicies):
        mydict = {}
        for i, x in enumerate(q_row[(score_indicies[0]):(score_indicies[-1])+1]):
            if not np.isnan(x):
                mydict[i] = int(x)
        return mydict

    @staticmethod
    def _create_score_responses(score_map):
        mydict = {'pos': [],
                  'neu': [],
                  'neg': [],
                  'ignore': []
                  }

        for scoring_term in scoring_terms_dict:
            for response_option in score_map:
                # add to correct value
                if score_map[response_option] == scoring_terms_dict[scoring_term]['value']:
                    mydict[scoring_term].append(response_option)

        return mydict

    @staticmethod
    def _create_scored_responses(score_map):
        mylist = []
        for response_option in score_map:
            # if not an ignore vale
            if score_map[response_option] != scoring_ignore_value:
                mylist.append(response_option)
        return mylist

    @staticmethod
    def _create_question_columns(qid, q_type, responses):
        mylist=[]
        if q_type == 'M':
            for option in responses:
                mylist.append(f'{qid}_{option}')
        elif q_type == 'S':
            mylist.append(qid)
        return mylist

    @staticmethod
    def _create_scored_columns(qid, q_type, scored_responses):
        mylist = []
        if q_type == 'M':
            for response_option in scored_responses:
                mylist.append(f'{qid}_{response_option}')
        elif q_type == 'S':
            mylist.append(qid)
        return mylist

    @staticmethod
    def _screate_score_columns_dict(qid, q_type, score_responses):
        score_columns = {'pos': [],
                         'neu': [],
                         'neg': [],
                         'ignore': []}

        if q_type == 'M':
            for score_type in score_responses:
                for x in score_responses[score_type]:
                    score_columns[score_type].append(f'{qid}_{x}')

        return score_columns


class Reporting:

    def __init__(self, combined, questions):
        self.df = calc_scores(combined.df, questions, score_types=['pos', 'neu', 'neg'])
