from pathlib import Path
import pandas as pd
import xlsxwriter

import config
import survey_platform as sp





def get_agg_df(data: pd.DataFrame, breakdown_field: list, agg_method: str) -> pd.DataFrame:
    """aggregates a df either by the breakdown field list, or if there is to be no breakdown, just aggregate"""

    if breakdown_field is not None:
        df = data.groupby(breakdown_field)
    else:
        # If no breakdown, create artificial field to group by
        data['GROUP'] = 1
        df = data.groupby('GROUP')

    # Apply aggregation method to the group object according to agg_method
    df = eval(f'df.{agg_method}().transpose()')

    # If there are blanks, meove the ZZZZ which is there to keep them at the back alphabetically
    df = df.rename({'ZZZZZBLANK': 'BLANK'}, axis='columns')

    return df


def is_iterable(thing) -> bool:
    """Creates worksheets name"""
    return True if isinstance(thing, list) or isinstance(thing, tuple) else False


def write_breakdown_level_names(df, worksheet, row, start_column, workbook_format):
    for index, level_name in enumerate(df.columns.names):
        if level_name is not None:
            worksheet.write((row + index), start_column - 1, level_name, workbook_format)


def write_categories(categories, worksheet, row, column, workbook_format):
    start_merge_index = 0
    len_categories = len(categories)

    for index, category in enumerate(categories):
        if index == len_categories - 1 or categories[index + 1] != category:
            # if no merge needed, write only a single cell
            if index == start_merge_index:
                worksheet.write(row + index, column, category, workbook_format)
            # if there are multiple cells, write as a merge
            else:
                worksheet.merge_range(row + start_merge_index, column, row + index,
                                      column,
                                      category, workbook_format)

            start_merge_index = index + 1


def write_headers(df, worksheet, row, start_column, workbook_format):
    header_row = row
    number_of_levels = df.columns.nlevels

    def write_multi_level(subset, level, first_column):
        start_merge_index = 0
        number_of_codes = len(subset)

        for index, code in enumerate(subset):
            if index == number_of_codes - 1 or subset[index + 1] != code:

                value = df.columns.levels[level][code]
                # value = str(level) + '/' + str(code)

                # if no merge needed, write only a single cell
                if index == start_merge_index:
                    worksheet.write(header_row + level, (first_column + index), value, workbook_format)
                # if there are multiple cells, write as a merge
                else:
                    worksheet.merge_range(header_row + level, (first_column + start_merge_index), header_row + level,
                                          (first_column + index),
                                          value, workbook_format)

                if level < number_of_levels - 1:
                    next_subset = df.columns.codes[level + 1][start_merge_index:index + 1]
                    write_multi_level(next_subset, level + 1, first_column=first_column + start_merge_index)

                start_merge_index = index + 1

    def write_single_level(column):
        for column_name in df.columns:
            worksheet.write(header_row, column, column_name, workbook_format)
            column += 1

    if number_of_levels > 1:
        codes = df.columns.codes[0]
        write_multi_level(codes, level=0, first_column=start_column)
    else:
        write_single_level(start_column)


def series_fill_na(series: pd.Series, fill_value: str = None) -> pd.Series:
    """Fills null values with a string, for example for Localities which are blank"""

    if not isinstance(series, pd.Series):
        raise Exception("Input must be a pandas series object")

    if fill_value is not None:
        series = series.fillna(f'ZZZZZ{fill_value}')

    return series


class Report:
    """Parent class for all reports"""

    def __init__(self,
                 source,
                 output_path,
                 questions,
                 sheet_breakdown_fields=None,
                 suppression_threshold=config.DEFAULT_SUPPRESSION_LIMIT,
                 survey_name=config.DEFAULT_SURVEY_NAME,
                 suppression_framework=None,
                 external_comparator=None,
                 comparator_text=None,
                 overall_text='Overall'):

        self.source = source
        self.external_comparator = external_comparator
        self.comparator_text = comparator_text
        self.questions = questions
        self.overall_text = overall_text

        self.suppression_threshold = suppression_threshold
        self.suppression_framework = suppression_framework

        self.output_path = config.DEFAULT_OUTPUT_PATH if output_path is None else Path(output_path)
        self.file_name = survey_name
        self.survey_name = survey_name

        self.sheet_breakdown_fields = sheet_breakdown_fields

        # Create the correct ReportWorkbook object
        self.workbook_class(self)


class ReportWorkbook:
    """An individual workbook of a report"""

    def __init__(self, parent_report):
        self.parent_report = parent_report

        self.breakdown_fields_flat = self.flatten_breakdown_fields()

        self.question_fields = self.get_question_fields()

        if self.parent_report.external_comparator is not None:
            self.external_comparator_data = self.create_external_comparator_data()
            self.external_comparator_n = self.external_comparator_n()
            self.comparator_text = self.parent_report.comparator_text
        else:
            self.external_comparator_data = None

        self.workbook_data = self.create_workbook_data()

        # The type of worksheet class being used, defined in child class
        self.worksheet_class = parent_report.worksheet_class

        self.file_name = parent_report.file_name
        self.report_name = parent_report.report_name

        self.file_name = f"{sp.sanitise_for_path(self.file_name)}_{self.report_name}.xlsx"
        self.output_path = config.DEFAULT_OUTPUT_PATH if parent_report.output_path is None else parent_report.output_path
        self.workbook_path = self.output_path.joinpath(self.file_name)

        self.workbook = self.create_workbook()
        self.formats = self.create_report_formats()

        try:
            self.create_guidance_page()
        except:
            pass

        self.worksheets = []
        self.create_sheets()
        self.workbook.close()

    def external_comparator_n(self):
        return len(self.parent_report.external_comparator)

    def create_external_comparator_data(self):
        df = self.parent_report.external_comparator
        df = df[self.question_fields]
        df = self.calculate_workbook_data(df)
        df = self.calculate_external_comparator(df)
        return df

    def create_workbook_data(self):
        df = self.parent_report.source
        df = self.drop_unnessecary_columns(df)
        df = self.fill_empty_breakdown_values(df)
        df = self.calculate_workbook_data(df)
        return df

    def get_question_fields(self):
        #if not overridden by child class, just get all question columns
        return self.parent_report.questions.all_question_columns


    def calculate_workbook_data(self, df):
        #not always needed
        return df

    def drop_unnessecary_columns(self, df):
        return df.drop(columns=self.get_columns_to_drop(df))

    def fill_empty_breakdown_values(self, df):
        for field in self.breakdown_fields_flat:
            if field is not None:
                df[field] = series_fill_na(df[field], 'BLANK')
        return df

    def get_columns_to_drop(self, df):
        columns_to_keep = self.breakdown_fields_flat + self.question_fields
        return list(set(df.columns).difference(columns_to_keep))

    def flatten_breakdown_fields(self):
        """retuerns a flat list of all unique breakdown fields needed, unique by virtue of set conversion"""
        flattened_breakdown_fields = list(set(pd.core.common.flatten(self.parent_report.sheet_breakdown_fields)))
        #Remove any 'None' values before returning:
        return [x for x in flattened_breakdown_fields if x]

    # def create_workbook_data(self, scored, ses):
    #     if scored:
    #         data = sp.calc_scores(self.parent_report.source, self.parent_report.questions, ['pos'])
    #
    #         self.score_columns = [f"{x.qid}_pos" for x in self.parent_report.questions.scored_questions]
    #         self.total_count = data[self.score_columns].count()
    #         self.total_mean = data[self.score_columns] \
    #             .mean() \
    #             .mask(self.total_count < self.parent_report.suppression_threshold) \
    #             .div(100) \
    #             .fillna('*')
    #         return data
    #     if ses:
    #         report_breakdown_fields = list(set(pd.core.common.flatten(self.parent_report.breakdown_fields)))
    #         columns_to_keep = report_breakdown_fields + ses_questions
    #         columns_to_drop = list(set(self.parent_report.source.columns).difference(columns_to_keep))
    #         self.parent_report.source = self.parent_report.source.drop(columns=columns_to_drop)
    #
    #         for field in report_breakdown_fields:
    #             self.parent_report.source[field] = series_fill_na(self.parent_report.source[field], 'BLANK')
    #
    #         for sesq in ses_questions:
    #             self.parent_report.source[sesq] = self.parent_report.source[sesq].map(sesmap)
    #         return self.parent_report.source
    #     else:
    #         return self.parent_report.source

    def create_report_formats(self):
        return {key: self.workbook.add_format(value) for (key, value) in self.format_dict.items()}

    def create_workbook(self) -> xlsxwriter.Workbook:
        """Creates an excel workbook to build the report in"""
        workbook = xlsxwriter.Workbook(self.workbook_path)
        return workbook

    def create_sheets(self):
        number_of_multi_levels = 0
        for i, sheet_breakdown in enumerate(self.parent_report.sheet_breakdown_fields):
            # add worksheet to workbook object
            sheet_breakdown = sheet_breakdown if is_iterable(sheet_breakdown) else [sheet_breakdown]

            if sheet_breakdown[0] is None:
                worksheet_name = 'Total'
            elif len(sheet_breakdown) == 1:
                worksheet_name = sheet_breakdown[0]
            else:
                number_of_multi_levels += 1
                worksheet_name = f"Multi-level {number_of_multi_levels}"


            worksheet = self.workbook.add_worksheet(sp.sanitize_worksheet_name(worksheet_name))

            #if sheet_breakdown[0] is not None:
            columns_to_drop = list(set(self.breakdown_fields_flat).difference(sheet_breakdown))
            worksheet_data = self.workbook_data.drop(columns=columns_to_drop)

            report_worksheet = self.worksheet_class(worksheet_data, worksheet, sheet_breakdown, self)

            self.worksheets.append(report_worksheet)


class ReportWorksheet:
    """An individual worksheet of a report"""

    def __init__(self, sheet_data, worksheet, sheet_breakdown, parent_workbook):
        self.parent_workbook = parent_workbook

        self.external_comparator = True if self.parent_workbook.external_comparator_data is not None else False

        self.sheet_data = sheet_data
        self.sheet_breakdown = sheet_breakdown

        self.formats = parent_workbook.formats



        self.survey_name = parent_workbook.parent_report.survey_name
        self.questions = parent_workbook.parent_report.questions

        self.worksheet = worksheet
        self.number_of_breakdowns = len(sheet_breakdown)

        self.breakdown_text = self.generate_breakdown_text()

    def generate_breakdown_text(self):
        if len(self.sheet_breakdown) > 1:
            return f"{[', '.join([str(elem) for elem in self.sheet_breakdown])][0]}"
        else:
            return str(self.sheet_breakdown[0])

    @staticmethod
    def write_row_from_df(df_row, worksheet, row, column, format_count, format_percent):
        for index, value in enumerate(df_row):
            if index % 2:
                worksheet.write(row, column, value, format_percent)
            else:
                worksheet.write(row, column, value, format_count)
            column += 1

    @staticmethod
    def write_breakdown_level_names(df, worksheet, row, start_column, workbook_format):
        for index, level_name in enumerate(df.columns.names):
            if level_name is not None:
                worksheet.write((row + index), start_column - 1, level_name, workbook_format)

    @staticmethod
    def write_headers(df, worksheet, row, start_column, workbook_format):
        header_row = row
        number_of_levels = df.columns.nlevels

        def write_level(subset, level, first_column):
            start_merge_index = 0
            number_of_codes = len(subset)

            for index, code in enumerate(subset):
                if index == number_of_codes - 1 or subset[index + 1] != code:

                    value = df.columns.levels[level][code]
                    # value = str(level) + '/' + str(code)

                    # if no merge needed, write only a single cell
                    if index == start_merge_index:
                        worksheet.write(header_row + level, (first_column + index), value, workbook_format)
                    # if there are multiple cells, write as a merge
                    else:
                        worksheet.merge_range(header_row + level, (first_column + start_merge_index),
                                              header_row + level,
                                              (first_column + index),
                                              value, workbook_format)

                    if level < number_of_levels - 1:
                        next_subset = df.columns.codes[level + 1][start_merge_index:index + 1]
                        write_level(next_subset, level + 1, first_column=first_column + start_merge_index)

                    start_merge_index = index + 1

        codes = df.columns.codes[0]
        write_level(codes, level=0, first_column=start_column)


