import survey_platform as sp
import questions as qst
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

#######

# Internal benchmarking

#######
###

survey_name = f"NSS20 INSIGHT TEAM"
file_name = f"NSS20 INSIGHT TEAM SES"

sesreport.SesReport(source=responses.df, questions=questions,
              sheet_breakdown_fields=[['Trust Type', 'Organisation code'], 'Trust Type', 'ResponseMode', 'STAFFGROUP', 'Q22b',
                                      'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
              suppression_threshold=11,
              output_path=r'C:\Users\steve.baker\Desktop\NSS\insight', survey_name=survey_name,
              report_name='NHS Staff Survey 2020 - Insight SES', file_name=file_name,
              overall_text='Overall')