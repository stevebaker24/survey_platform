import report
import config, report_config
import copy

import pandas as pd
import numpy as np


def write_row_from_df(df_row, worksheet, row, column, format_count, format_percent):
    for index, value in enumerate(df_row):
        if index % 2:
            worksheet.write(row, column, value, format_percent)
        else:
            worksheet.write(row, column, value, format_count)
        column += 1


def write_breakdown_level_names(df, worksheet, row, start_column, workbook_format):
    for index, level_name in enumerate(df.columns.names):
        if level_name is not None:
            worksheet.write((row + index), start_column - 1, level_name, workbook_format)


def add_missing_options(df, question):
    # Adds response options not picked up bu the cross tab (i.e. no responses for that option
    for option in question.response_options:
        if option not in df.index:
            df.loc[option] = 0
            df.sort_index(inplace=True)


def create_empty_df(df, question, overall_text):
    # Adds response options not picked up bu the cross tab (i.e. no responses for that option
    data = [0 for x in question.response_options]

    return pd.DataFrame({overall_text: [0 for x in question.response_options]})


def create_crosstab(df, question, suppression_threshold, overall_text, breakdown_column_names=None):
    breakdown_columns = [overall_text] if breakdown_column_names is None else breakdown_column_names

    if question.q_type == config.SINGLE_CODE:
        # remove anythign not in the list of respinse options
        # mainly here for targetted questions where 'ignore' options are not included.
        # not implemented for multi-response questions if that ever comes up, not in any current surveys
        question_series = df[question.qid].copy()
        question_series.loc[~question_series.isin(question.response_options.keys())] = np.nan

        count = pd.crosstab(question_series, breakdown_columns).fillna(0)
        subtotal = count.sum()
    else:
        dfs = multi_q_count_dfs(df, question, breakdown_columns)
        if len(dfs) == 0:
            count = pd.DataFrame()
            subtotal = pd.Series()
        else:
            count = pd.concat(dfs).fillna(0)
            subtotal = multi_subtotal(df, question, breakdown_columns)

    # Check if any answers, if none, crfeate empy dataframe
    if len(count) == 0:
        if breakdown_column_names is None:
            count = create_empty_df(count, question, overall_text=overall_text)
        else:
            return None

    # add any missing response options
    add_missing_options(count, question)

    # calculate percentage
    percent = (count / subtotal) * 100

    # suppress the count and percent
    suppressed_count = suppress(count, subtotal, suppression_threshold)
    suppressed_percent = suppress(percent, subtotal, suppression_threshold)

    # combine the count and percent into single DF
    suppressed_concatted = combine_count_percent_dfs(suppressed_count, suppressed_percent)

    # Remove ZZZ from blank, there to keep Blank at the back when ordering.
    suppressed_concatted = suppressed_concatted.rename({f'ZZZZZ{config.BLANK_STR}': config.BLANK_STR}, axis='columns')

    # calculate the 'total' rows for the bottom:
    if question.q_type == config.SINGLE_CODE:
        total = suppressed_concatted.sum(min_count=1)
    elif (question.q_type == config.MULTI_CODE) and (count.sum()[0] == 0):
        total = pd.Series({'Count': np.nan, 'Percent': np.nan})
    else:
        # cant just sum the count df for multi
        # needs additional to frame and transpose becaise not a df going in
        suppressed_subtotal = suppress(subtotal, subtotal, suppression_threshold).to_frame().transpose()

        # just needs to statically be 100, a sum of the percentages is meaningless
        suppressed_subtotal_percent = suppressed_subtotal.copy()
        suppressed_subtotal_percent.loc[1] = 100
        suppressed_subtotal_percent = suppress(suppressed_subtotal_percent, subtotal, suppression_threshold)

        # combine into one total row and convert df to series
        total = combine_count_percent_dfs(suppressed_subtotal, suppressed_subtotal_percent).squeeze()

    return dict(table=suppressed_concatted.fillna('*'), overall=total.fillna('*'))


def suppress(df, subtotal, suppression_threshold):
    # I dont know why this needs the double transpose but it does, there has to be a better way
    return df.transpose().mask((subtotal < suppression_threshold)).transpose()


def multi_subtotal(df, question, breakdown_columns):
    subtotal = (df[question.question_columns].sum(axis=1) > 0).replace(False, np.nan)
    return pd.crosstab(subtotal, breakdown_columns).squeeze(axis=0)


def multi_q_count_dfs(df, question, breakdown_columns):
    dflist = []
    for column in question.question_columns:
        crosstabdf = pd.crosstab(df[column], breakdown_columns)
        if not crosstabdf.empty:
            crosstabdf.index = [int(column.split('_')[1])]
            dflist.append(crosstabdf)
    return dflist


def combine_count_percent_dfs(df_count, df_percent):
    # concatenate the two dfs
    df_concat = pd.concat([df_count, df_percent], axis=1, keys=['Count', 'Percent'])

    # move count/percent to the bottom level
    levels = [i for (i, x) in enumerate(df_concat.columns.names)]
    levels.append(levels.pop(0))
    df_concat.columns = df_concat.columns.reorder_levels(levels)

    return df_concat.sort_index(axis='columns')


class FrequencyTableReport(report.Report):
    def __init__(self, source, output_path, questions, sheet_breakdown_fields, suppression_threshold, survey_name,
                 report_name, file_name, overall_text=None):
        self.workbook_class = FrequencyTableWorkbook
        self.worksheet_class = FrequencyTableWorksheet
        self.report_name = 'Frequency Table Report'

        super().__init__(source, output_path, questions, sheet_breakdown_fields, suppression_threshold,
                         survey_name=survey_name, report_name=report_name, file_name=file_name,
                         overall_text=overall_text)


class FrequencyTableWorkbook(report.ReportWorkbook):

    def __init__(self, parent_report):
        self.format_dict = report_config.FORMATS
        super().__init__(parent_report)

        # Inheritance probably not needed.


class FrequencyTableWorksheet(report.ReportWorksheet):

    def __init__(self, sheet_data, worksheet, sheet_breakdown, parent_workbook):
        super().__init__(sheet_data, worksheet, sheet_breakdown, parent_workbook)

        self.breakdown_columns = self.get_breakdown_columns()
        self.create_table()

    def get_breakdown_columns(self):
        return [self.sheet_data[x] for x in self.sheet_breakdown if x is not None]

    def create_table(self):
        # workseet general formatting and setup
        self.worksheet.hide_gridlines(2)
        self.worksheet.set_column('A:A', 1)
        self.worksheet.set_column('B:B', 1)
        self.worksheet.set_column('C:C', 50)
        self.worksheet.set_column('D:XFD', 12.29)
        self.worksheet.insert_image('C1', report_config.LOGO_PATH, {'y_offset': 10, 'x_offset': 10})
        self.worksheet.freeze_panes(5, 0)

        self.worksheet.set_zoom(75)

        # worksheet Title Section
        self.worksheet.write(1, 3, self.survey_name, self.formats['SUBTITLE'])
        self.worksheet.write(2, 3, self.parent_workbook.parent_report.report_name, self.formats['SUBTITLE'])
        self.worksheet.write(3, 3, f'Broken Down By: {self.breakdown_text}', self.formats['SUBTITLE'])

        self.row = 6
        self.question_info_column = 2
        self.starter_column = 3

        self.write_all_questions()

    def write_question(self, question, targeted=False):
        if question.q_type not in [config.SINGLE_CODE, config.MULTI_CODE]:
            return

        if targeted:
            if not question.targeted:
                return
            else:
                # Make a copy of the question object with the 'ignore' response options removed.
                question = copy.deepcopy(question)
                for key in question.targeted_options:
                    question.response_options.pop(key)

        row = self.row
        question_info_column = self.question_info_column
        starter_column = self.starter_column

        # create crosstabs dicts (for total and breakdown), returns dict of crosstabs
        crosstabtotaldict = create_crosstab(self.sheet_data, question,
                                            self.parent_workbook.parent_report.suppression_threshold,
                                            self.parent_workbook.parent_report.overall_text)

        crosstabdict = create_crosstab(self.sheet_data, question,
                                       self.parent_workbook.parent_report.suppression_threshold,
                                       self.parent_workbook.parent_report.overall_text,
                                       self.breakdown_columns)

        # Determine if there breakdowns or are any responses and set flag, used to determine if to write the breakdown tables/headers or not.
        if (len(self.breakdown_columns) > 0) and (crosstabdict is not None):
            responses_bool = True
        else:
            responses_bool = False

        # create the question text
        q_text = question.text
        q_text = q_text + " (Multi-response)" if question.q_type == config.MULTI_CODE else q_text
        q_text = q_text + " (Scored Question)" if question.scored else q_text
        q_text = q_text + " (Targeted Question)" if targeted else q_text

        question_number = question.qid if not targeted else f"{question.qid}+"

        # write the question text
        self.worksheet.write(row, question_info_column, f"{question_number}: {q_text}", self.formats['QUESTION'])

        row += 2

        # Write Breakdown Header Names
        if responses_bool:
            write_breakdown_level_names(crosstabdict['table'], self.worksheet, row, starter_column,
                                        self.formats['LEVEL_TITLE'])

        # Write Total Header column
        # not using normal method to allow for vertical merge of total
        self.worksheet.merge_range(row, starter_column, row + self.number_of_breakdowns - 1, starter_column + 1,
                                   self.parent_workbook.parent_report.overall_text,
                                   self.formats['HEADER'])
        self.worksheet.write(row + self.number_of_breakdowns, starter_column, 'Count', self.formats['HEADER'])
        self.worksheet.write(row + self.number_of_breakdowns, starter_column + 1, 'Percent', self.formats['HEADER'])

        # Write Headers for main breakdown
        if responses_bool:
            report.write_headers(crosstabdict['table'], self.worksheet, row, starter_column + 2,
                                 self.formats['HEADER'])

            # set header row height for all levels
            for i in list(range(self.number_of_breakdowns)):
                self.worksheet.set_row(i + row, report_config.HEADER_ROW_HEIGHT)

        row += self.number_of_breakdowns

        self.worksheet.write(row, question_info_column, 'Option', self.formats['HEADER'])
        row += 1

        for option_number in question.response_options:
            option_text = question.response_options[option_number]
            if question.scored:
                self.worksheet.write(row, question_info_column - 1, '',
                                     self.formats[f'{question.option_score(option_number).upper()}_SQUARE'])
                option_text = f'{option_text} ({question.option_score_string(option_number)})'

            self.worksheet.write(row, question_info_column, option_text, self.formats['OPTION'])

            write_row_from_df(crosstabtotaldict['table'].loc[option_number], self.worksheet, row, starter_column,
                              self.formats['VALUE'], self.formats['PERCENT'])

            if responses_bool:
                write_row_from_df(crosstabdict['table'].loc[option_number], self.worksheet, row, starter_column + 2,
                                  self.formats['VALUE'], self.formats['PERCENT'])

            row += 1

        self.worksheet.write(row, 2, 'Total Responses', self.formats['OPTION_TOTAL'])

        write_row_from_df(crosstabtotaldict['overall'], self.worksheet, row, starter_column,
                          self.formats['VALUE_TOTAL'],
                          self.formats['PERCENT_TOTAL'])

        if responses_bool:
            write_row_from_df(crosstabdict['overall'], self.worksheet, row, starter_column + 2,
                              self.formats['VALUE_TOTAL'],
                              self.formats['PERCENT_TOTAL'])

        row += report_config.ROWS_AFTER_QUESTION

        self.row = row

    # write main questions
    def write_all_questions(self):
        # Write normal questions
        for question in self.questions:
            self.write_question(question)

        self.worksheet.write(self.row, 2, 'Targeted Questions', self.formats['TARGETED_HEADER'])
        self.worksheet.write(self.row + 1, 2,
                             'To produce more meaningful results for questions that may not be applicable to all respondents, results are shown below exluding response codes such as "N/A" or "I did not need".',
                             self.formats['QUESTION'])
        self.worksheet.write(self.row + 2, 2,
                             'If this is also a scored question, these are the values used to calculate Positive Scores.',
                             self.formats['QUESTION'])

        self.row += 5

        # write targetted questions
        for question in self.questions:
            self.write_question(question, targeted=True)
