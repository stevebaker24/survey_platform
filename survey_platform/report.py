from pathlib import Path

import pandas as pd
import xlsxwriter

import config
from survey_platform import survey_platform as sp


def is_iterable(thing) -> bool:
    """Creates worksheets name"""
    return True if isinstance(thing, list) or isinstance(thing, tuple) else False


def get_worksheet_name(sheet_breakdown):
    """Creates worksheets name"""
    if len(sheet_breakdown) > 1:
        return f"Multi - {[', '.join([str(elem) for elem in sheet_breakdown])]}"
    else:
        return str(sheet_breakdown[0])


def series_fill_na(series: pd.Series, fill_value: str = None) -> pd.Series:
    """Fills null values with a string, for example for Localities which are blank"""

    if not isinstance(series, pd.Series):
        raise Exception("Input must be a pandas series object")

    if fill_value is not None:
        series = series.fillna(fill_value)

    return series


class Report:
    """Parent class for all reports"""

    def __init__(self,
                 source,
                 output_path,
                 sheet_breakdowns=None,
                 questions=None,
                 suppression_threshold=config.DEFAULT_SUPPRESSION_LIMIT,
                 survey_name=config.DEFAULT_SURVEY_NAME,
                 suppression_framework=None,
                 fill_value=None):
        self.source = source

        self.questions = questions

        self.workbook = None

        self.fill_value = config.DEFAULT_FILL_VALUE if fill_value is None else fill_value
        self.suppression_threshold = suppression_threshold
        self.suppression_framework = suppression_framework

        self.output_path = config.DEFAULT_OUTPUT_PATH if output_path is None else Path(output_path)
        self.file_name = 'TEST FILE NAME'
        self.report_name = 'TEST REPORT NAME'
        self.survey_name = survey_name

        self.sheet_breakdowns = sheet_breakdowns if is_iterable(sheet_breakdowns) else [sheet_breakdowns]


class ReportWorkbook:
    """An individual workbook of a report"""

    def __init__(self, workbook_data, breakdown_fields, output_path):
        pass
        self.workbook_data = workbook_data

        self.breakdown_fields = breakdown_fields

        self.file_name = 'TEST FILE NAME'
        self.report_name = 'TEST REPORT NAME'
        self.file_name = f"{sp.sanitise_for_path(self.file_name)}_{self.report_name}.xlsx"
        self.output_path = config.DEFAULT_OUTPUT_PATH
        self.workbook_path = self.output_path.joinpath(self.file_name)

        self.workbook = self.create_workbook()
        self.worksheets = []

    def create_workbook(self) -> xlsxwriter.Workbook:
        """Creates an excel workbook to build the report in"""
        workbook = xlsxwriter.Workbook(self.workbook_path)
        return workbook

    def create_sheets(self):
        for sheet_breakdown in self.breakdown_fields:
            # add worksheet to workbook object
            sheet_breakdown = sheet_breakdown if is_iterable(sheet_breakdown) else [sheet_breakdown]

            worksheet_name = sp.sanitize_worksheet_name(get_worksheet_name(sheet_breakdown))
            worksheet = self.workbook.add_worksheet(worksheet_name)
            report_worksheet = ReportWorksheet(worksheet, sheet_breakdown)
            self.worksheets.append(report_worksheet)


class ReportWorksheet:
    """An individual worksheet of a report"""

    def __init__(self, sheet_data, worksheet, sheet_breakdown):

        self.sheet_data = sheet_data
        self.fill_na()

        self.sheet_breakdown = sheet_breakdown
        self.worksheet = worksheet

        self.sheet_name = get_worksheet_name(self.sheet_breakdown)
        self.number_of_breakdowns = len(sheet_breakdown)

    def fill_na(self):
        if is_iterable(self.sheet_breakdown):
            for field in self.sheet_breakdown:
                series = self.sheetdata[field]
                self.sheet_data[field] = series_fill_na(series)

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

    def get_sheet_breakdown_values(self, series: pd.Series) -> list:
        """Not immediately useful right now but will kee method around .Creates set of unique values from a series"""
        if not isinstance(series, pd.Series):
            raise Exception("Input must be a pandas series object")

        # sort unique values alphabetically
        unique_values = sorted(series.unique())

        # Move 'Blank' populated field to the end if blanks are filled.
        if self.fill_value is not None and self.fill_value in unique_values:
            unique_values.sort(key=self.fill_value.__eq__)
        # BLANK sorting in index, cant do alphabetically...

        return unique_values
