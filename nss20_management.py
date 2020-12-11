import survey_platform as sp
import questions as qst
import etabs

outcome_map = {'Blank': ['B'],
               'Completed': ['CP1', 'CP2', 'CP3', 'CO1', 'CO2', 'CO3', 'CO4', 'CO5', 'CO6', 'CO7'],
               'Excluded': ['EXCL'],
               'Ineligible': ['INEL'],
               'Left organisation': ['LE'],
               'Not returned': ['N'],
               'No further mailings': ['NFM'],
               'Opted out': ['REF'],
               'Undelivered': ['UN']}

questions = qst.Questions.from_file(
    r"N:\Feedback\Staff\NHS Staff Survey 2020_PXXXX\Reporting\NSS20 Positive Score Mapping TW V1.3 SB _DEV.xlsx")

responses = sp.Responses(
    r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20_Picker_Reporting_20201208_V5.parquet",
    indexcol='Sample ID')

responsesP_1 = sp.Responses(r"C:\Users\steve.baker\Desktop\NSS\Hist\REPORTING_2019_DROPPED.parquet", indexcol='URN')

# Add locality1/site unique codes
responses.df['LOCALITY1'].fillna('BLANK', inplace=True)
responses.df['LOC1CODE'] = responses.df['Organisation code'].str.split('/').str[0] + responses.df['LOCALITY1'].astype(
    'category').cat.codes.apply(lambda x: f'{x:04d}')


#load the current and historic data (a subet or whole thing, to speed things up)
#data = responses.df[responses.df['Organisation code'].isin(['00L', '00N', '00P', 'RXF', 'R1H', 'RF4', '78H', 'RC9'])]
data = responses.df
#dataP_1 = responsesP_1.df[responsesP_1.df['TRUSTID'].isin(['00L', '00N', '00P', 'RXF', 'R1H', 'RF4', '78H', 'RC9'])]
dataP_1 = responsesP_1.df

# # Positive Score Tables
# etabs.positivescoretable(data, questions, breakdown_field='Organisation code', suppression_threshold=10,
#                          filename='PositiveScoreTable_CURRENT', level_prefix='L0')
# etabs.positivescoretable(dataP_1, questions, breakdown_field='TRUSTID', suppression_threshold=10,
#                          filename='PositiveScoreTable_Y-2', level_prefix='L0', period='P-1')
# etabs.positivescoretable(dataP_1, questions, breakdown_field='TRUSTID', suppression_threshold=10,
#                          filename='PositiveScoreTable_Y-3', level_prefix='L0', period='P-1')
# etabs.positivescoretable(dataP_1, questions, breakdown_field='TRUSTID', suppression_threshold=10,
#                          filename='PositiveScoreTable_Y-4', level_prefix='L0', period='P-1')
#
# # SiteScores Current
# etabs.positivescoretable(data, questions, breakdown_field='LOC1CODE', suppression_threshold=10,
#                          filename='SiteScores_CURRENT', level_prefix='L1', l1_name_column='LOCALITY1')
#
# Significance Table
etabs.ez(data, dataP_1, questions, 'Organisation code', 'TRUSTID', level_prefix='L0',
         suppression_threshold=10, filename='SignificanceTable_ALL', benchmark_column='Trust Type')

# # MinMeanMax
# etabs.minmeanmax(data, questions, breakdown_field='Organisation code', type_field='Trust Type',
#                  suppression_threshold=10)
#
# # SiteN
# etabs.site_n(data, questions, 'LOC1CODE', 'Organisation code', l1_name_field='LOCALITY1')
#
# # Response Rate
# etabs.response(data, 'Organisation code', 'Trust Type', 'OUTCOME', level_prefix='L0', filename='RespRates_CURRENT')
# etabs.response(dataP_1, 'TRUSTID', 'TRUSTTYPE', 'OUTCOME', level_prefix='L1', filename='RespRates_HISTORIC')

# Survey Information
# etabs.survey_information(data, 'Organisation code', 'OUTCOME', level_prefix='L0', survey_name='NHS Staff Survey 2020',
#                          current_period='2020', period_minus_1='2019', period_minus_2='2018', period_minus_3='2017',
#                          period_minus_4='2016', name_column='Organisation Name', type_column='Trust Type',
#                          outcome_map=outcome_map)
