import report
import report_config
from report import get_agg_df
from xlsxwriter.utility import xl_rowcol_to_cell
from decimal import Decimal, ROUND_HALF_UP

import survey_platform as sp


class RagReport(report.Report):
    def __init__(self, source, output_path, questions, sheet_breakdown_fields, suppression_threshold, survey_name,
                 external_comparator=None, external_comparator_n=None, comparator_text=None, report_name=None,
                 file_name=None,
                 overall_text=None):
        self.workbook_class = RAGWorkbook
        self.worksheet_class = RAGWorksheet
        self.report_name = 'RAG Table Report'

        super().__init__(source, output_path, questions, sheet_breakdown_fields, suppression_threshold,
                         external_comparator=external_comparator, external_comparator_n=external_comparator_n,
                         comparator_text=comparator_text,
                         overall_text=overall_text, survey_name=survey_name, report_name=report_name,
                         file_name=file_name)


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
                                   'This report shows positive scores by each of the breakdown categories across each worksheet. These scores are visually compared to the comparator by RAG colouring. It is a dynamic report you can adjust to get the maximum insight from your data.',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(8, 1, 8, 13,
                                   'By default, the RAG comparison is set to 3 or more percentage points difference between the scores. Red differences are where the scores are more than this value below the comparator, green differences are more than this value above the comparator. The percentage point difference value can be adjusted by changing the value in cell B6. For example, to highlight all differences of 8 pecentage points or more adjust cell B6 to 8',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(9, 1, 9, 13,
                                   'The positive score is the percentage of respondents to whom the question applies, who gave a favourable response to each question. Values are rounded to the nearest percent. Only questions that can be positively scored have been included.',
                                   self.formats['RAG_GUIDANNCE'])
        guidance_sheet.merge_range(10, 1, 10, 13,
                                   'If there is a suppression threshold for your survey, where there are less than this many responses to a question (or zero), the respective scores are replaced with an asterisk (*).',
                                   self.formats['RAG_GUIDANNCE'])

        guidance_sheet.set_row(7, 42)
        guidance_sheet.set_row(8, 80.25)
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
        self.worksheet.write(3, 2, f'Breakdown: {self.breakdown_text}', self.formats['SUBTITLE'])
        self.worksheet.write(4, 2, f'Suppression Threshold: {self.parent_workbook.parent_report.suppression_threshold}',
                             self.formats['SUBTITLE'])

        ###RAG set point
        self.worksheet.write(5, 0, 'Set RAG % point difference:', self.formats['RAG_SET_POINT_TEXT'])
        # write default pp difference value (aboslute value to use in formulas)
        abs_pp_cell = xl_rowcol_to_cell(5, 1, col_abs=True, row_abs=True)
        self.worksheet.write(abs_pp_cell, 3, self.formats['SET_PERCENT'])

        # Key
        self.worksheet.write(0, 3, 'Key:', self.formats['SUBTITLE_CENTER'])
        self.worksheet.write(1, 3, 1, self.formats['RAG_100'])
        self.worksheet.write(2, 3, f'=">" & {abs_pp_cell} &" ppt above"', self.formats['RAG_POS'])
        self.worksheet.write(3, 3, f'="<" & {abs_pp_cell} &" ppt below"', self.formats['RAG_NEG'])
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

        # get dfs
        size = get_agg_df(self.sheet_data, sheet_breakdown, 'size')
        count = get_agg_df(self.sheet_data, sheet_breakdown, 'count')
        mean = get_agg_df(self.sheet_data, sheet_breakdown, 'mean').mask(
            count < self.parent_workbook.parent_report.suppression_threshold) \
            .div(100) \
            .fillna('*')

        # write merged categories_for_output
        categories = [question.category for question in self.questions.scored_questions]
        report.write_categories(categories, self.worksheet, self.number_of_breakdowns + 7, 0, self.formats['RAG_Q_NUM'])

        # write breakdown headers and breakdown names
        header_start_column = 5 if self.external_comparator is not None else 4
        report.write_headers(mean, self.worksheet, 6, header_start_column, self.formats['HEADER'])
        report.write_breakdown_level_names(mean, self.worksheet, 6, 3, self.formats['LEVEL_TITLE'])

        # comparator text either equals overall or the provided string for an external comparator
        comparator_text = f'{self.parent_workbook.parent_report.overall_text}' if self.external_comparator is None else self.parent_workbook.parent_report.comparator_text

        self.write_single_header(f'Comparator ({comparator_text})', 3)
        # if there is an external comparator, write hte header for the aditional overall column
        if self.external_comparator is not None:
            self.write_single_header(f'{self.parent_workbook.parent_report.overall_text}', 4)

        # decider the column localtion of the orcerall column if there is an external comparator or not
        n_overall_column = 4 if self.external_comparator is not None else 3
        value_start_col = 5 if self.external_comparator is not None else 4

        # write n
        # overall
        self.worksheet.write(6 + self.number_of_breakdowns, n_overall_column, f'n = {len(self.sheet_data)}',
                             self.formats['HEADER'])
        # comparator n
        if self.external_comparator is not None:
            self.worksheet.write(6 + self.number_of_breakdowns, 3, f'n = {self.external_comparator_n}',
                                 self.formats['HEADER'])
        # n for breakdowns
        for index, nnumb in enumerate(size):
            self.worksheet.write(6 + self.number_of_breakdowns, value_start_col + index, f'n = {nnumb}',
                                 self.formats['HEADER'])

        # determine what the comparator should be (external or overall) and write
        comprarator_series = self.external_comparator if self.external_comparator is not None else self.parent_workbook.total_mean

        # write comparator values
        for value_index, value in enumerate(comprarator_series.values):
            # rounding
            if value != '*':
                value = Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.worksheet.write(7 + self.number_of_breakdowns + value_index, 3, value, self.formats['RAG_CMP'])



        # if overall is not the comparator, write it on the next column.
        if self.external_comparator is not None:
            for value_index, value in enumerate(parent_workbook.total_mean.values):
                if value != '*':
                    value = Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                self.worksheet.write(7 + self.number_of_breakdowns + value_index, 4, value, self.formats['RAG_NEU'])



        # write q numbers and pos text
        for index, question in enumerate(mean.index):
            # set row height
            self.worksheet.set_row(index + 7 + self.number_of_breakdowns, 30)
            qid, pos_text = self.define_q_qid(question)
            self.worksheet.write(index + 7 + self.number_of_breakdowns, 2, pos_text, self.formats['RAG_Q_TEXT'])
            self.worksheet.write(index + 7 + self.number_of_breakdowns, 1, qid, self.formats['RAG_Q_NUM'])



        #def write actual values
        for index, question in enumerate(mean.index):

            for value_index, value in enumerate(mean.iloc[index]):

                if value != '*':
                    value = Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                self.worksheet.write(index + 7 + self.number_of_breakdowns, value_start_col + value_index, value,
                                     self.formats['RAG_NEU'])






        #if used in this report, write the total row merged text:
        self.write_total_row_header(len(mean))






        # Apply conditional
        # get absolute cell references for start points for conditional formulas

        #defines the cell in A1 notation where the first comparator and value cells are
        abs_cell_cmp_start = xl_rowcol_to_cell(7 + self.number_of_breakdowns, 3, col_abs=True)
        abs_cell_value = xl_rowcol_to_cell(7 + self.number_of_breakdowns, 4)

        #number of breakdown columns
        number_columns = len(mean.columns) + 1 if self.external_comparator is not None else len(mean.columns)
        number_questions = len(mean.index)

        self.worksheet.conditional_format(self.number_of_breakdowns + 7, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'=LEFT({abs_cell_value})="1"',
                                           'format': self.formats['RAG_100']})
        self.worksheet.conditional_format(self.number_of_breakdowns + 7, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'=LEFT({abs_cell_value})="*"',
                                           'format': self.formats['RAG_SUPP']})
        self.worksheet.conditional_format(self.number_of_breakdowns + 7, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'=OR({abs_cell_value}>{abs_cell_cmp_start}+({abs_pp_cell}/100),{abs_cell_value}=1)',
                                           'format': self.formats['RAG_POS']})
        self.worksheet.conditional_format(self.number_of_breakdowns + 7, 4,
                                          self.number_of_breakdowns + number_questions + 6, number_columns + 3,
                                          {'type': 'formula',
                                           'criteria': f'=({abs_cell_value}<{abs_cell_cmp_start}-({abs_pp_cell}/100))',
                                           'format': self.formats['RAG_NEG']})

    def define_q_qid(self, question):
        qid = question[:-4]
        pos_text = self.questions.get_by_qid(qid).pos_text
        return qid, pos_text

    def write_total_row_header(self, length=None):
        pass