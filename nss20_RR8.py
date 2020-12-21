import survey_platform as sp
import questions as qst
import rag
import sesreport

questions = qst.Questions.from_file(
    r"N:\Feedback\Staff\NHS Staff Survey 2020_PXXXX\Reporting\NSS20 Positive Score Mapping TW AR V1.3.xlsx")

responses = sp.Responses(
    r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20_Picker_Reporting_20201212_V6.parquet",
    indexcol='Sample ID')

responses.df = responses.df[responses.df['OUTCOME'].str[0] == 'C']

# Do benchmarking group remapping for 2020
responses.df.loc[responses.df['Trust Type'] == 'ACO', 'Trust Type'] = 'ACU'
responses.df.loc[responses.df['Trust Type'] == 'MCO', 'Trust Type'] = 'MEN'

data = responses.df[responses.df['Organisation code'] == 'RR8']

#######
# SES by Characteristic
#######

survey_name = f"RR8 Aditional Analysis"
file_name = f"RR8 SES ARN"

sesreport.SesReport(source=data, questions=questions,
                    sheet_breakdown_fields=['LOCALITY1', ['LOCALITY1', 'Q22b'], ['LOCALITY1', 'Disability (Q26a)'],
                                            ['LOCALITY1', 'Q23'], ['LOCALITY1', 'BME (Q23)'], ['LOCALITY1', 'Q22a'],
                                            ['LOCALITY1', 'Q24'], ['LOCALITY1', 'Q25']],
                    suppression_threshold=11,
                    output_path=r'C:\Users\steve.baker\Desktop\NSS\RR8 ARN', survey_name=survey_name,
                    report_name='NHS Staff Survey 2020 - Engagement Report', file_name=file_name,
                    overall_text='Organisation Overall')

#######
# RAG by Loc1/2/3
#######

survey_name = f"RR8 Aditional Analysis"
file_name = f"RR8 RAG ARN 1"

rag.RagReport(source=data, questions=questions,
              sheet_breakdown_fields=[['LOCALITY1', 'LOCALITY2', 'LOCALITY3']],
              suppression_threshold=11,
              output_path=r'C:\Users\steve.baker\Desktop\NSS\RR8 ARN', survey_name=survey_name,
              report_name='NHS Staff Survey 2020 - RAG Report', file_name=file_name,
              overall_text='Organisation Overall')

#######
# RAG multi breakdpwn locality 1/2/4 and 1/2/5 and lcoality 1/Staff Group
#######

survey_name = f"RR8 Aditional Analysis"
file_name = f"RR8 RAG ARN 3"

rag.RagReport(source=data, questions=questions,
              sheet_breakdown_fields=[['LOCALITY1', 'LOCALITY2', 'LOCALITY4'], ['LOCALITY1', 'LOCALITY2', 'LOCALITY5'],
                                      ['LOCALITY1', 'STAFFGROUP']],
              suppression_threshold=11,
              output_path=r'C:\Users\steve.baker\Desktop\NSS\RR8 ARN', survey_name=survey_name,
              report_name='NHS Staff Survey 2020 - RAG Report', file_name=file_name,
              overall_text='Organisation Overall')

#######
# RAG multi breakdpwn locality 1/2/4 and 1/2/5 and lcoality 1/Staff Group
#######


