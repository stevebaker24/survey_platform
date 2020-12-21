import survey_platform as sp
import questions as qst
import rag

questions = qst.Questions.from_file(
    r"N:\Feedback\Staff\NHS Staff Survey 2020_PXXXX\Reporting\NSS20 Positive Score Mapping TW AR V1.3.xlsx")

responses = sp.Responses(
    r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20_Picker_Reporting_20201212_V6.parquet",
    indexcol='Sample ID')

responses.df = responses.df[responses.df['OUTCOME'].str[0] == 'C']

# import histroic data
historicdata = sp.Responses(r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20HISTORICV2.parquet",
                            indexcol='URN')
historicdata.df = historicdata.df[historicdata.df['OUTCOME'].str[0] == 'C']
dataP_1 = historicdata.df[historicdata.df['YEAR'] == '2019']
del (historicdata)

###########

# Historical Benchmarking

##########

for trust_code in responses.df['Organisation code'].unique():
    trustdf = responses.df[responses.df['Organisation code'] == trust_code]
    trust_name = trustdf['Organisation Name'].iloc[0]

    if trust_code not in dataP_1['TRUSTID'].unique():
        print(F"{trust_code} - no hist data")
        continue

    trust_hist_df = dataP_1[dataP_1["TRUSTID"] == trust_code]

    comparator_n = len(trust_hist_df)

    questions_list = questions.get_period_questions('P-1')

    source_columns = [question.question_columns for question in questions_list if question.scored]
    source_columns = [item for sublist in source_columns for item in sublist]

    scored_df = sp.calc_scores(trust_hist_df[source_columns], questions_list, score_types=['pos'])

    scored_count = scored_df.count().transpose()
    scored_df = scored_df.mean().transpose()

    scored_df = scored_df.mask(scored_count < 11)

    scored_df.index = scored_df.index.str[:-4]

    current_scored_qs = [q.qid for q in questions.scored_questions]
    comparator = scored_df.reindex(current_scored_qs)
    comparator = comparator/100
    comparator = comparator.fillna('*')


    survey_name = f"{trust_code} - {trust_name}"
    # Trim down to x characters
    if (len(survey_name)) > 45:
        survey_name = survey_name[:45] + "(...)"

    file_name = f"{trust_code}_NSS20_RAG_Report_Historic_Benchmark"

    comparator_text = f"Organisation Overall - 2019"

    print(survey_name)

    rag.RagReport(source=trustdf, questions=questions,
                  sheet_breakdown_fields=['LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4', 'LOCALITY5',
                                          'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                          'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                  suppression_threshold=11,
                  output_path=r'C:\Users\steve.baker\Desktop\NSS\rag_draftV2', survey_name=survey_name,
                  report_name='NHS Staff Survey 2020 - RAG Report (Historic)', file_name=file_name,
                  overall_text='Organisation Overall - 2020', external_comparator=comparator,
                  external_comparator_n=comparator_n, comparator_text=comparator_text)

#######

# Internal benchmarking

#######
###
for trust_code in responses.df['Organisation code'].unique():
    trustdf = responses.df[responses.df['Organisation code'] == trust_code]

    trust_name = trustdf['Organisation Name'].iloc[0]

    survey_name = f"{trust_code} - {trust_name}"
    # Trim down to x characters
    if (len(survey_name)) > 45:
        survey_name = survey_name[:45] + "(...)"

    file_name = f"{trust_code}_NSS20_RAG_Table_Report_Internal_Benchmark"

    print(survey_name)

    rag.RagReport(source=trustdf, questions=questions,
                  sheet_breakdown_fields=['LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4', 'LOCALITY5',
                                          'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                          'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                  suppression_threshold=11,
                  output_path=r'C:\Users\steve.baker\Desktop\NSS\rag_draftv2', survey_name=survey_name,
                  report_name='NHS Staff Survey 2020 - RAG Report (Internal)', file_name=file_name,
                  overall_text='Organisation Overall')



#######

# External benchmarking

#######


# Do benchmarking group remapping for 2020
responses.df.loc[responses.df['Trust Type'] == 'ACO', 'Trust Type'] = 'ACU'
responses.df.loc[responses.df['Trust Type'] == 'MCO', 'Trust Type'] = 'MEN'

for org_type in responses.df['Trust Type'].unique():

    org_df = responses.df[responses.df['Trust Type'] == org_type]

    comparator_n = len(org_df)

    source_columns = [question.question_columns for question in questions if question.scored]
    source_columns = [item for sublist in source_columns for item in sublist]

    scored_df = sp.calc_scores(org_df[['Organisation code'] + source_columns], questions, score_types=['pos'])

    mean_df = scored_df.groupby('Organisation code').mean().transpose()
    count_df = scored_df.groupby('Organisation code').count().transpose()

    mean_df = mean_df.mask(count_df < 11)

    mean_df.index = mean_df.index.str[:-4]
    mean_df = mean_df.mean(axis=1)
    comparator = mean_df/100

    comparator = comparator.fillna('*')

    for trust_code in org_df['Organisation code'].unique():
        trustdf = org_df[org_df['Organisation code'] == trust_code]

        trust_name = trustdf['Organisation Name'].iloc[0]

        survey_name = f"{trust_code} - {trust_name}"
        # Trim down to x characters
        if (len(survey_name)) > 45:
            survey_name = survey_name[:45] + "(...)"

        file_name = f"{trust_code}_NSS20_RAG_Table_Report_External_Benchmark"

        comparator_text = f"Picker Average"

        print(survey_name)

        rag.RagReport(source=trustdf, questions=questions,
                      sheet_breakdown_fields=['LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4', 'LOCALITY5',
                                              'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                              'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                      suppression_threshold=11,
                      output_path=r'C:\Users\steve.baker\Desktop\NSS\rag_draftv2', survey_name=survey_name,
                      report_name='NHS Staff Survey 2020 - RAG Report (External)', file_name=file_name,
                      overall_text='Organisation Overall', external_comparator=comparator,
                  external_comparator_n=comparator_n, comparator_text=comparator_text)