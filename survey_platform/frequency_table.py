import xlsxwriter
from . import survey_platform as sp
from . import config, frequency_table_config


def get_frequency_table(source, questions, suppression_threshold=0, sheet_breakdown_fields=None,
                        survey_name='Picker Survey', output_path=None, file_name=''):
    df = source.copy()

    output_path = r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\freq' if output_path is None else output_path
    workbook = xlsxwriter.Workbook(f'{output_path}\\{sp.sanitise_for_path(file_name)}Frequency_Table_Report.xlsx')

    # Spreadsheet formats
    formats = {key: workbook.add_format(value) for (key, value) in frequency_table_config.FORMATS.items()}

    sheet_breakdown_fields = ['Total'] if sheet_breakdown_fields is None else sheet_breakdown_fields
    for sheet_breakdown_field in sheet_breakdown_fields:
        worksheet = workbook.add_worksheet(sp.create_worksheet_name(sheet_breakdown_field))

        # workseet general formatting and setup
        worksheet.hide_gridlines(2)
        worksheet.hide_row_col_headers()
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

        table_start_row = row = 6
        column = 3

        # Create sheet breakdown list with 'Total' at the start
        sheet_breakdown_values = ['Total'] if sheet_breakdown_field == 'Total' else ['Total'] + sorted(
            df[sheet_breakdown_field].fillna('BLANK').unique().tolist())

        # Move blanks to the end
        if 'BLANK' in sheet_breakdown_values:
            sheet_breakdown_values.sort(key='BLANK'.__eq__)

        for index_sheet_breakdown_value, sheet_breakdown_value in enumerate(sheet_breakdown_values):
            # Determine if first breakdown column
            first_breakdown_column = True if index_sheet_breakdown_value == 0 else False

            # filter to breakdown_value only
            breakdown_sheet_value_df = df[
                df[sheet_breakdown_field] == sheet_breakdown_value] if not first_breakdown_column else df

            for question in questions:
                if question.q_type not in [config.MULTI_CODE, config.SINGLE_CODE]:
                    continue

                breakdown_sheet_value_question_df = breakdown_sheet_value_df[question.question_columns]

                # calculate total responses
                breakdown_value_total_responses = breakdown_sheet_value_question_df.notna().any(axis='columns').sum()

                # calcualte scorable responses fro scored single response questions
                if question.scored:
                    if question.q_type == config.SINGLE_CODE:
                        breakdown_value_total_scorable_responses = breakdown_sheet_value_question_df.isin(
                            question.scored_responses).to_numpy().sum()
                    else:
                        breakdown_value_total_scorable_responses = (
                                    breakdown_sheet_value_question_df[question.scored_columns].sum(
                                        axis=1) > 0).to_numpy().sum()

                    percent_scorable = (breakdown_value_total_scorable_responses / breakdown_value_total_responses)*100

                suppressed = True if breakdown_value_total_responses < suppression_threshold else False

                # if the first of the breakdowns, write the question text
                if first_breakdown_column:
                    # Append Multi and scored indicators
                    q_text = question.text

                    if question.q_type == config.MULTI_CODE:
                        q_text = q_text + " (Multi-response)"
                    if question.scored:
                        q_text = q_text + " (Scored Question)"

                    # write the question text
                    worksheet.write(row, 2, f"{question.qid}: {q_text}", formats['QUESTION'])

                row += 2

                # merge the header row and set height
                worksheet.merge_range(row, column, row, column + 1, sheet_breakdown_value, formats['HEADER'])
                worksheet.set_row(row, 50)

                row += 1

                # write headers
                # if the first of the breakdowns, also write option header
                if first_breakdown_column:
                    worksheet.write(row, 2, 'Option', formats['HEADER'])
                worksheet.write(row, column, 'Count', formats['HEADER'])
                worksheet.write(row, column + 1, '%', formats['HEADER'])

                row += 1

                for option_number in question.response_options:
                    if first_breakdown_column:
                        option_text = question.response_options[option_number]

                        # add positive score information to option text
                        if question.scored:
                            worksheet.write(row, 1, '',
                                            formats[f'{question.option_score(option_number).upper()}_SQUARE'])
                            option_text = f'{option_text} ({question.option_score_string(option_number)})'

                        worksheet.write(row, 2, option_text, formats['OPTION'])

                    if suppressed:
                        worksheet.write(row, column, config.SUPPRESSION_SYMBOL, formats['VALUE'])
                        worksheet.write(row, column + 1, config.SUPPRESSION_SYMBOL, formats['PERCENT'])

                    else:
                        if question.q_type == config.MULTI_CODE:
                            count_option_responses = (
                                    breakdown_sheet_value_question_df[f'{question.qid}_{option_number}'] == 1).sum()
                        else:
                            count_option_responses = (
                                    breakdown_sheet_value_question_df[question.qid] == option_number).sum()

                        response_percent = (count_option_responses / breakdown_value_total_responses) * 100

                        worksheet.write(row, column, count_option_responses, formats['VALUE'])
                        worksheet.write(row, column + 1, round(response_percent, 5), formats['PERCENT'])

                    row += 1

                if first_breakdown_column:
                    worksheet.write(row, 2, 'Total Responses', formats['OPTION_TOTAL'])

                if suppressed:
                    worksheet.write(row, column, config.SUPPRESSION_SYMBOL, formats['VALUE_TOTAL'])
                    worksheet.write(row, column + 1, config.SUPPRESSION_SYMBOL, formats['VALUE_TOTAL'])
                else:
                    worksheet.write(row, column, breakdown_value_total_responses, formats['VALUE_TOTAL'])
                    worksheet.write(row, column + 1, 100, formats['PERCENT_TOTAL'])

                    if question.scored:
                        row += 1
                        if first_breakdown_column:
                            worksheet.write(row, 2, 'Total Scorable Responses', formats['OPTION_TOTAL'])

                        # noinspection PyUnboundLocalVariable
                        worksheet.write(row, column, breakdown_value_total_scorable_responses, formats['VALUE_TOTAL'])
                        # noinspection PyUnboundLocalVariable
                        worksheet.write(row, column + 1, percent_scorable, formats['PERCENT_TOTAL'])
                row += 3
            column = column + 2
            row = table_start_row
    workbook.close()
