from survey_platform import survey_platform as sp
import timeit
import pendulum

repeats = 1

#survey = None


def create_survey():
    global survey
    survey = sp.Survey('TESTSURVEY', 'SPECIALSURVEY',
                       'C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/questions.csv',
                       'C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/responses.parquet',
                       'C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/sample.parquet')


def create_rags():

    for org in survey.sample.get_orgs():
        sp.get_summary_csv(survey.combined.df, org, 'locality1', survey.questions)


print(timeit.timeit(create_survey, number=repeats)/repeats)
print(timeit.timeit(create_rags, number=repeats)/repeats)
