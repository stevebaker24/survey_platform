import survey_platform as sp
import questions as qst
import freq_table as ft

questions = qst.Questions.from_file(
    r"N:\Feedback\Staff\NHS Staff Survey 2020_PXXXX\Reporting\NSS20 Positive Score Mapping TW AR V1.3.xlsx")

responses = sp.Responses(
    r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20_Picker_Reporting_20201212_V6.parquet",
    indexcol='Sample ID')

for trust_code in responses.df['Organisation code'].unique():
    trustdf = responses.df[responses.df['Organisation code'] == trust_code]

    trust_name = trustdf['Organisation Name'].iloc[0]

    survey_name = f"{trust_code} - {trust_name}"

    file_name = f"{trust_code}_NSS20_Frequency_Table_Report"

    print(survey_name)

    ft.FrequencyTableReport(source=trustdf, questions=questions,
                            sheet_breakdown_fields=['LOCALITY1', 'LOCALITY2', 'LOCALITY3', 'LOCALITY4', 'LOCALITY5',
                                                    'LOCALITY6', 'LOCALITY7', 'LOCALITY8', 'STAFFGROUP', 'Q22b',
                                                    'Disability (Q26a)', 'Q23', 'BME (Q23)', 'Q22a', 'Q24', 'Q25'],
                            suppression_threshold=11,
                            output_path=r"C:\Users\steve.baker\Desktop\NSS\freq_v4", survey_name=survey_name,
                            report_name='NHS Staff Survey 2020 - Frequency Table Report', file_name=file_name,
                            overall_text='Organisation Overall')
