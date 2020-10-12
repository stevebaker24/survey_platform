from pathlib import Path

import pandas as pd
import xlsxwriter

import config
from survey_platform import survey_platform as sp


class ReportWorkbook:
    """An individual workbook of a report"""

    def __init__(self):
        pass
        self.workbook = self.create_workbook()
        self.sheets = []

    def create_workbook(self) -> xlsxwriter.Workbook:
        """Creates an excel workbook to build the report in"""

        workbook_path = f'{self.output_path}\\{sp.sanitise_for_path(self.file_name)}{self.report_name}.xlsx'
        workbook = xlsxwriter.Workbook(workbook_path)
        return workbook

    def add_sheet(self, report_worksheet):
        self.sheets.append(report_worksheet)

    def get_sheet_breakdown_values(self, series: pd.Series) -> list:
        """Creates set of unique values from a series"""

        if not isinstance(series, pd.Series):
            raise Exception("Input must be a pandas series object")

        # sort unique values alphabetically
        unique_values = sorted(series.unique())

        # Move 'Blank' populated field to the end if blanks are filled.
        if self.fill_value is not None and self.fill_value in unique_values:
            unique_values.sort(key=self.fill_value.__eq__)

        return unique_values


class ReportWorksheet:
    """An individual worksheet of a report"""
    def __init__(self, sheet_breakdown):

        self.sheet_name = self.worksheet_details(sheet_breakdown)['worksheet_name']
        self.number_of_breakdowns = self.worksheet_details(sheet_breakdown)['number_of_breakdowns']

        self.worksheet = self.create_worksheet()

    def create_worksheet(self) -> xlsxwriter.Workbook.worksheet_class:
        """Creates a worksheet in the workbook"""
        # sanitise name for filename
        worksheet_name = sp.create_worksheet_name(self.sheet_name)
        return self.workbook.add_worksheet(sp.create_worksheet_name(worksheet_name))

    @staticmethod
    def worksheet_details(sheet_breakdown) -> dict:
        """Creates worksheets probbaly needs some changing"""
        if isinstance(sheet_breakdown, list) or isinstance(sheet_breakdown, tuple):
            worksheet_name = f"Multi - {[', '.join([str(elem) for elem in sheet_breakdown])]}"
            number_of_breakdowns = len(sheet_breakdown)
        else:
            worksheet_name = str(sheet_breakdown)
            number_of_breakdowns = 1

        return dict(worksheet_name=worksheet_name, number_of_breakdowns=number_of_breakdowns)


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

        self.sheet_breakdowns = sheet_breakdowns

    @staticmethod
    def series_fill_na(series: pd.Series, fill_value: str = None) -> pd.Series:
        """Fills null values with a string, for example for Localities which are blank"""

        if not isinstance(series, pd.Series):
            raise Exception("Input must be a pandas series object")

        if fill_value is not None:
            series = series.fillna(fill_value)

        return series






