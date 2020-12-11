import report
import report_config
from report import get_agg_df
from xlsxwriter.utility import xl_rowcol_to_cell

import survey_platform as sp


class RagReport(report.Report):
    def __init__(self, source, output_path, questions, sheet_breakdown_fields, suppression_threshold, survey_name,
                 report_name, file_name, overall_text=None):
        self.workbook_class = RAGWorkbook
        self.worksheet_class = RAGWorksheet
        self.report_name = 'RAG Table Report'

        super().__init__(source, output_path, questions, sheet_breakdown_fields, suppression_threshold,
                         survey_name=survey_name, report_name=report_name, file_name=file_name,
                         overall_text=overall_text)


class RAGWorkbook(report.ReportWorkbook):

    def __init__(self, parent_report):
        self.format_dict = report_config.FORMATS
        super().__init__(parent_report)

    def calculate_workbook_data(self, df):
        data = sp.calc_scores(self.parent_report.source, self.parent_report.questions, ['pos'])
        data = self.fill_empty_breakdown_values(data)

        self.score_columns = [f"{x.qid}_pos" for x in self.parent_report.questions.scored_questions]
        self.total_count = data[self.score_columns].count()
        self.total_mean = data[self.score_columns] \
            .mean() \
            .mask(self.total_count < self.parent_report.suppression_threshold) \
            .div(100) \
            .fillna('*')
        return data

    def create_guidance_page(self):
        guidance_sheet = self.workbook.add_worksheet('Guidance')
        guidance_sheet.merge_range(6, 1, 6, 13, 'RAG Report Guidance', self.formats['RAG_GUIDANNCE_BOLD'])
        guidance_sheet.merge_range(7, 1, 7, 13,
                                   'This report shows positive scores for the elements of the breakdown categories compared with the combined score. It is a dynamic report you can adjust to get the maximum insight from your data.',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(8, 1, 8, 13,
                                   'By default the RAG comparison is set at 3 or more percentage points difference between the scores. To highlight all differences of 5 percentage points or more adjust cell B6 to 5, to see all differences of 10 percentage points or more change this to 10. Red differences are where the scores are more than this value below the comparator, green differences are more than this value above the comparator.',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(9, 1, 9, 13,
                                   'The positive score is the percentage of respondents to whom the question applies,  who who gave a favourable response to each question. Values are rounded to the nearest percent. Only questions that can be positively scored have been included.',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(10, 1, 10, 13,
                                   'If there is a suppression threshold for your survey, where there are less than x responses to a question (or zero),  the respective scores are replaced with an asterisk (*)',
                                   self.formats['RAG_GUIDANNCE'])

        guidance_sheet.set_row(7, 42)
        guidance_sheet.set_row(8, 63)
        guidance_sheet.set_row(9, 49)
        guidance_sheet.set_row(10, 36)

        guidance_sheet.insert_image('B2', report_config.LOGO_PATH, {'y_offset': 10, 'x_offset': 0})

        guidance_sheet.hide_gridlines(2)


class RAGWorksheet(report.ReportWorksheet):

    def __init__(self, sheet_data, worksheet, sheet_breakdown, parent_workbook):
        super().__init__(sheet_data, worksheet, sheet_breakdown, parent_workbook)

        self.sheet_data = self.sheet_data[sheet_breakdown + self.parent_workbook.score_columns]

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
        self.worksheet.write(3, 2, f'Broken Down By: {self.breakdown_text}', self.formats['SUBTITLE'])

        self.worksheet.write(5, 0, 'Set RAG % point difference:', self.formats['RAG_SET_POINT_TEXT'])


        # write default pp difference value (aboslute value to use in formulas)
        abs_pp_cell = xl_rowcol_to_cell(5, 1, col_abs=True, row_abs=True)
        self.worksheet.write(abs_pp_cell, 3, self.formats['SET_PERCENT'])

        self.worksheet.set_row(self.number_of_breakdowns + 6, 30)

        # total n per group
        # droped_na = self.sheet_data.dropna(how='all', subset=[f"{x.qid}_pos" for x in self.questions.scored_questions])
        # size = sp.get_grouped_df(droped_na, sheet_breakdown, 'size')

        size = get_agg_df(self.sheet_data, sheet_breakdown, 'size')
        count = get_agg_df(self.sheet_data, sheet_breakdown, 'count')
        mean_not_supp = get_agg_df(self.sheet_data, sheet_breakdown, 'mean')

        mean = get_agg_df(self.sheet_data, sheet_breakdown, 'mean').mask(
            count < self.parent_workbook.parent_report.suppression_threshold) \
            .div(100) \
            .fillna('*')

        # write merged categories_for_output
        categories = [question.category for question in self.questions.scored_questions]
        report.write_categories(categories, self.worksheet, self.number_of_breakdowns + 7, 0, self.formats['RAG_Q_NUM'])

        report.write_headers(mean, self.worksheet, 6, 4, self.formats['HEADER'])
        report.write_breakdown_level_names(mean, self.worksheet, 6, 3, self.formats['LEVEL_TITLE'])

        if self.number_of_breakdowns > 1:
            self.worksheet.merge_range(6, 3, self.number_of_breakdowns + 5, 3, self.parent_workbook.parent_report.overall_text, self.formats['HEADER'])
        else:
            self.worksheet.write(self.number_of_breakdowns + 5, 3, self.parent_workbook.parent_report.overall_text, self.formats['HEADER'])

        # write comparator values
        for value_index, value in enumerate(self.parent_workbook.total_mean):
            self.worksheet.write(7 + self.number_of_breakdowns + value_index, 3, value, self.formats['RAG_CMP'])

        # write actual values
        for index, question in enumerate(mean.index):
            self.worksheet.set_row(index + 7 + self.number_of_breakdowns, 30)
            qid = question[:-4]
            pos_text = self.questions.get_by_qid(qid).pos_text
            self.worksheet.write(index + 7 + self.number_of_breakdowns, 2, pos_text, self.formats['RAG_Q_TEXT'])
            self.worksheet.write(index + 7 + self.number_of_breakdowns, 1, qid, self.formats['RAG_Q_NUM'])
            for value_index, value in enumerate(mean.iloc[index]):
                self.worksheet.write(index + 7 + self.number_of_breakdowns, 4 + value_index, value,
                                     self.formats['RAG_NEU'])

        # write n
        self.worksheet.write(6 + self.number_of_breakdowns, 3, f'n = {len(self.sheet_data)}',
                             self.formats['HEADER'])
        for index, nnumb in enumerate(size):
            self.worksheet.write(6 + self.number_of_breakdowns, 4 + index, f'n = {nnumb}',
                                 self.formats['HEADER'])

        # write q and qnum and section headers
        self.worksheet.write(6 + self.number_of_breakdowns, 0, 'Section',
                             self.formats['HEADER'])
        self.worksheet.write(6 + self.number_of_breakdowns, 1, 'Q',
                             self.formats['HEADER'])
        self.worksheet.write(6 + self.number_of_breakdowns, 2, 'Description',
                             self.formats['HEADER'])

        # Apply conditional
        # get absolute cell references for start points for conditional formulas
        abs_cell_cmp_start = xl_rowcol_to_cell(6 + self.number_of_breakdowns, 3, col_abs=True)
        abs_cell_value = xl_rowcol_to_cell(6 + self.number_of_breakdowns, 4)
        number_columns = len(mean.columns)
        number_questions = len(mean.index)

        self.worksheet.conditional_format(self.number_of_breakdowns + 6, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'=LEFT({abs_cell_value})="*"',
                                           'format': self.formats['RAG_SUPP']})
        self.worksheet.conditional_format(self.number_of_breakdowns + 6, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'=OR({abs_cell_value}>{abs_cell_cmp_start}+({abs_pp_cell}/100),{abs_cell_value}=1)',
                                           'format': self.formats['RAG_POS']})
        self.worksheet.conditional_format(self.number_of_breakdowns + 6, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'=OR({abs_cell_value}<{abs_cell_cmp_start}-({abs_pp_cell}/100),{abs_cell_value}=0)',
                                           'format': self.formats['RAG_NEG']})
