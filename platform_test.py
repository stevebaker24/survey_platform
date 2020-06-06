from survey_platform import survey_platform as sp

survey = sp.Survey('TESTSURVEY', 'SPECIALSURVEY',
                   'C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/questions.csv',
                   'C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/responses.parquet',
                   'C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/sample.parquet')

for org in survey.combined.get_orgs():
    survey.combined.get_summary(org, 'locality1')

test='test'