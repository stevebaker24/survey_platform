import survey_platform as sp
import questions as qst
import etabs
import numpy as np
import pandas as pd

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
    r"N:\Feedback\Staff\NHS Staff Survey 2020_PXXXX\Reporting\NSS20 Positive Score Mapping TW AR V1.3.xlsx")

responses = sp.Responses(
    r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20_Picker_Reporting_20201212_V6.parquet",
    indexcol='Sample ID')

historicdata = sp.Responses(r"C:\Users\steve.baker\PycharmProjects\python-scripts\NSS20HISTORICV2.parquet",
                            indexcol='URN')


data = responses.df

####MAP NCA TRUST CODE
data.loc[data['Organisation code'].isin(['RM3', 'RW6']), 'Organisation code'] = 'NCA'
data.loc[data['Organisation code'] == 'NCA', 'Organisation Name'] = 'Northern Care Alliance'

historicdata.df.loc[historicdata.df['TRUSTID'].isin(['RM3', 'RW6']), 'TRUSTID'] = 'NCA'


###########
# Do benchmarking group remapping for 2020

data.loc[data['Trust Type'] == 'ACO', 'Trust Type'] = 'ACU'
data.loc[data['Trust Type'] == 'MCO', 'Trust Type'] = 'MEN'



# Add Trust type names:

trust_type_name_map = {
    "ACU": "Acute and Acute & Community Trusts",
    'AMB': "Ambulance Trust",
    'ASP': "Acute Specialist Trust",
    'CCG': "Clinical Commissioning Group",
    'COM': "Community Trust",
    'MEN': "Mental Health & Learning Disability and Mental Health#COMMA# Learning Disability & Community Trusts",
    'OTH': "Other Organisation Type"
}

data['Trust Type Name'] = data['Trust Type'].map(trust_type_name_map)

############
# Add locality1/site unique codes

data['LOCALITY1'].fillna('BLANK', inplace=True)

dfs = []

for trust in data['Organisation code'].unique():
    trustdf = data[data['Organisation code'] == trust]
    trustdf['TEMP'] = trustdf['LOCALITY1'].copy()
    trustdf = trustdf[['Sample ID', 'TEMP']]
    trustdf['LOC1CODE'] = (trustdf['TEMP'].astype('category').cat.codes) + 1

    # proabbly not needed but just tryiong to match outputs
    dfs.append(trustdf[['Sample ID', 'LOC1CODE']])

totaldf = pd.concat(dfs)

data = data.merge(totaldf, how='left', left_on='Sample ID', right_on='Sample ID', suffixes=(None, '_r'))

data['LOC1ID'] = data['Organisation code'].str.split('/').str[0] + 'ID' + data['LOC1CODE'].apply(lambda x: f'{x:05d}')

# ###########

# dataP_1 = historicdata.df[historicdata.df['YEAR'] == '2019']
# dataP_2 = historicdata.df[historicdata.df['YEAR'] == '2018']
# dataP_3 = historicdata.df[historicdata.df['YEAR'] == '2017']
# dataP_4 = historicdata.df[historicdata.df['YEAR'] == '2016']
#
# # Positive Score Tables
# etabs.positivescoretable(data, questions, breakdown_field='Organisation code', suppression_threshold=11,
#                           filename='PositiveScoreTable_CURRENT', level_prefix='L0')
# etabs.positivescoretable(dataP_2, questions, breakdown_field='TRUSTID', suppression_threshold=11,
#                          filename='PositiveScoreTable_Y-2', level_prefix='L0', period='P-1')
# etabs.positivescoretable(dataP_3, questions, breakdown_field='TRUSTID', suppression_threshold=11,
#                          filename='PositiveScoreTable_Y-3', level_prefix='L0', period='P-1')
# etabs.positivescoretable(dataP_4, questions, breakdown_field='TRUSTID', suppression_threshold=11,
#                          filename='PositiveScoreTable_Y-4', level_prefix='L0', period='P-1')
#
# # SiteScores Current
# etabs.positivescoretable(data, questions, breakdown_field='LOC1ID', suppression_threshold=11,
#                          filename='SiteScores_CURRENT', level_prefix='L1', l1_name_column='LOCALITY1')
#
# # Significance Table
# etabs.ez(data, dataP_1, questions, 'Organisation code', 'TRUSTID', level_prefix='L0',
#          suppression_threshold=11, filename='SignificanceTable_ALL', benchmark_column='Trust Type')
#
# # MinMeanMax
# #COLUMN HEADERS NEED MANUALLY PATCHING TO MATCH EXISTING FORMAT, NO TIME TO CHANGE CODE
# etabs.minmeanmax(data, questions, breakdown_field='Organisation code', type_field='Trust Type',
#                  suppression_threshold=11)
#
#
# # SiteN
# etabs.site_n(data, questions, 'LOC1ID', 'Organisation code', l1_name_field='LOCALITY1')
#
# # Response Rate
# etabs.response(data, 'Organisation code', 'Trust Type', 'OUTCOME', level_prefix='L0', filename='RespRates_CURRENT')
# etabs.response(dataP_1, 'TRUSTID', 'TRUSTTYPE', 'OUTCOME', level_prefix='L0', filename='RespRates_HISTORIC')

#Survey Information
etabs.survey_information(data, 'Organisation code', 'OUTCOME', level_prefix='L0', survey_name='NHS Staff Survey',
                         current_period='2020', period_minus_1='2019', period_minus_2='2018', period_minus_3='2017',
                         period_minus_4='2016', name_column='Organisation Name', type_column='Trust Type',
                         type_name_column='Trust Type Name', outcome_map=outcome_map)
