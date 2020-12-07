import survey_platform as sp
import questions as qst
import freq_table as ft


questions = qst.Questions.from_file(
    r"N:\Feedback\Staff\NHS Staff Survey 2020_PXXXX\Reporting\NSS20 Positive Score Mapping TW V1.2.xlsx")

responses = sp.Responses(
    r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20_Picker_Reporting_20201204_V3.csv", indexcol='Sample ID')

for trust in responses.df['Organisation code'].unique():

    print(trust)
    trustdf = responses.df[responses.df['Organisation code'] == trust]

    ft.FrequencyTableReport(source=trustdf, questions=questions,
                            sheet_breakdown_fields=[None, 'LOCALITY1', ['LOCALITY1', 'LOCALITY2'], ['LOCALITY2', 'LOCALITY1']], suppression_threshold=10,
                            output_path=r'C:\Users\steve.baker\Desktop\Picker Survey', survey_name=trust)
