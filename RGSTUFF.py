from survey_platform import survey_platform as sp

questions = sp.Questions(r"C:\Users\steve.baker\Desktop\RG\questions.xlsx")

responses = sp.Responses(r"C:\Users\steve.baker\Desktop\RG\data.tsv", indexcol='ExternalReference')

#sp.get_frequency_table(source=responses.df, questions=questions, file_breakdown_field='Trust Code', sheet_breakdown_fields=['BME', 'DISABILITY', 'AGE BAND'], suppression_threshold=11)

#sp.get_rag(source=responses.df, questions=questions, group_by='DISABILITY', seperate_by_field='Trust Code', seperator='RQW')

sp.get_freetext(source=responses.df, questions=questions, file_breakdown_field='Trust Code', sheet_breakdown_fields=['BME', 'AGE BAND', 'DISABILITY'], suppression_framework='staff', suppression_threshold=11)