import xlsxwriter
import pandas as pd
import numpy as np

from . import survey_platform as sp
from . import config, frequency_table_config


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


def write_headers(df, worksheet, row, start_column, workbook_format):
    header_row = row
    number_of_levels = df.columns.nlevels

    def write_level(subset, level, first_column):
        start_merge_index = 0
        number_of_codes = len(subset)

        for index, code in enumerate(subset):
            if index == number_of_codes - 1 or subset[index + 1] != code:

                value = df.columns.levels[level][code]
                #value = str(level) + '/' + str(code)

                # if no merge needed, write only a single cell
                if index == start_merge_index:
                    worksheet.write(header_row+level, (first_column + index), value, workbook_format)
                # if there are multiple cells, write as a merge
                else:
                    worksheet.merge_range(header_row+level, (first_column + start_merge_index), header_row+level,
                                          (first_column + index),
                                          value, workbook_format)

                if level < number_of_levels - 1:
                    next_subset = df.columns.codes[level+1][start_merge_index:index+1]
                    write_level(next_subset, level+1, first_column=first_column+start_merge_index)

                start_merge_index = index + 1

    codes = df.columns.codes[0]
    write_level(codes, level=0, first_column=start_column)


def add_missing_options(df, question):
    # Adds response options not picked up bu the cross tab (i.e. no responses for that option
    for option in question.response_options:
        if option not in df.index:
            df.loc[option] = 0
            df.sort_index(inplace=True)


def create_crosstab(df, question, suppression_threshold, breakdown_columns=None):

    breakdown_columns = ['Total'] if breakdown_columns is None else breakdown_columns

    if question.q_type == config.SINGLE_CODE:
        count = pd.crosstab(df[question.qid], breakdown_columns).fillna(0)
        subtotal = count.sum()
    else:
        count = pd.concat(multi_q_count_dfs(df, question, breakdown_columns)).fillna(0)
        subtotal = multi_subtotal(df, question, breakdown_columns)

    # add missing response options
    add_missing_options(count, question)

    # calculate percentage
    percent = (count / subtotal) * 100

    # suppress the count and percent
    suppressed_count = suppress(count, subtotal, suppression_threshold)
    suppressed_percent = suppress(percent, subtotal, suppression_threshold)

    # combine the count and percent into single DF
    suppressed_concatted = combine_count_percent_dfs(suppressed_count, suppressed_percent)

    # calculate the 'total' rows for the bottom:
    if question.q_type == config.SINGLE_CODE:
        total = suppressed_concatted.sum(min_count=1)
    else:
        # cant just sum the count df for multi
        # needs additional to frame and transpose becaise not a df going in
        hello = suppress(subtotal, subtotal, suppression_threshold)
        suppressed_subtotal = suppress(subtotal, subtotal, suppression_threshold).to_frame().transpose()

        # just needs to statically be 100, a sum of the percentages is meaningless
        suppressed_subtotal_percent = suppressed_subtotal.copy()
        suppressed_subtotal_percent.loc[1] = 100
        suppressed_subtotal_percent = suppress(suppressed_subtotal_percent, subtotal, suppression_threshold)

        # combine into one total row and convert df to series
        total = combine_count_percent_dfs(suppressed_subtotal, suppressed_subtotal_percent).squeeze()

    return dict(table=suppressed_concatted.fillna('*'), total=total.fillna('*'))


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


def get_frequency_table(source, questions, suppression_threshold=0, sheet_breakdown_fields=None,
                        survey_name='Picker Survey', output_path=None, file_name=''):
    df = source.copy()

    output_path = r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\freq' if output_path is None else output_path


    # Spreadsheet formats
    formats = {key: workbook.add_format(value) for (key, value) in frequency_table_config.FORMATS.items()}

    # generate breakdown dfs
    sheet_breakdown_fields = ['Total'] if sheet_breakdown_fields is None else sheet_breakdown_fields

    for index, sheet_breakdown_field in enumerate(sheet_breakdown_fields):

        if isinstance(sheet_breakdown_field, list):
            breakdown_columns = [df[x] for x in sheet_breakdown_field]
            numbreakdowns = len(sheet_breakdown_field)
            worksheetname = f'Multi Breakdown {index + 1}'
        else:
            breakdown_columns = df[sheet_breakdown_field]
            numbreakdowns = 1
            worksheetname = sheet_breakdown_field

        worksheet = workbook.add_worksheet(sp.create_worksheet_name(worksheetname))

        # workseet general formatting and setup
        worksheet.hide_gridlines(2)
        worksheet.set_column('A:A', 1)
        worksheet.set_column('B:B', 1)
        worksheet.set_column('C:C', 50)
        worksheet.set_column('D:XFD', 12.29)
        worksheet.insert_image('C1', frequency_table_config.LOGO_PATH, {'y_offset': 29, 'x_offset': 10})
        worksheet.freeze_panes(5, 0)

        # worksheet Title Section
        worksheet.write(1, 3, survey_name, formats['SUBTITLE'])
        worksheet.write(2, 3, 'Frequency Tables Report', formats['SUBTITLE'])
        worksheet.write(3, 3, f'Broken Down By: {sheet_breakdown_field}', formats['SUBTITLE'])

        row = 6
        question_info_column = 2
        starter_column = 3

        for question in questions:
            # Skip Non single/multi questions
            if question.q_type not in [config.SINGLE_CODE, config.MULTI_CODE]:
                continue

            # create crosstabs dicts (for total and breakdown), returns dict of crosstabs
            crosstabtotaldict = create_crosstab(df, question, suppression_threshold)
            crosstabdict = create_crosstab(df, question, suppression_threshold, breakdown_columns)

            # create the question text
            q_text = question.text
            q_text = q_text + " (Multi-response)" if question.q_type == config.MULTI_CODE else q_text
            q_text = q_text + " (Scored Question)" if question.scored else q_text

            # write the question text
            worksheet.write(row, question_info_column, f"{question.qid}: {q_text}", formats['QUESTION'])

            row += 2

            # Wrtie Breakdown Header Names
            write_breakdown_level_names(crosstabdict['table'], worksheet, row, starter_column, formats['LEVEL_TITLE'])

            # Write Total Header
            # not using normal method to allow for vertical merge of total
            worksheet.merge_range(row, starter_column, row+numbreakdowns-1, starter_column+1, 'Total', formats['HEADER'])
            worksheet.write(row + numbreakdowns, starter_column, 'Count', formats['HEADER'])
            worksheet.write(row + numbreakdowns, starter_column+1, 'Percent', formats['HEADER'])

            # Write Headers
            write_headers(crosstabdict['table'], worksheet, row, starter_column+2,
                          formats['HEADER'])

            row += numbreakdowns

            worksheet.write(row, question_info_column, 'Option', formats['HEADER'])
            row += 1

            for option_number in question.response_options:
                option_text = question.response_options[option_number]
                if question.scored:
                    worksheet.write(row, question_info_column - 1, '',
                                    formats[f'{question.option_score(option_number).upper()}_SQUARE'])
                    option_text = f'{option_text} ({question.option_score_string(option_number)})'

                worksheet.write(row, question_info_column, option_text, formats['OPTION'])

                write_row_from_df(crosstabtotaldict['table'].loc[option_number], worksheet, row, starter_column,
                                  formats['VALUE'], formats['PERCENT'])
                write_row_from_df(crosstabdict['table'].loc[option_number], worksheet, row, starter_column+2,
                                  formats['VALUE'], formats['PERCENT'])

                row += 1

            worksheet.write(row, 2, 'Total Responses', formats['OPTION_TOTAL'])

            write_row_from_df(crosstabtotaldict['total'], worksheet, row, starter_column, formats['VALUE_TOTAL'],
                              formats['PERCENT_TOTAL'])
            write_row_from_df(crosstabdict['total'], worksheet, row, starter_column+2, formats['VALUE_TOTAL'],
                              formats['PERCENT_TOTAL'])

            row += frequency_table_config.ROWS_AFTER_QUESTION

    workbook.close()
