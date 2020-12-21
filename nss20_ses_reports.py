import survey_platform as sp
import questions as qst
import sesreport

questions = qst.Questions.from_file(
    r"N:\Feedback\Staff\NHS Staff Survey 2020_PXXXX\Reporting\NSS20 Positive Score Mapping TW AR V1.3.xlsx")

responses = sp.Responses(
    r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20_Picker_Reporting_20201212_V6.parquet",
    indexcol='Sample ID')

responses.df = responses.df[responses.df['OUTCOME'].str[0] == 'C']

sesmap = {5: 10, 4: 7.5, 3: 5, 2: 2.5, 1: 0}

###
# External Benchmarking/Picker Average

# Do benchmarking group remapping for 2020
responses.df.loc[responses.df['Trust Type'] == 'ACO', 'Trust Type'] = 'ACU'
responses.df.loc[responses.df['Trust Type'] == 'MCO', 'Trust Type'] = 'MEN'

for org_type in responses.df['Trust Type'].unique():

    org_df = responses.df[responses.df['Trust Type'] == org_type]

    ses_questions_dict = {'Advocacy': ['Q18c', 'Q18d', 'Q18a'], 'Involvement': ['Q4b', 'Q4a', 'Q4d'],
                          'Motivation': ['Q2a', 'Q2b', 'Q2c']}
    ses_questions = sesreport.ses_get_question_fields(ses_questions_dict)

    # dataprep:
    comparator = org_df[['Organisation code'] + ses_questions]
    #number of people who gave at least one answer for the ses questions
    comparator_n = len(comparator)

    comparator = sesreport.ses_map_data(comparator, ses_questions, sesmap)
    comparator = sesreport.create_total_ses_df(comparator, ['Organisation code'], ses_questions_dict, 11)
    comparator = comparator.mean(axis=1)

    for trust_code in org_df['Organisation code'].unique():
        trustdf = org_df[org_df['Organisation code'] == trust_code]

        trust_name = trustdf['Organisation Name'].iloc[0]

        survey_name = f"{trust_code} - {trust_name}"
        # Trim down to x characters
        if (len(survey_name)) > 45:
            survey_name = survey_name[:45] + "(...)"

        file_name = f"{trust_code}_NSS20_Engagement_Report_External_Benchmark"

        comparator_text = f"Picker Average"

        print(survey_name)

        sesreport.SesReport(source=trustdf, questions=questions,
                            sheet_breakdown_fields=['LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4', 'LOCALITY5',
                                                    'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                                    'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                            suppression_threshold=11,
                            output_path=r'C:\Users\steve.baker\Desktop\NSS\ses_draftV3', survey_name=survey_name,
                            report_name='NHS Staff Survey 2020 - Engagement Report (External)', file_name=file_name,
                            overall_text='Organisation Overall', external_comparator=comparator,
                            external_comparator_n=comparator_n, comparator_text=comparator_text)

###########

# Historical Benchmarking

##########
historicdata = sp.Responses(r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20HISTORICV2.parquet",
                            indexcol='URN')
historicdata.df = historicdata.df[historicdata.df['OUTCOME'].str[0] == 'C']

dataP_1 = historicdata.df[historicdata.df['YEAR'] == '2019']

del(historicdata)

for trust_code in responses.df['Organisation code'].unique():
    trustdf = responses.df[responses.df['Organisation code'] == trust_code]
    trust_name = trustdf['Organisation Name'].iloc[0]

    if trust_code not in dataP_1['TRUSTID'].unique():
        print(F"{trust_code} - no hist data")
        continue

    #Different to 2020...
    ses_questions_dict = {'Advocacy': ['Q21c', 'Q21d', 'Q21a'], 'Involvement': ['Q4b', 'Q4a', 'Q4d'],
                          'Motivation': ['Q2a', 'Q2b', 'Q2c']}

    trust_hist_df = dataP_1[dataP_1["TRUSTID"] == trust_code]

    ses_questions = sesreport.ses_get_question_fields(ses_questions_dict)

    # dataprep:
    comparator = trust_hist_df[['TRUSTID'] + ses_questions]
    #number of people who gave at least one answer for the ses questions
    comparator_n = len(comparator)

    comparator = sesreport.ses_map_data(comparator, ses_questions, sesmap)
    comparator = sesreport.create_total_ses_df(comparator, None, ses_questions_dict, 11)
    comparator = comparator.mean(axis=1)

    survey_name = f"{trust_code} - {trust_name}"
    # Trim down to x characters
    if (len(survey_name)) > 45:
        survey_name = survey_name[:45] + "(...)"

    file_name = f"{trust_code}_NSS20_Engagement_Report_Historic_Benchmark"

    comparator_text = f"Organisation Overall - 2019"

    print(survey_name)

    sesreport.SesReport(source=trustdf, questions=questions,
                        sheet_breakdown_fields=['LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4', 'LOCALITY5',
                                                'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                                'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                        suppression_threshold=11,
                        output_path=r'C:\Users\steve.baker\Desktop\NSS\ses_draftV3', survey_name=survey_name,
                        report_name='NHS Staff Survey 2020 - Engagement Report (Historic)', file_name=file_name,
                        overall_text='Organisation Overall - 2020', external_comparator=comparator,
                        external_comparator_n=comparator_n, comparator_text=comparator_text)

###########

# Internal Benchmarking

##########

for trust_code in responses.df['Organisation code'].unique():
    trustdf = responses.df[responses.df['Organisation code'] == trust_code]
    trust_name = trustdf['Organisation Name'].iloc[0]

    survey_name = f"{trust_code} - {trust_name}"
    # Trim down to x characters
    if (len(survey_name)) > 45:
        survey_name = survey_name[:45] + "(...)"

    file_name = f"{trust_code}_NSS20_Engagement_Report_Internal_Benchmark"

    print(survey_name)

    sesreport.SesReport(source=trustdf, questions=questions,
                        sheet_breakdown_fields=['LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4', 'LOCALITY5',
                                                'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                                'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                        suppression_threshold=11,
                        output_path=r'C:\Users\steve.baker\Desktop\NSS\ses_draftV3', survey_name=survey_name,
                        report_name='NHS Staff Survey 2020 - Engagement Report (Internal)', file_name=file_name,
                        overall_text='Organisation Overall')
