import report
import report_config
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

from xlsxwriter.utility import xl_rowcol_to_cell

from report import get_agg_df


class SesReport(report.Report):
    def __init__(self, source, output_path, questions, sheet_breakdown_fields, suppression_threshold, survey_name,
                 external_comparator=None, external_comparator_n=None, comparator_text=None, report_name=None,
                 file_name=None,
                 overall_text=None):
        self.workbook_class = SesWorkbook
        self.worksheet_class = SesWorksheet
        self.file_name = 'SES_Report'
        self.report_name = 'SES_Report'
        super().__init__(source, output_path, questions, sheet_breakdown_fields, suppression_threshold,
                         external_comparator=external_comparator, external_comparator_n=external_comparator_n,
                         comparator_text=comparator_text,
                         overall_text=overall_text, survey_name=survey_name, report_name=report_name,
                         file_name=file_name)


class SesWorkbook(report.ReportWorkbook):

    def __init__(self, parent_report):
        self.format_dict = report_config.FORMATS
        self.sesmap = {5: 10, 4: 7.5, 3: 5, 2: 2.5, 1: 0}
        self.ses_questions_dict = {'Advocacy': ['Q18c', 'Q18d', 'Q18a'], 'Involvement': ['Q4b', 'Q4a', 'Q4d'],
                                   'Motivation': ['Q2a', 'Q2b', 'Q2c']}

        super().__init__(parent_report)

    def calculate_workbook_data(self, df):
        mapped = ses_map_data(df, self.question_fields, self.sesmap)

        self.total_mean = create_total_ses_df(mapped, None, self.ses_questions_dict,
                                              self.parent_report.suppression_threshold)[1]

        return mapped

    def get_question_fields(self) -> list:
        """Gets a list of questions from the ses_questrions dictionary of structure {'Category': [List of Qs]}"""
        return ses_get_question_fields(self.ses_questions_dict)

    def create_guidance_page(self):
        guidance_sheet = self.workbook.add_worksheet('Guidance')
        guidance_sheet.merge_range(6, 1, 6, 13, 'Staff Engagement Report Guidance', self.formats['RAG_GUIDANNCE_BOLD'])
        guidance_sheet.merge_range(7, 1, 7, 13,
                                   'This report shows staff engagement scores by each of the breakdown categories across each worksheet. These scores are visually compared to the comparator by RAG colouring. It is a dynamic report you can adjust to get the maximum insight from your data.',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(8, 1, 8, 13,
                                   'By default, the RAG comparison is set to 0.4 or more points difference between the scores. Red differences are where the scores are more than this value below the comparator, green differences are more than this value above the comparator. The percentage point difference value can be adjusted by changing the value in cell B6. For example, to highlight all differences of 0.8 points or more adjust cell B6 to 0.8',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(9, 1, 9, 13,
                                   'Staff engagement scores are calculated for key questions from the survey, grouped into three categories. The maximum possible score is 10 (all respondents answer most positively e.g. "Strongly agree“) and the lowest possible score is 0 (all respondents answer most negatively e.g. "Strongly disagree"). The engagement score for each category is an average of its three respective question scores. The overall staff engagement score is the average of the scores for all categories.',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(10, 1, 10, 13,
                                   'If there is a suppression threshold for your survey, where there are less than this many responses to a question (or zero), the respective scores are replaced with an asterisk (*). The overall Staff Engagement Score will only be displayed if there are a sufficient number of respondents to all of the 9 questions.',
                                   self.formats['RAG_GUIDANNCE'])

        guidance_sheet.set_row(7, 54)
        guidance_sheet.set_row(8, 73)
        guidance_sheet.set_row(9, 73)
        guidance_sheet.set_row(10, 51)

        guidance_sheet.insert_image('B2', report_config.LOGO_PATH, {'y_offset': 10, 'x_offset': 0})

        guidance_sheet.hide_gridlines(2)


class SesWorksheet(report.ReportWorksheet):

    def __init__(self, sheet_data, worksheet, sheet_breakdown, parent_workbook):
        super().__init__(sheet_data, worksheet, sheet_breakdown, parent_workbook)

        # only include people who answered at least one of the SES questions
        self.sheet_data = sheet_data

        self.worksheet.hide_gridlines(2)
        self.worksheet.set_column('A:A', 30)
        self.worksheet.set_column('B:B', 10)
        self.worksheet.set_column('C:C', 60)
        self.worksheet.set_column('D:ZZ', 18.5)

        self.worksheet.set_zoom(75)

        self.worksheet.insert_image('A1', report_config.LOGO_PATH,
                                    {'y_offset': 15, 'x_offset': 10, 'x_scale': 0.85, 'y_scale': 0.85})

        self.worksheet.freeze_panes(self.number_of_breakdowns + 7, 4)

        for i in range(self.number_of_breakdowns):
            self.worksheet.set_row(i + 6, 45)

        # worksheet Title Section
        self.worksheet.write(1, 2, self.survey_name, self.formats['SUBTITLE'])
        self.worksheet.write(2, 2, self.parent_workbook.parent_report.report_name, self.formats['SUBTITLE'])
        self.worksheet.write(3, 2, f'Breakdown: {self.breakdown_text}', self.formats['SUBTITLE'])
        self.worksheet.write(4, 2, f'Suppression Threshold: {self.parent_workbook.parent_report.suppression_threshold}',
                             self.formats['SUBTITLE'])

        ##SES set point
        self.worksheet.write(5, 0, 'Set RAG point difference:', self.formats['RAG_SET_POINT_TEXT'])
        # write default pp difference value (aboslute value to use in formulas)
        abs_pp_cell = xl_rowcol_to_cell(5, 1, col_abs=True, row_abs=True)
        self.worksheet.write(abs_pp_cell, 0.4, self.formats['SET_PERCENT'])

        # Key
        self.worksheet.write(0, 3, 'Key:', self.formats['SUBTITLE_CENTER'])
        self.worksheet.write(1, 3, 10, self.formats['SES_10'])
        self.worksheet.write(2, 3, f'=">" & {abs_pp_cell} &" pts above"', self.formats['RAG_POS'])
        self.worksheet.write(3, 3, f'="<" & {abs_pp_cell} &" pts below"', self.formats['RAG_NEG'])
        self.worksheet.write(4, 3, 'In between', self.formats['RAG_NEU'])

        # set height of n row
        self.worksheet.set_row(self.number_of_breakdowns + 6, 30)

        # write q and qnum and section headers
        self.worksheet.write(6 + self.number_of_breakdowns, 0, 'Section',
                             self.formats['HEADER'])
        self.worksheet.write(6 + self.number_of_breakdowns, 1, 'Q',
                             self.formats['HEADER'])
        self.worksheet.write(6 + self.number_of_breakdowns, 2, 'Description',
                             self.formats['HEADER'])

        # works out size, i.e. number of rows (n/a or not)
        size = get_agg_df(self.sheet_data, sheet_breakdown, 'size')
        # get actual dfs
        mean = create_total_ses_df(self.sheet_data, self.sheet_breakdown, self.parent_workbook.ses_questions_dict,
                                   self.parent_workbook.parent_report.suppression_threshold)

        #redundant
        # sesoveralldf = create_total_ses_df(self.sheet_data, None, self.parent_workbook.ses_questions_dict,
        #                                    self.parent_workbook.parent_report.suppression_threshold)


        # create dict of row labels (messy but gets the job done for now)
        question_labels_dict = self.get_question_label_lists()

        # write merged categories
        categories = question_labels_dict['categories']
        report.write_categories(categories, self.worksheet, self.number_of_breakdowns + 7, 0,
                                self.formats['RAG_Q_NUM'])

        #SES unique...
        # # Write question numbers
        # for index, question in enumerate(question_labels_dict['questions']):
        #     self.worksheet.write(index + 7 + self.number_of_breakdowns, 1, question, self.formats['RAG_Q_NUM'])
        # # Write pos text
        # for index, question in enumerate(question_labels_dict['postext']):
        #     self.worksheet.write(index + 7 + self.number_of_breakdowns, 2, question, self.formats['RAG_Q_TEXT'])


        # write breakdown headers and breakdown names
        header_start_column = 5 if self.external_comparator is not None else 4
        report.write_headers(mean, self.worksheet, 6, header_start_column, self.formats['HEADER'])
        report.write_breakdown_level_names(mean, self.worksheet, 6, 3, self.formats['LEVEL_TITLE'])

        # comparator text either equals overall or the provided string for an external comparator
        comparator_text = f'{self.parent_workbook.parent_report.overall_text}' if self.external_comparator is None else self.parent_workbook.parent_report.comparator_text

        self.write_single_header(f'Comparator ({comparator_text})', 3)
        # if there is an external comparator, write the header for the aditional overall column
        if self.external_comparator is not None:
            self.write_single_header(f'{self.parent_workbook.parent_report.overall_text}', 4)

        # decider the column localtion of the orcerall column if there is an external comparator or not as well as value start columns
        n_overall_column = 4 if self.external_comparator is not None else 3
        value_start_col = 5 if self.external_comparator is not None else 4

        # write n
        # n overall
        self.worksheet.write(6 + self.number_of_breakdowns, n_overall_column, f'n = {len(self.sheet_data)}',
                             self.formats['HEADER'])
        # comparator
        if self.external_comparator is not None:
            self.worksheet.write(6 + self.number_of_breakdowns, 3, f'n = {self.external_comparator_n}',
                                 self.formats['HEADER'])
        # n for breakdowns
        for index, nnumb in enumerate(size):
            self.worksheet.write(6 + self.number_of_breakdowns, value_start_col + index, f'n = {nnumb}',
                                 self.formats['HEADER'])

        # determine what the comparator should be (external or overall) and write
        comprarator_series = self.external_comparator.values if self.external_comparator is not None else self.parent_workbook.total_mean

        for value_index, value in enumerate(comprarator_series):
            #rounding
            if value != '*':
                value = Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            self.worksheet.write(7 + self.number_of_breakdowns + value_index, 3, value, self.formats['SES_CMP'])



        # if overall is not the comparator, write it on the next column.
        if self.external_comparator is not None:
            for value_index, value in enumerate(self.parent_workbook.total_mean.values):
                if value != '*':
                    value = Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                self.worksheet.write(7 + self.number_of_breakdowns + value_index, 4, value, self.formats['SES_NEU'])



        # write q numbers and pos text
        for index, question in enumerate(mean.index):
            # set row height
            self.worksheet.set_row(index + 7 + self.number_of_breakdowns, 30)
            qid, pos_text = self.define_q_qid(question)
            self.worksheet.write(index + 7 + self.number_of_breakdowns, 2, pos_text, self.formats['RAG_Q_TEXT'])
            self.worksheet.write(index + 7 + self.number_of_breakdowns, 1, qid, self.formats['RAG_Q_NUM'])



        # def write actual values
        for index, question in enumerate(mean.index):

            for value_index, value in enumerate(mean.iloc[index]):

                if value != '*':
                    value = Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

                self.worksheet.write(index + 7 + self.number_of_breakdowns, value_start_col + value_index, value,
                                     self.formats['SES_NEU'])




        #if used in this report, write the total row merged text:
        self.write_total_row_header(len(mean))







        # Apply conditional
        # get absolute cell references for start points for conditional formulas

        abs_cell_cmp_start = xl_rowcol_to_cell(7 + self.number_of_breakdowns, 3, col_abs=True)
        abs_cell_value = xl_rowcol_to_cell(7 + self.number_of_breakdowns, 4)

        number_columns = len(mean.columns) + 1 if self.external_comparator is not None else len(mean.columns)
        number_questions = len(mean.index)

        self.worksheet.conditional_format(self.number_of_breakdowns + 7, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'={abs_cell_value}=10',
                                           'format': self.formats['SES_10']})
        self.worksheet.conditional_format(self.number_of_breakdowns + 7, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'=LEFT({abs_cell_value})="*"',
                                           'format': self.formats['RAG_SUPP']})
        self.worksheet.conditional_format(self.number_of_breakdowns + 7, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'=OR({abs_cell_value}>{abs_cell_cmp_start}+({abs_pp_cell}),{abs_cell_value}=10)',
                                           'format': self.formats['SES_POS']})
        self.worksheet.conditional_format(self.number_of_breakdowns + 7, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'=OR({abs_cell_value}<{abs_cell_cmp_start}-({abs_pp_cell}),{abs_cell_value}=0)',
                                           'format': self.formats['SES_NEG']})





    def define_q_qid(self, question):
        if question not in ['Overall', 'Staff Engagement Score']:
            qid = question
            pos_text = self.questions.get_by_qid(qid).pos_text
        else:
            qid = 'N/A'
            pos_text = 'Overall'

        return qid, pos_text

    def write_total_row_header(self, length=None):
        # write overall SES row label
        self.worksheet.merge_range(self.number_of_breakdowns + 6 + length, 0,
                                   self.number_of_breakdowns + 6 + length, 2, 'Staff Engagment Score',
                                   self.formats['RAG_Q_NUM'])

    def get_question_label_lists(self):
        categories_for_output = []
        ses_questions_for_output = []
        ses_pos_text_for_output = []

        for category, item in self.parent_workbook.ses_questions_dict.items():
            ses_questions_for_output = ses_questions_for_output + item + ['N/A']
            for i in range(len(item) + 1):
                categories_for_output.append(category)

        for question in ses_questions_for_output:
            if question == 'N/A':
                appendval = 'Overall'
            else:
                appendval = (self.questions.get_by_qid(question)).pos_text
            ses_pos_text_for_output.append(appendval)

        return {'categories': categories_for_output, 'questions': ses_questions_for_output,
                'postext': ses_pos_text_for_output}


def ses_map_data(df, question_fields, sesmap):
    """Maps the recode values to the corresponding SES value for each SES question (ses_questions_list) accordinbg to
    the ses_map dictionary """
    for question in question_fields:
        df[question] = df[question].map(sesmap)
    return df


def ses_get_question_fields(ses_questions_dict) -> list:
    """Gets a list of questions from the ses_questrions dictionary of structure {'Category': [List of Qs]}"""
    return sum([value for value in ses_questions_dict.values()], [])


def create_total_ses_df(data: pd.DataFrame, breakdown, questions_dict: dict,
                        suppression_threshold: int) -> pd.DataFrame:
    """Creeates an overall ses data frame, with all categories (with summary) and an overall SES row. Fills na values
    (i.e. missing or suppressed) with '*'"""

    # Creates a list of dfs for each category and combined them.
    category_dfs = []
    for questions in questions_dict.values():
        df = data[questions] if breakdown is None else data[breakdown + questions]
        category_df = create_category_ses_df(df, breakdown, suppression_threshold)
        category_dfs.append(category_df)
    combineddf = pd.concat(category_dfs)

    # Adds a total staff engagement score row
    total_ses = create_average_ses(combineddf.loc['Overall'], 'Staff Engagement Score')

    return combineddf.append(total_ses).fillna('*')


def create_category_ses_df(data: pd.DataFrame, breakdown, suppression_threshold: int):
    """creates a ses dataframe with all of the questions in a category and an overall row"""
    df = create_ses_df(data, breakdown, suppression_threshold)
    catergoy_overall = create_average_ses(df, 'Overall')
    return df.append(catergoy_overall)


def create_ses_df(data, breakdown, suppression_threshold) -> pd.DataFrame:
    """Creates the SES score dataframe, with an overall row, with or without a breakdown suppressed to the
    suppression threshold. Typically useful for a single category. Calculates the count of responses and the sum of the
    mapped ses value. sum/count gives SES score. Values are suppressed accoding to the count df."""

    countdf = get_agg_df(data, breakdown, 'count')
    sumdf = get_agg_df(data, breakdown, 'sum')
    return (sumdf / countdf).mask(countdf < suppression_threshold)


def create_average_ses(data: pd.DataFrame, series_name: str) -> pd.Series:
    """Creeates an overall ses row (average). If a column contains no blanks (i.e. suppressed or missing data), the
    overall score is the average of the individual scores. """

    return data.mean().mask(data.count() < len(data)).rename(series_name)
