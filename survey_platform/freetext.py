def get_freetext(source, questions, sheet_breakdown_fields=[], file_breakdown_field=None, file_breakdown_values=[], suppression_threshold=None, suppression_framework=None):

    source = source[source['Outcome']==1]

    if len(file_breakdown_values) == 0 and file_breakdown_field != None:
        file_breakdown_values = source[file_breakdown_field].unique().tolist()

    if file_breakdown_field == None:
        file_breakdown_values = ['Total']

    for file_breakdown_value in file_breakdown_values:
        if file_breakdown_field == None:
            breakdown_file_df = source
        else:
            breakdown_file_df = source[source[file_breakdown_field] == file_breakdown_value]

        workbook = xlsxwriter.Workbook(
            r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\text' + '\\' + file_breakdown_value.replace("/", "") + '_NMEC_Free_Text_Report.xlsx')

        header_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'bold': True, 'text_wrap': True, 'border': 1, 'border_color': 'white',
             'font_name': 'Arial', 'font_color': 'white', 'bg_color': '#5b4173'})
        value_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#4d4639','text_wrap': True, 'font_name': 'Arial',
             'font_color': '#4d4639'})
        subtitle_format = workbook.add_format(
            {'valign': 'vcenter', 'font_name': 'Arial', 'font_color': '#4d4639', 'bold': True})

        if len (sheet_breakdown_fields) == 0:
            sheet_breakdown_fields.append(file_breakdown_field)

        for sheet_breakdown_field in sheet_breakdown_fields:
            breakdown_file_df[sheet_breakdown_field] = breakdown_file_df[sheet_breakdown_field].fillna('BLANK')

            test = create_worksheet_name(sheet_breakdown_field)

            worksheet = workbook.add_worksheet(create_worksheet_name(sheet_breakdown_field))

            worksheet.hide_gridlines(2)

            worksheet.set_column('A:A', 1)
            worksheet.set_column('B:B', 50)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 145)


            worksheet.insert_image('B1', r'C:\Users\steve.baker\Desktop\MAT Nonsense\picker2.png', {'y_offset': 29, 'x_offset': 10})

            row = 1
            worksheet.write(row, 2, 'New mothers\' experiences of care survey 2020', subtitle_format)
            row = 2
            worksheet.write(row, 2, f'{file_breakdown_value} Free Text Report', subtitle_format)
            row = 3
            worksheet.write(row, 2, f'Broken Down By: {sheet_breakdown_field}', subtitle_format)

            row += 2

            columns = [sheet_breakdown_field]

            text_questions = questions.text_response_questions
            text_question_columns = [i.get_qid() for i in text_questions]
            text_question_formatted = [f'{i.get_qid()} - {i.q_text}' for i in text_questions]

            columns = [sheet_breakdown_field] + text_question_columns

            my_special_df = breakdown_file_df[columns]
            my_special_df_melt = my_special_df.melt(id_vars = sheet_breakdown_field)
            my_special_df_melt = my_special_df_melt.rename({'variable':'Question', 'value':'Response'}, axis=1)
            my_special_df_meltdf5 = my_special_df_melt.dropna(how='any', subset=['Response'])


            ###suppression### Deosnt work, need metric for 'responded'
            if suppression_framework == 'patient':
                grouped = breakdown_file_df[sheet_breakdown_field].value_counts()
                suppress_list = (grouped.index[grouped < suppression_threshold]).tolist()

                my_special_df_meltdf5.loc[my_special_df_meltdf5[sheet_breakdown_field].isin(suppress_list), ['Response']] = '* COMMENT SUPPRESSED *'

            if suppression_framework == 'staff':
                groupeddf = my_special_df_meltdf5.groupby(['Question'] + [sheet_breakdown_field]).count()

                dropcombos = (groupeddf[groupeddf['Response'] < suppression_threshold]).index.tolist()

                rowstochange = []
                for df_row in my_special_df_meltdf5.iterrows():
                    combo = tuple((df_row[1][['Question', sheet_breakdown_field]]).tolist())

                    if combo in dropcombos:
                        rowstochange.append(df_row[0])

                my_special_df_meltdf5.loc[rowstochange, ['Response']] = '* COMMENT SUPPRESSED*'


            q_map_dict = dict(zip(text_question_columns, text_question_formatted))
            my_special_df_meltdf5['Question'] = my_special_df_meltdf5['Question'].map(q_map_dict)



            headers = ['Question'] + [i for i in my_special_df_meltdf5.columns if i != 'Question']

            my_special_df_meltdf5 = my_special_df_meltdf5[headers]

            column = 1
            for header in headers:
                worksheet.write(row, column, header, header_format)
                column += 1

            worksheet.autofilter(row, 1, row, len(headers))

            row += 1

            worksheet.freeze_panes(row, 0)

            for dfrow in my_special_df_meltdf5.iterrows():
                column = 1
                for value in dfrow[1]:
                    worksheet.write(row, column, value, value_format)

                    column += 1
                row+=1

        workbook.close()
