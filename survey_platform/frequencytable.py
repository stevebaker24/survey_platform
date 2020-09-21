def get_frequency_table(source, questions, suppression_threshold, sheet_breakdown_fields=[], file_breakdown_field=None, file_breakdown_values=[]):

    if len(file_breakdown_values) == 0 and file_breakdown_field != None:
        file_breakdown_values = source[file_breakdown_field].fillna('BLANK').unique().tolist()

    if file_breakdown_field == None:
        file_breakdown_values = ['Total']

    for file_breakdown_value in file_breakdown_values:
        if file_breakdown_field == None:
            breakdown_file_df = source
        else:
            breakdown_file_df = source[source[file_breakdown_field] == file_breakdown_value]


        workbook = xlsxwriter.Workbook(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\freq' + '\\' +  file_breakdown_value.replace("/", "") + '_NMEC_Frequency_Table_Report.xlsx')

        question_format = workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_color': '#4d4639'})
        header_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'bold': True, 'text_wrap': True, 'border': 1, 'border_color': 'white',
             'font_name': 'Arial', 'font_color': 'white', 'bg_color': '#5b4173'})
        value_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#4d4639', 'font_name': 'Arial',
             'font_color': '#4d4639'})
        value_total_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#4d4639',
             'font_name': 'Arial', 'font_color': '#4d4639'})
        percent_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#4d4639', 'font_name': 'Arial',
             'font_color': '#4d4639', 'num_format': '0.0'})
        option_format = workbook.add_format(
            {'border': 1, 'border_color': '#4d4639', 'valign': 'vcenter', 'text_wrap': True, 'font_name': 'Arial',
             'font_color': '#4d4639'})
        option_total_format = workbook.add_format(
            {'bold': True, 'border': 1, 'border_color': '#4d4639', 'valign': 'vcenter', 'text_wrap': True,
             'font_name': 'Arial', 'font_color': '#4d4639'})
        subtitle_format = workbook.add_format(
            {'valign': 'vcenter', 'font_name': 'Arial', 'font_color': '#4d4639', 'bold': True})

        if len(sheet_breakdown_fields) == 0:
            sheet_breakdown_fields.append('Total')

        for sheet_breakdown_field in sheet_breakdown_fields:
            #sanitise for worksheets
            worksheet = workbook.add_worksheet(create_worksheet_name(sheet_breakdown_field))

            worksheet.hide_gridlines(2)

            worksheet.set_column('A:A', 1)
            worksheet.set_column('B:B', 50)
            worksheet.set_column('C:Z', 12.29)

            #worksheet.set_row(0, 90)

            worksheet.insert_image('B1', r'C:\Users\steve.baker\Desktop\MAT Nonsense\picker2.png', {'y_offset': 29, 'x_offset': 10})

            row = 1
            worksheet.write(row, 2, 'New mothers\' experiences of care survey 2020', subtitle_format)
            row = 2
            worksheet.write(row, 2, f'{file_breakdown_value} Frequency Tables Report', subtitle_format)
            row = 3
            worksheet.write(row, 2, f'Broken Down By: {sheet_breakdown_field}', subtitle_format)


            worksheet.freeze_panes(row+2, 0)

            row += 3
            table_start_row = row

            column = 2

            if sheet_breakdown_field == 'Total':
                sheet_breakdown_values = ['Total']
            else:
                sheet_breakdown_values = breakdown_file_df[sheet_breakdown_field].fillna('BLANK').unique().tolist()
                sheet_breakdown_values = sorted(sheet_breakdown_values)
                sheet_breakdown_values = ['Total'] + sheet_breakdown_values

                if 'BLANK' in sheet_breakdown_values:
                    sheet_breakdown_values.remove('BLANK')
                    sheet_breakdown_values = sheet_breakdown_values + ['BLANK']




            for index_sheet_breakdown_value, sheet_breakdown_value in enumerate(sheet_breakdown_values):
                # filter to breakdown_value only
                if sheet_breakdown_value == 'Total (Number of Respondents)' or sheet_breakdown_field == 'Total':
                    breakdown_sheet_value_df = breakdown_file_df
                else:
                    breakdown_sheet_value_df = breakdown_file_df[breakdown_file_df[sheet_breakdown_field] == sheet_breakdown_value]

                # iterate through the questions
                targeted_questions = []

                for question in questions.questions_dict['P']:

                    q_type = question.q_type

                    if q_type not in ['S', 'M']:
                        continue

                    qid = question.get_qid()
                    q_text = question.q_text
                    q_response_options = question.get_responses()

                    scored = question.scored

                    if scored:
                        score_map = question.get_score_map()
                        score_responses = question.get_score_responses()
                        if question.targeted:
                            targeted_questions.append(question)

                    def calcualte_breakdown_value_total_responses(q_type, q_text, q_response_options, breakdown_sheet_value_df):
                        #calculate total vaue for the breakdown
                        if q_type == 'M':
                            qids = []
                            for option in q_response_options:
                                qids.append(f'{qid}_{option}')
                            breakdown_value_total_responses = len(breakdown_sheet_value_df[qids].dropna(how='all'))

                        elif q_type == 'S':
                            breakdown_value_total_responses = (breakdown_sheet_value_df[qid].notnull()).sum()

                        return breakdown_value_total_responses

                    breakdown_value_total_responses = calcualte_breakdown_value_total_responses(q_type, q_text, q_response_options, breakdown_sheet_value_df)

                    #if the first of the breakdowns
                    if index_sheet_breakdown_value == 0:

                        if q_type == 'M':
                            q_text = f'{q_text} (Multi-response)'
                        if scored:
                            q_text = f'{q_text} (Scored Question)'

                        worksheet.write(row, 1, f"{qid}: {q_text}", question_format)

                    row += 2

                    worksheet.merge_range(row, column, row, column + 1, sheet_breakdown_value, header_format)
                    worksheet.set_row(row, 50)

                    row += 1

                    if index_sheet_breakdown_value == 0:
                        worksheet.write(row, 1, 'Option', header_format)

                    worksheet.write(row, column, 'Count', header_format)
                    worksheet.write(row, column + 1, '%', header_format)

                    row += 1

                    breakdown_value_total_percent = 0

                    for option_number in q_response_options:
                        if index_sheet_breakdown_value == 0:
                            response_option = q_response_options[option_number]

                            if scored:
                                if option_number in score_responses['pos']:
                                    response_option = f'{response_option} (Positive)'
                                if option_number in score_responses['neu']:
                                    response_option = f'{response_option} (Neutral)'
                                if option_number in score_responses['neg']:
                                    response_option = f'{response_option} (Negative)'
                                if option_number in score_responses['ignore']:
                                    response_option = f'{response_option} (Excluded)'

                            worksheet.write(row, 1, response_option, option_format)

                        if breakdown_value_total_responses < suppression_threshold:
                            count_option_responses = '*'
                            response_percent = '*'
                            breakdown_value_total_percent = '*'
                        else:
                            if q_type == 'M':
                                count_option_responses = (breakdown_sheet_value_df[f'{qid}_{option_number}'] == 1).sum()
                            elif q_type == 'S':
                                count_option_responses = (breakdown_sheet_value_df[qid] == option_number).sum()

                            response_percent_noround = (count_option_responses / breakdown_value_total_responses) * 100
                            response_percent = round(response_percent_noround, 5)

                            if q_type == 'M':
                                breakdown_value_total_percent = 'N/A'
                            elif q_type == 'S':
                                breakdown_value_total_percent += response_percent_noround

                        worksheet.write(row, column, count_option_responses, value_format)
                        worksheet.write(row, column + 1, response_percent, percent_format)

                        row += 1

                        worksheet.write(row, column + 1, breakdown_value_total_percent, value_total_format)

                        if index_sheet_breakdown_value == 0:
                            total_text = 'Total (Number of Respondents)' if q_type == 'M' else 'Total'
                            worksheet.write(row, 1, total_text, option_total_format)

                    if breakdown_value_total_responses < suppression_threshold:
                        worksheet.write(row, column, '*', value_total_format)
                    else:
                        worksheet.write(row, column, breakdown_value_total_responses, value_total_format)

                    row += 3






                worksheet.write(row, 1, 'Targeted \'Plus\' Questions', question_format)
                row += 3







                for question in targeted_questions:
                    q_type = question.q_type

                    if q_type not in ['S', 'M']:
                        continue

                    qid = question.get_qid()
                    q_text = question.q_text
                    q_response_options = question.get_responses()

                    scored = question.scored

                    if scored:
                        score_map = question.get_score_map()
                        score_responses = question.get_score_responses()
                        q_text = f'{q_text} (Scored Question)'
                        scored_responses = question.get_scored_responses()


                    #calculate total vaue for the breakdown
                    if q_type == 'M':
                        q_text = f'{q_text} (Multi-response)'
                        qids = question.get_scored_columns()
                        breakdown_value_total_responses = len(breakdown_sheet_value_df[qids].dropna(how='all'))

                    elif q_type == 'S':
                        breakdown_value_total_responses = breakdown_sheet_value_df[qid].isin(scored_responses).sum()

                    #if the first of the breakdowns
                    if index_sheet_breakdown_value == 0:
                        worksheet.write(row, 1, f"{qid}+: {q_text}", question_format)

                    row += 2

                    worksheet.merge_range(row, column, row, column + 1, sheet_breakdown_value, header_format)
                    worksheet.set_row(row, 50)

                    row += 1

                    if index_sheet_breakdown_value == 0:
                        worksheet.write(row, 1, 'Option', header_format)

                    worksheet.write(row, column, 'Count', header_format)
                    worksheet.write(row, column + 1, '%', header_format)

                    row += 1

                    breakdown_value_total_percent = 0

                    for option_number in scored_responses:
                        if index_sheet_breakdown_value == 0:
                            response_option = q_response_options[option_number]

                            if scored:
                                if option_number in score_responses['pos']:
                                    response_option = f'{response_option} (Positive)'
                                if option_number in score_responses['neu']:
                                    response_option = f'{response_option} (Neutral)'
                                if option_number in score_responses['neg']:
                                    response_option = f'{response_option} (Negative)'
                                if option_number in score_responses['ignore']:
                                    continue


                            worksheet.write(row, 1, response_option, option_format)

                        if breakdown_value_total_responses < suppression_threshold:
                            count_option_responses = '*'
                            response_percent = '*'
                            breakdown_value_total_percent = '*'
                        else:
                            if q_type == 'M':
                                count_option_responses = (breakdown_sheet_value_df[f'{qid}_{option_number}'] == 1).sum()
                            elif q_type == 'S':
                                count_option_responses = (breakdown_sheet_value_df[qid] == option_number).sum()

                            response_percent_noround = (count_option_responses / breakdown_value_total_responses) * 100
                            response_percent = round(response_percent_noround, 5)

                            if q_type == 'M':
                                breakdown_value_total_percent = 'N/A'
                            elif q_type == 'S':
                                breakdown_value_total_percent += response_percent_noround

                        worksheet.write(row, column, count_option_responses, value_format)
                        worksheet.write(row, column + 1, response_percent, percent_format)

                        row += 1

                        worksheet.write(row, column + 1, breakdown_value_total_percent, value_total_format)

                        if index_sheet_breakdown_value == 0:
                            total_text = 'Total (Respondents)' if q_type == 'M' else 'Total'
                            worksheet.write(row, 1, total_text, option_total_format)

                    if breakdown_value_total_responses < suppression_threshold:
                        worksheet.write(row, column, '*', value_total_format)
                    else:
                        worksheet.write(row, column, breakdown_value_total_responses, value_total_format)

                    row += 3


                column = column + 2
                row = table_start_row

        workbook.close()