from survey_platform import survey_platform as sp
import timeit

repeats = 1

survey = None


def create_survey():
    global survey
    survey = sp.Survey('TESTSURVEY',
                       'SPECIALSURVEY',
                       'C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/questions.csv',
                       'C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/responses.parquet',
                       'C:/Users/steve.baker/PycharmProjects/survey_app/survey_app/static/sample.parquet')


# sp.get_heatmap(survey.reporting, ['Q2', 'Q3', 'Q4'])
def create_rags():
    for org in survey.sample.get_orgs():
        sp.get_rag(survey, seperator=org, group_by=['locality1'], questions=survey.questions)
        break


def create_freq():
    for org in survey.sample.get_orgs():
        sp.get_freq_tables(org, survey.combined.df, survey.questions)
        break


def create_freetext():
    for org in survey.sample.get_orgs():
        sp.get_freetext(org, survey.combined.df, survey.questions)
        break


print(timeit.timeit(create_survey, number=repeats)/repeats)
print(timeit.timeit(create_rags, number=repeats)/repeats)
print(timeit.timeit(create_freq, number=repeats)/repeats)
print(timeit.timeit(create_freetext, number=repeats)/repeats)
