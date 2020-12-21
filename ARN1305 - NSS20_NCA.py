import survey_platform as sp
import questions as qst
import rag
import sesreport
import freq_table as ft

questions = qst.Questions.from_file(
    r"N:\Feedback\Staff\NHS Staff Survey 2020_PXXXX\Reporting\NSS20 Positive Score Mapping TW AR V1.3.xlsx")

responses = sp.Responses(
    r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20_Picker_Reporting_20201212_V6.parquet",
    indexcol='Sample ID')

responses.df = responses.df[responses.df['OUTCOME'].str[0] == 'C']

responses.df['LOCALITY0'] = responses.df['Organisation code']

responses.df.loc[responses.df['Organisation code'].isin(['RM3', 'RW6']), 'Organisation code'] = 'NCA'

responses.df.loc[responses.df['Trust Type'] == 'ACO', 'Trust Type'] = 'ACU'
responses.df.loc[responses.df['Trust Type'] == 'MCO', 'Trust Type'] = 'MEN'

trustdf = responses.df[responses.df['Organisation code'] == 'NCA']


### HISTORIC DATA
historicdata = sp.Responses(r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20HISTORICV2.parquet",
                            indexcol='URN')
historicdata.df = historicdata.df[historicdata.df['OUTCOME'].str[0] == 'C']

historicdata.df['LOCALITY0'] = historicdata.df['TRUSTID']
historicdata.df.loc[historicdata.df['TRUSTID'].isin(['RM3', 'RW6']), 'TRUSTID'] = 'NCA'

dataP_1 = historicdata.df[historicdata.df['YEAR'] == '2019']

del(historicdata)


### General Info

survey_name = f"NCA - Northern Care Alliance (RM3/RW6)"

#######

# Internal benchmarking RAG

#######

file_name = f"NCA_NSS20_RAG_Table_Report_Internal_Benchmark"

rag.RagReport(source=trustdf, questions=questions,
              sheet_breakdown_fields=['LOCALITY0', 'LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4', 'LOCALITY5',
                                      'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                      'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
              suppression_threshold=11,
              output_path=r'C:\Users\steve.baker\Desktop\NSS', survey_name=survey_name,
              report_name='NHS Staff Survey 2020 - RAG Report (Internal)', file_name=file_name,
              overall_text='Organisation Overall')

#######

# External benchmarking RAG

#######

org_df = responses.df[responses.df['Trust Type'] == 'ACU']

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

file_name = f"NCA_NSS20_RAG_Table_Report_External_Benchmark"
comparator_text = f"Picker Average"

rag.RagReport(source=trustdf, questions=questions,
              sheet_breakdown_fields=['LOCALITY0', 'LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4', 'LOCALITY5',
                                      'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                      'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
              suppression_threshold=11,
              output_path=r'C:\Users\steve.baker\Desktop\NSS', survey_name=survey_name,
              report_name='NHS Staff Survey 2020 - RAG Report (External)', file_name=file_name,
              overall_text='Organisation Overall', external_comparator=comparator,
                  external_comparator_n=comparator_n, comparator_text=comparator_text)


#######

# Historical benchmarking RAG

#######

trust_hist_df = dataP_1[dataP_1["TRUSTID"] == 'NCA']
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


file_name = f"NCA_NSS20_RAG_Report_Historic_Benchmark"
comparator_text = f"Organisation Overall - 2019"

rag.RagReport(source=trustdf, questions=questions,
              sheet_breakdown_fields=['LOCALITY0', 'LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4', 'LOCALITY5',
                                      'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                      'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
              suppression_threshold=11,
              output_path=r'C:\Users\steve.baker\Desktop\NSS', survey_name=survey_name,
              report_name='NHS Staff Survey 2020 - RAG Report (Historic)', file_name=file_name,
              overall_text='Organisation Overall (2020)', external_comparator=comparator,
                  external_comparator_n=comparator_n, comparator_text=comparator_text)



#######

# Internal benchmarking SES

#######

file_name = f"NCA_NSS20_Engagement_Report_Internal_Benchmark"

sesreport.SesReport(source=trustdf, questions=questions,
                    sheet_breakdown_fields=['LOCALITY0', 'LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4',
                                            'LOCALITY5',
                                            'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                            'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                    suppression_threshold=11,
                    output_path=r'C:\Users\steve.baker\Desktop\NSS', survey_name=survey_name,
                    report_name='NHS Staff Survey 2020 - Engagement Report (Internal)', file_name=file_name,
                    overall_text='Organisation Overall')

#######

# External benchmarking SES

#######

org_type_df = responses.df[responses.df['Trust Type'] == 'ACU']

sesmap = {5: 10, 4: 7.5, 3: 5, 2: 2.5, 1: 0}
ses_questions_dict = {'Advocacy': ['Q18c', 'Q18d', 'Q18a'], 'Involvement': ['Q4b', 'Q4a', 'Q4d'],
                      'Motivation': ['Q2a', 'Q2b', 'Q2c']}
ses_questions = sesreport.ses_get_question_fields(ses_questions_dict)

# dataprep:
comparator = org_type_df[['Organisation code'] + ses_questions]
# number of people who gave at least one answer for the ses questions
comparator_n = len(comparator)

comparator = sesreport.ses_map_data(comparator, ses_questions, sesmap)
comparator = sesreport.create_total_ses_df(comparator, ['Organisation code'], ses_questions_dict, 11)
comparator = comparator.mean(axis=1)

file_name = f"NCA_NSS20_Engagement_Report_External_Benchmark"
comparator_text = f"Picker Average"

sesreport.SesReport(source=trustdf, questions=questions,
                    sheet_breakdown_fields=['LOCALITY0', 'LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4',
                                            'LOCALITY5',
                                            'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                            'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                    suppression_threshold=11,
                    output_path=r'C:\Users\steve.baker\Desktop\NSS', survey_name=survey_name,
                    report_name='NHS Staff Survey 2020 - Engagement Report (External)', file_name=file_name,
                    overall_text='Organisation Overall', external_comparator=comparator,
                    external_comparator_n=comparator_n, comparator_text=comparator_text)

#######

# Historic benchmarking SES

#######

#Different to 2020 so redefine
ses_questions_dict = {'Advocacy': ['Q21c', 'Q21d', 'Q21a'], 'Involvement': ['Q4b', 'Q4a', 'Q4d'],
                      'Motivation': ['Q2a', 'Q2b', 'Q2c']}
ses_questions = sesreport.ses_get_question_fields(ses_questions_dict)

trust_hist_df = dataP_1[dataP_1["TRUSTID"] == 'NCA']

# dataprep:
comparator = trust_hist_df[['TRUSTID'] + ses_questions]
#number of people who gave at least one answer for the ses questions
comparator_n = len(comparator)

comparator = sesreport.ses_map_data(comparator, ses_questions, sesmap)
comparator = sesreport.create_total_ses_df(comparator, None, ses_questions_dict, 11)
comparator = comparator.mean(axis=1)

file_name = f"NCA_NSS20_Engagement_Report_Historic_Benchmark"
comparator_text = f"Organisation Overall - 2019"

sesreport.SesReport(source=trustdf, questions=questions,
                    sheet_breakdown_fields=['LOCALITY0', 'LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4',
                                            'LOCALITY5',
                                            'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                            'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                    suppression_threshold=11,
                    output_path=r'C:\Users\steve.baker\Desktop\NSS', survey_name=survey_name,
                    report_name='NHS Staff Survey 2020 - Engagement Report (Historic)', file_name=file_name,
                    overall_text='Organisation Overall (2020)', external_comparator=comparator,
                    external_comparator_n=comparator_n, comparator_text=comparator_text)



#####
#Frequency Tables
#####


survey_name = "NCA_NSS20_Frequency Tables"

file_name = f"NCA_NSS20_Frequency_Table_Report"


ft.FrequencyTableReport(source=trustdf, questions=questions,
                        sheet_breakdown_fields=['LOCALITY0', 'LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4',
                                        'LOCALITY5',
                                        'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                        'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                        suppression_threshold=11,
                        output_path=r"C:\Users\steve.baker\Desktop\NSS", survey_name=survey_name,
                        report_name='NHS Staff Survey 2020 - Frequency Table Report', file_name=file_name,
                        overall_text='Organisation Overall')