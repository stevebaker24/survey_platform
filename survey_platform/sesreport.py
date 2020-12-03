from . import report
from . import frequency_table_config

import pandas as pd
import numpy as np

from xlsxwriter.utility import xl_rowcol_to_cell

from survey_platform import survey_platform as sp
from survey_platform.report import get_agg_df


def create_ses(source, questions, sheet_breakdown_fields, suppression_threshold, output_path, external_comparator, comparator_text, overall_text):
    SesReport(source, output_path, questions, sheet_breakdown_fields, suppression_threshold,
              external_comparator=external_comparator, comparator_text=comparator_text, overall_text=overall_text)


class SesReport(report.Report):
    def __init__(self, source, output_path, questions, sheet_breakdown_fields, suppression_threshold,
                 external_comparator, comparator_text, overall_text):
        self.workbook_class = SesWorkbook
        self.worksheet_class = SesWorksheet
        self.file_name = 'SES_Report'
        self.report_name = 'SES_Report'
        super().__init__(source, output_path, questions, sheet_breakdown_fields, suppression_threshold,
                         external_comparator=external_comparator, comparator_text=comparator_text, overall_text=overall_text)


class SesWorkbook(report.ReportWorkbook):

    def __init__(self, parent_report):
        self.format_dict = frequency_table_config.FORMATS
        self.sesmap = {5: 10, 4: 7.5, 3: 5, 2: 2.5, 1: 0}
        self.ses_questions_dict = {'SESCAT1': ['B5', 'B13', 'B15'], 'SESCAT2': ['C18', 'C21', 'D1'],
                                   'SESCAT3': ['D4', 'D8', 'E3']}

        super().__init__(parent_report)

    def calculate_external_comparator(self, df):
        return create_total_ses_df(df, None, self.ses_questions_dict,
                                   self.parent_report.suppression_threshold)

    def calculate_workbook_data(self, df):
        return self.ses_map_data(df)

    def ses_map_data(self, df):
        """Maps the recode values to the corresponding SES value for each SES question (ses_questions_list) accordinbg to
        the ses_map dictionary """
        for question in self.question_fields:
            df[question] = df[question].map(self.sesmap)
        return df

    def get_question_fields(self) -> list:
        """Gets a list of questions from the ses_questrions dictionary of structure {'Category': [List of Qs]}"""
        return sum([value for value in self.ses_questions_dict.values()], [])

    def create_guidance_page(self):
        guidance_sheet = self.workbook.add_worksheet('Guidance')
        guidance_sheet.merge_range(6, 1, 6, 13, 'SES Report Guidance', self.formats['RAG_GUIDANNCE_BOLD'])
        guidance_sheet.merge_range(7, 1, 7, 13,
                                   'SESThis report shows positive scores for the reakdown categories_for_output compared with the combined score. It is a dynamic report you can adjust to get the maximum insight from your data.',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(8, 1, 8, 13,
                                   'SESBy default the RAG comparison is set at 3 or more percentage points difference between the scores. To highlight all differences of 5 percentage points or more adjust cell E6 to 5, to see all differences of 10 percentage points or more change this to 10 etc. Red differences are where the scores are more than this value below the organisation average, green differences are more than this value above the organisation average.',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(9, 1, 9, 13,
                                   'SESThe positive score is the percentage of respondents to whom the question applies,  who who gave a favourable response to each question. Values are rounded to the nearest percent. Only questions that can be positively scored have been included.',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(10, 1, 10, 13,
                                   'SESIf there is a suppression threshold for your survey, where there are less than x responses to a question (or zero),  the respective scores are replaced with an asterisk (*)',
                                   self.formats['RAG_GUIDANNCE'])

        guidance_sheet.set_row(7, 42)
        guidance_sheet.set_row(8, 63)
        guidance_sheet.set_row(9, 49)
        guidance_sheet.set_row(10, 36)

        guidance_sheet.insert_image('B2', frequency_table_config.LOGO_PATH, {'y_offset': 10, 'x_offset': 0})

        guidance_sheet.hide_gridlines(2)


class SesWorksheet(report.ReportWorksheet):

    def __init__(self, sheet_data, worksheet, sheet_breakdown, parent_workbook):
        super().__init__(sheet_data, worksheet, sheet_breakdown, parent_workbook)

        self.worksheet.hide_gridlines(2)
        self.worksheet.set_column('A:A', 30)
        self.worksheet.set_column('B:B', 10)
        self.worksheet.set_column('C:C', 60)
        self.worksheet.set_column('D:ZZ', 18.5)

        self.worksheet.set_zoom(75)

        self.worksheet.insert_image('A1', frequency_table_config.LOGO_PATH,
                                    {'y_offset': 15, 'x_offset': 10, 'x_scale': 0.85, 'y_scale': 0.85})

        self.worksheet.freeze_panes(self.number_of_breakdowns + 7, 4)

        for i in range(self.number_of_breakdowns):
            self.worksheet.set_row(i + 6, 42)

        # worksheet Title Section
        self.worksheet.write(1, 2, self.survey_name, self.formats['SUBTITLE'])
        self.worksheet.write(2, 2, 'Staff Engagement Score Report', self.formats['SUBTITLE'])
        self.worksheet.write(3, 2, f'Broken Down By: {self.breakdown_text}', self.formats['SUBTITLE'])
        self.worksheet.write(1, 3, 'RAG SES', self.formats['SUBTITLE'])
        self.worksheet.write(2, 3, 'difference:', self.formats['SUBTITLE'])

        # write default pp difference value (aboslute value to use in formulas)
        abs_pp_cell = xl_rowcol_to_cell(3, 3, col_abs=True, row_abs=True)
        self.worksheet.write(abs_pp_cell, 0.4, self.formats['SET_PERCENT'])

        # works out size, i.e. number of rows (n/a or not) to get n
        size = get_agg_df(self.sheet_data, sheet_breakdown, 'size')

        # get actual dfs
        sesdf = create_total_ses_df(self.sheet_data, self.sheet_breakdown, self.parent_workbook.ses_questions_dict,
                                    self.parent_workbook.parent_report.suppression_threshold)
        sesoveralldf = create_total_ses_df(self.sheet_data, None, self.parent_workbook.ses_questions_dict,
                                           self.parent_workbook.parent_report.suppression_threshold)

        # create dict of row labels (messy but gets the job done for now)
        question_labels_dict = self.get_question_label_lists()
        # write merged categories
        report.write_categories(question_labels_dict['categories'], self.worksheet, self.number_of_breakdowns + 7, 0,
                                self.formats['RAG_Q_NUM'])
        # Write question numbers
        for index, question in enumerate(question_labels_dict['questions']):
            self.worksheet.write(index + 7 + self.number_of_breakdowns, 1, question, self.formats['RAG_Q_NUM'])
        # Write pos text
        for index, question in enumerate(question_labels_dict['postext']):
            self.worksheet.write(index + 7 + self.number_of_breakdowns, 2, question, self.formats['RAG_Q_TEXT'])
        # write overall SES row label
        self.worksheet.merge_range(self.number_of_breakdowns + 6 + len(sesdf), 0,
                                   self.number_of_breakdowns + 6 + len(sesdf), 2, 'Staff Engagment Score',
                                   self.formats['RAG_Q_NUM'])

        # write headers
        header_start_column = 5 if self.external_comparator else 4
        report.write_headers(sesdf, self.worksheet, 6, header_start_column, self.formats['HEADER'])
        report.write_breakdown_level_names(sesdf, self.worksheet, 6, 3, self.formats['LEVEL_TITLE'])

        comparator_text = f'({self.parent_workbook.parent_report.overall_text})' if not self.external_comparator else self.parent_workbook.comparator_text

        self.write_single_header(f'Comparator ({comparator_text})', 3)

        if self.external_comparator:
            self.write_single_header(f'{self.parent_workbook.parent_report.overall_text}', 4)

        # write q and qnum and section headers
        self.worksheet.write(6 + self.number_of_breakdowns, 0, 'Section',
                             self.formats['HEADER'])
        self.worksheet.write(6 + self.number_of_breakdowns, 1, 'Q',
                             self.formats['HEADER'])
        self.worksheet.write(6 + self.number_of_breakdowns, 2, 'Description',
                             self.formats['HEADER'])

        # write n
        self.worksheet.set_row(self.number_of_breakdowns + 6, 30)
        # n overall
        n_overall_column = 4 if self.external_comparator else 3
        self.worksheet.write(6 + self.number_of_breakdowns, n_overall_column, f'n = {len(self.sheet_data)}',
                             self.formats['HEADER'])
        # comparator
        if self.external_comparator:
            self.worksheet.write(6 + self.number_of_breakdowns, 3, f'n = {self.parent_workbook.external_comparator_n}',
                                 self.formats['HEADER'])

        # n breakdowns
        value_start_col = 5 if self.external_comparator else 4
        for index, nnumb in enumerate(size):
            self.worksheet.write(6 + self.number_of_breakdowns, value_start_col + index, f'n = {nnumb}',
                                 self.formats['HEADER'])

        #determine what the comparator should be (external or overall) and write
        comprarator_series = self.parent_workbook.external_comparator_data.values if self.external_comparator else sesoveralldf.values
        for value_index, value in enumerate(comprarator_series):
            self.worksheet.write(7 + self.number_of_breakdowns + value_index, 3, value, self.formats['RAG_CMP'])

        #if overall is not the comparator, write it on the next column.
        if self.external_comparator:
            for value_index, value in enumerate(sesoveralldf.values):
                self.worksheet.write(7 + self.number_of_breakdowns + value_index, 4, value, self.formats['SES_NEU'])

        # write actual values
        for index, question in enumerate(sesdf.index):
            self.worksheet.set_row(index + 7 + self.number_of_breakdowns, 30)
            for value_index, value in enumerate(sesdf.iloc[index]):
                self.worksheet.write(index + 7 + self.number_of_breakdowns, value_start_col + value_index, value,
                                     self.formats['SES_NEU'])

        # Apply conditional
        # get absolute cell references for start points for conditional formulas
        abs_cell_cmp_start = xl_rowcol_to_cell(7 + self.number_of_breakdowns, 3, col_abs=True)
        abs_cell_value = xl_rowcol_to_cell(7 + self.number_of_breakdowns, 4)
        number_columns = len(sesdf.columns)+1 if self.external_comparator else len(sesdf.columns)
        number_questions = len(sesdf.index)

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

    def write_single_header(self, title, column):
        if self.number_of_breakdowns > 1:
            self.worksheet.merge_range(6, column, self.number_of_breakdowns + 5, column, title, self.formats['HEADER'])
        else:
            self.worksheet.write(self.number_of_breakdowns + 5, column, title, self.formats['HEADER'])


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

# categories = []
# categories_for_output = []
# ses_questions = []
# ses_questions_for_output = []
# for category, item in ses_questions_dict.items():
#     categories.append(category)
#     ses_questions = ses_questions + item
#     ses_questions_for_output = ses_questions_for_output + item + ['N/A']
#     for i in range(len(item)+1):
#         categories_for_output.append(category)
