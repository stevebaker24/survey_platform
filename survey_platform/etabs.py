import os

import numpy as np
import pandas as pd

import survey_platform as sp
import config

import math


def get_mean_df(scored_df, comparator):
    mean_df = scored_df.groupby(comparator) \
        .mean() \
        .transpose()
    return mean_df


def get_score_df(source, questions, breakdown_field, score_types, period='P'):
    if period != 'P':
        questions = questions.get_period_questions(period)
    else:
        questions = questions.scored_questions

    source_columns = [question.question_columns for question in questions if question.scored]

    # flatten the column list
    source_columns = [item for sublist in source_columns for item in sublist]

    # get scores
    scored_df = sp.calc_scores(source[[breakdown_field] + source_columns], questions, score_types=score_types)

    return scored_df


def positivescoretable(source, questions, breakdown_field, suppression_threshold, period='P', filename='posscoretable',
                       level_prefix=None, l1_name_column=None):
    scored_df = get_score_df(source, questions, breakdown_field, ['pos', 'neu', 'neg'], period=period)
    mean_df = get_mean_df(scored_df, breakdown_field)

    count_df = scored_df.rename(columns=lambda x: x + '.N' if x != breakdown_field else x) \
        .groupby(breakdown_field) \
        .count() \
        .transpose()

    # apply suppression mask to mean df
    mask = (count_df < suppression_threshold)
    mask.index = mask.index.str.strip('.N')
    mean_df = mean_df.mask(mask)

    # calculate the overall scores as dfs
    overall_dfs = []
    for suffix in config.score_suffixes:
        overall_dfs.append(mean_df[mean_df.index.str.contains(suffix)].mean().rename(f'Overall{suffix}'))

    # append all the different dfs
    output_df = mean_df.append(count_df)

    for overall_df in overall_dfs:
        output_df = output_df.append(overall_df)

    # name the index column
    output_df.index.name = 'Question'

    #handle unasked vs suppressed questions. unasked defined by either the while row being blank or,
    # if a question from P is not present in this period. this is added in this case.
    if period != 'P':
        p_questions = [i.qid for i in questions.scored_questions]
        current_historic_questions = output_df.index.str.split('_').str[0].unique()

        questions_not_in_current_historic = [i for i in p_questions if i not in current_historic_questions]

        missing = []
        for question in questions_not_in_current_historic:
            for score in ['pos', 'neu', 'neg']:
                output_df.loc[f"{question}_{score}"] = np.nan

        #find completely empty rows and populate with '-'
        output_df.loc[output_df[output_df.columns].count(axis=1) == 0, output_df.columns] = '-'



    # if site names needed, add the site name row at the bottom.
    # column headers need to be 'generalised'
    if level_prefix == 'L1':
        ids = output_df.columns
        id_dict = {x: source[source[breakdown_field] == x][l1_name_column].unique()[0] for x in output_df.columns}
        names = ids.map(id_dict)

        names_dict = dict(zip(ids, names))
        series = (pd.Series(names_dict)).rename('SiteName')
        output_df = output_df.append(series)
        output_df.index.name = 'CASE_LBL'

    # apply label prefix:
    if level_prefix is not None:
        output_df.columns = (level_prefix) + (output_df.columns.str.replace("/", "_"))

    output_df.index = output_df.index.str.replace('_pos.N', '_NPos')

    output_df.fillna('*', inplace=True)

    # if l0 save csv if l1 save excel dont know why but NSS20 needs this, rob cannot fix
    if level_prefix == 'L0':
        output_df.to_csv(rf'C:\Users\steve.baker\Desktop\NSS\{filename}.csv')
    elif level_prefix == 'L1':
        output_df.to_excel(rf'C:\Users\steve.baker\Desktop\NSS\{filename}.xlsx', sheet_name=filename)


def minmeanmax(source, questions, breakdown_field, type_field, suppression_threshold=0):
    scored_df = get_score_df(source, questions, breakdown_field, ['pos'])
    mean_df = get_mean_df(scored_df, breakdown_field)

    # suppression...
    count_df = scored_df \
        .groupby(breakdown_field) \
        .count() \
        .transpose()

    # apply suppression mask to mean df
    mask = (count_df < suppression_threshold)
    mean_df = mean_df.mask(mask)

    type_dict = {x: source[source[breakdown_field] == x][type_field].unique()[0] for x in mean_df.columns}
    mean_df.rename(columns=type_dict, inplace=True)

    table_dict = {'MIN (Current)': None,
                  'MEAN (Current)': None,
                  'MAX (Current)': None
                  }

    for breakdown in table_dict:
        aggregate_function = breakdown.split('(')[0].lower()
        df = (eval(f'mean_df.groupby(mean_df.columns, axis=1).{aggregate_function}()'))
        # df = (eval(f'mean_df.{aggregate_function}(axis=1)')).rename('Mean')
        df.index = df.index.str.replace('_pos', f'_{aggregate_function}')
        df.fillna('*', inplace=True)
        table_dict[breakdown] = df

    # write all dfs to excell
    writer = pd.ExcelWriter(rf'C:\Users\steve.baker\Desktop\NSS\MinMeanMax_CURRENT.xlsx',
                            engine='xlsxwriter')

    worksheet = writer.book.add_worksheet('MinMeanMax')
    writer.sheets['MinMeanMax'] = worksheet

    row = 0
    for table in table_dict:
        title = f'TABLE: {table}'
        worksheet.write(row, 0, title)
        table_dict[table].to_excel(writer, sheet_name='MinMeanMax', startcol=0, startrow=row + 2)
        row = row + len(table_dict[table]) + 4

    writer.save()

    dfcsv = pd.read_excel(rf'C:\Users\steve.baker\Desktop\NSS\MinMeanMax_CURRENT.xlsx',
                          sheet_name='MinMeanMax', header=None)
    dfcsv.to_csv((rf'C:\Users\steve.baker\Desktop\NSS\MinMeanMax_CURRENT.csv'), index=0, header=0)
    os.remove(rf'C:\Users\steve.baker\Desktop\NSS\MinMeanMax_CURRENT.xlsx')


# add picker average to ez

def ez(source, other_source, questions, source_breakdown_field, other_source_breakdown_field, benchmark_column,
       level_prefix=None, suppression_threshold=0, filename='ez'):
    # drop values in other_source_comparator not in source_comparator (i.e. trusts no longer in survey):
    source_comparator_values = source[source_breakdown_field].unique().tolist()
    other_source_indexes_to_remove = other_source[
        ~other_source[other_source_breakdown_field].isin(source_comparator_values)].index
    other_source = other_source.drop(other_source_indexes_to_remove)

    # score dfs
    scored_df = get_score_df(source, questions, source_breakdown_field, ['pos'])
    scored_df_other = get_score_df(other_source, questions, other_source_breakdown_field, ['pos'], period='P-1')

    # calcuate mean dfs
    mean_df = get_mean_df(scored_df, source_breakdown_field)
    mean_df_other = get_mean_df(scored_df_other, other_source_breakdown_field)

    # suppress mean dfs
    count_df = scored_df \
        .groupby(source_breakdown_field) \
        .count() \
        .transpose()

    count_df_other = scored_df_other \
        .groupby(other_source_breakdown_field) \
        .count() \
        .transpose()

    # apply suppression mask to mean df
    mask = (count_df < suppression_threshold)
    mean_df = mean_df.mask(mask)

    mask_other = (count_df_other < suppression_threshold)
    mean_df_other = mean_df_other.mask(mask_other)

    # start to calcualte the picker avergae(benchmark)

    name_dict = {x: source[source[source_breakdown_field] == x][benchmark_column].unique()[0] for x in count_df.columns}

    benchmark = mean_df.transpose()
    benchmark['type'] = benchmark.index.map(name_dict)
    benchmark_mean_df = benchmark.groupby('type').mean()

    # using the masked count so that the number going into the picker average are correct. I think this is right...
    benchmark = count_df.mask(mask).transpose()
    benchmark['type'] = benchmark.index.map(name_dict)
    benchmark_count_df = benchmark.groupby('type').sum()

    benchmark_prep_df = mean_df.transpose()
    columns_to_drop = benchmark_prep_df.columns
    benchmark_prep_df['type'] = benchmark.index.map(name_dict)
    benchmark_prep_df = benchmark_prep_df.drop(columns=columns_to_drop)

    mean_df_picker_average = pd.merge(benchmark_prep_df, benchmark_mean_df, left_on='type', right_index=True) \
        .drop(columns=('type')) \
        .transpose()

    count_df_picker_average = pd.merge(benchmark_prep_df, benchmark_count_df, left_on='type', right_index=True) \
        .drop(columns=('type')) \
        .transpose()

    #####
    # picker_average_masked_sum = count_df_masked.sum(axis=1)
    # picker_average_mask = picker_average_masked_sum < suppression_threshold
    #
    # mean_df_picker_average = mean_df.mean(axis=1)
    # mean_df_picker_average = mean_df_picker_average.mask(picker_average_mask)

    # rename question vars for output
    mean_df_other_output = mean_df_other.copy()
    mean_df_other_output.index = mean_df_other_output.index.str.replace('_pos', '_posh')

    #fill missing questions with '-' like in positve_score_Y-x
    # handle unasked vs suppressed questions. unasked defined by either the while row being blank or,
    # if a question from P is not present in this period. this is added in this case.

    p_questions = [i.qid for i in questions.scored_questions]
    current_historic_questions = mean_df_other_output.index.str.split('_').str[0].unique()

    questions_not_in_current_historic = [i for i in p_questions if i not in current_historic_questions]

    for question in questions_not_in_current_historic:
        mean_df_other_output.loc[f"{question}_posh"] = np.nan

    # find completely empty rows and populate with '-'
    mean_df_other_output.loc[mean_df_other_output[mean_df_other_output.columns].count(axis=1) == 0, mean_df_other_output.columns] = '-'
    #fill remaining nas with '*'
    mean_df_other_output.fillna('*', inplace=True)


    # overall posh per trust:
    overall_posh = mean_df_other.mean(axis=0)

    # overall posh per trust for questions in historical dataset only
    indexes_to_drop = []
    for item in mean_df.index:
        if item not in mean_df_other.index:
            indexes_to_drop.append(item)

    mean_df_h_comparable = mean_df.drop(indexes_to_drop, axis=0)
    overall_pos = mean_df_h_comparable.mean(axis=0)

    # CALC DIFF H OVERALL
    diffhoverall = overall_pos - overall_posh

    # pos score absolute difference
    diff_p_df_picker_average = mean_df.sub(mean_df_picker_average, axis=0)
    diff_p_df_picker_average.index = diff_p_df_picker_average.index.str.replace('_pos', '_diffp')

    diff_p_df_historic = mean_df.sub(mean_df_other, axis=0)
    diff_p_df_historic.index = diff_p_df_historic.index.str.replace('_pos', '_diffh')

    # dataframe of number of positive respinses by comparator
    count_posn_df = scored_df.replace(0, np.nan) \
        .groupby(source_breakdown_field) \
        .count() \
        .transpose()

    count_posn_df_other = scored_df_other.replace(0, np.nan) \
        .groupby(other_source_breakdown_field) \
        .count() \
        .transpose()

    count_posn_df_other_output = count_posn_df_other.copy()
    count_posn_df_other_output.index = count_posn_df_other_output.index.str.replace('_pos', '_posh_N')

    # dataframe of number of scorable responses by comparator
    count_scorable_df = scored_df.groupby(source_breakdown_field) \
        .count() \
        .transpose()
    count_scorable_df_other = scored_df_other.groupby(other_source_breakdown_field) \
        .count() \
        .transpose()

    #PICKER AVERAGE POS N
    #calc as (posscore/100) * scorable N I.e. derive posn from the postive score and base count because it is from an average not calcualted from base numbers

    picker_average_posn = (mean_df_picker_average/100)*count_df_picker_average
    picker_average_posn.to_csv(rf"C:\Users\steve.baker\Desktop\NSS\pickeraverageposn.csv")
    count_df_picker_average.to_csv(rf"C:\Users\steve.baker\Desktop\NSS\pickeraveragescorablen.csv")
    # calculate Z
    def calc_z(score_n_base, scorable_n_base, score_n_comparison, scorable_n_comparison):
        p1 = (score_n_base + 1) / (scorable_n_base + 2)
        p2 = (score_n_comparison + 1) / (scorable_n_comparison + 2)

        nominator = p1.sub(p2, axis=0)

        denominator1 = (p1 * (1 - p1)) / (scorable_n_base + 2)
        denominator2 = (p2 * (1 - p2)) / (scorable_n_comparison + 2)
        denominator_total = np.sqrt(denominator1.add(denominator2, axis=0))

        return nominator / denominator_total

    # apply suppression mask here... I think
    z_scored_historic = calc_z(count_posn_df, count_scorable_df, count_posn_df_other, count_scorable_df_other)
    z_scored_historic = z_scored_historic.mask(mask)
    z_scored_historic = z_scored_historic.mask(mask_other)
    z_scored_historic.index = z_scored_historic.index.str.replace('_pos', '_Zh')

    # add picker average suppression (unlikely to be needed but better to include)
    z_scored_picker_average = calc_z(count_posn_df, count_scorable_df, picker_average_posn, count_df_picker_average)
    z_scored_picker_average.to_csv(rf"C:\Users\steve.baker\Desktop\NSS\pickeraverageZscore.csv")
    z_scored_picker_average = z_scored_picker_average.mask(mask)
    z_scored_picker_average = z_scored_picker_average.mask((count_df_picker_average < suppression_threshold), axis=1)
    z_scored_picker_average.index = z_scored_picker_average.index.str.replace('_pos', '_Z')

    # determine sig or not (buckets)
    def determine_z_sig(z_scored_df):
        conds = [z_scored_df.values < -1.96, z_scored_df.values > 1.96, np.isnan(z_scored_df.values)]
        choices = [-1, 1, np.nan]

        z_bucketed_df = pd.DataFrame(np.select(conds, choices, default=0),
                                     index=z_scored_df.index,
                                     columns=z_scored_df.columns)

        return z_bucketed_df

    z_bucketed_historic = determine_z_sig(z_scored_historic)
    z_bucketed_picker_average = determine_z_sig(z_scored_picker_average)

    # count of significnace outcomes
    df_dict = {'SUMPOS': [0, -1],
               'SUMNEG': [0, 1],
               'SUMZERO': [1, -1]}

    # count significance
    def count_significant(bucketed_df, prefix):
        dataframes = []
        for x in df_dict:
            dataframes.append(bucketed_df.replace(df_dict[x], np.nan).count().rename(f'{prefix}{x}'))
        return dataframes

    count_significant_historic = count_significant(z_bucketed_historic, 'ZH_')
    count_significant_picker_average = count_significant(z_bucketed_picker_average, 'Z_')
    z_count_outputs = count_significant_historic + count_significant_picker_average

    # combine it all!!!

    combined_df = z_bucketed_picker_average.append(diff_p_df_picker_average) \
        .append(z_bucketed_historic) \
        .append(diff_p_df_historic) \
        .append(mean_df_other_output) \
        .append(count_posn_df_other_output) \
        .append(overall_pos.rename('Overall_pos')) \
        .append(overall_posh.rename('Overall_posh')) \
        .append(diffhoverall.rename('DIFFHOVERALL'))

    for series in z_count_outputs:
        combined_df = combined_df.append(series)

    # apply label prefix:
    if level_prefix is not None:
        combined_df.columns = (level_prefix) + (combined_df.columns.str.replace("/", "_"))

    combined_df.index.name = 'Question'

    # save csv
    combined_df.to_csv(rf"C:\Users\steve.baker\Desktop\NSS\{filename}.csv")


def response(source, comparator, org_type_field, outcome_field, filename='response', level_prefix=None):
    source = source.filter([comparator, org_type_field, outcome_field])

    # mapping of outcome codes for the survey
    outcome_options = {
        'NonResponse': ['REF', 'UN', 'NFM', 'N', 'B'],
        'Response': ['CP1', 'CP2', 'CP3', 'CO1', 'CO2', 'CO3', 'CO4', 'CO5', 'CO6', 'CO7'],
        'Ineligible': ['INEL', 'LE', 'EXCL'],
        'Invited': ['CP1', 'CP2', 'CP3', 'CO1', 'CO2', 'CO3', 'CO4', 'CO5', 'CO6', 'CO7', 'REF', 'INEL', 'LE', 'EXCL',
                    'UN', 'NFM', 'N', 'B']
    }

    for outcome in outcome_options:
        source.loc[source[outcome_field].isin(outcome_options[outcome]), outcome] = 1

    # calcualte field
    grouped_df = source.drop(outcome_field, axis=1).groupby(comparator).sum()
    grouped_df['Eligible'] = grouped_df['Invited'] - grouped_df['Ineligible']
    grouped_df = grouped_df.astype(int)
    grouped_df['RR'] = (grouped_df['Response'] / grouped_df['Eligible']) * 100

    # Add trust type and calcualte average response rate when grouped by org_type_field, add back to main df
    type_dict = {x: source[source[comparator] == x][org_type_field].unique()[0] for x in grouped_df.index}
    grouped_df['type'] = grouped_df.index.map(type_dict)
    trust_type_rr = grouped_df[['type', 'RR']].groupby(['type']).mean().rename(columns={'RR': 'RR_mean'})
    grouped_df = grouped_df.merge(trust_type_rr, how='left', left_on='type', right_index=True)

    # apply label prefix:
    if level_prefix is not None:
        grouped_df.index = (level_prefix) + (grouped_df.index.str.replace("/", "_"))

    # reorder
    grouped_df = grouped_df[['NonResponse', 'Response', 'Ineligible', 'RR', 'RR_mean', 'Eligible', 'Invited']]

    # change index header for Etabs
    grouped_df.index.name = 'ID_Code'

    # export to csv
    grouped_df.to_csv(rf'C:\Users\steve.baker\Desktop\NSS\{filename}.csv')


def site_n(source, questions, breakdown_field, l0_field, l1_name_field):
    scored_df = get_score_df(source, questions, breakdown_field, ['pos'])

    count_df = scored_df \
        .groupby(breakdown_field) \
        .count()

    trust_code_dict = {x: source[source[breakdown_field] == x][l0_field].unique()[0] for x in count_df.index}

    count_df['ID_CODE'] = count_df.index.map(trust_code_dict)

    site_name_dict = {x: source[source[breakdown_field] == x][l1_name_field].unique()[0] for x in count_df.index}

    count_df['SiteName'] = count_df.index.map(site_name_dict)

    # Add level identifiers
    count_df.index = 'L1' + count_df.index
    count_df['ID_CODE'] = 'L0' + count_df['ID_CODE'].str.replace('/', '_')

    count_df.columns = count_df.columns.str.replace('_pos', '_respondents')
    count_df.index.name = 'SITE_CODE'

    count_df = count_df.reset_index()
    count_df = count_df.set_index('ID_CODE')

    count_df.to_csv(rf'C:\Users\steve.baker\Desktop\NSS\Site_N.csv')


def survey_information(source, breakdown_field, outcome_field, level_prefix, survey_name, current_period,
                       period_minus_1, period_minus_2, period_minus_3, period_minus_4, name_column, type_column,
                       type_name_column, outcome_map):
    # dict to hold all dataframes for this sheet.
    dataframes = {}

    source['SURVEY_NAME'] = survey_name
    survey_name_df = pd.pivot_table(source[['SURVEY_NAME', type_column]], index='SURVEY_NAME', columns=type_column,
                                    aggfunc=np.size) / 2
    survey_name_df.columns = 'Count_' + survey_name_df.columns

    dataframes['Survey Name'] = survey_name_df

    # Survey Years
    survey_years_df = pd.DataFrame(
        data={'Mean': [current_period, period_minus_1, period_minus_2, period_minus_3, period_minus_4]},
        index=['YEAR', 'YEAR_MINUS1', 'YEAR_MINUS2', 'YEAR_MINUS3', 'YEAR_MINUS4'],
        columns=['Mean'])
    dataframes['Survey Years'] = survey_years_df

    # Count Trusts
    hello = source[breakdown_field].value_counts().to_frame()

    # add trust/site name
    name_dict = {x: source[source[breakdown_field] == x][name_column].unique()[0] for x in hello.index}
    hello['Name'] = hello.index.map(name_dict)

    # add level indicator
    hello.index = level_prefix + hello.index.str.replace('/', '_')

    hello = hello.rename(columns={breakdown_field: 'Count'})
    trust_name_df = hello[['Name', 'Count']]
    dataframes['Trust Name'] = trust_name_df

    # outcome tables (one for paper, online and combined)

    def create_coutcome_table(inputdf):
        dfs = []
        for outcome in outcome_map:
            df = inputdf[inputdf[outcome_field].isin(outcome_map[outcome])]
            df2 = df[breakdown_field].value_counts().rename(outcome)
            dfs.append(df2)

        dfconcat = pd.concat(dfs, axis=1).fillna(0).transpose()
        invited_df = dfconcat.sum().rename('Invited').to_frame().transpose()
        outcome_df = invited_df.append(dfconcat)

        # find missing columns (i.e. trusts with no paper) so everyone gets a copy)
        for x in [i for i in source[breakdown_field].unique().tolist() if i not in outcome_df.columns]:
            outcome_df[x] = 0

        outcome_df.columns = level_prefix + outcome_df.columns.str.replace('/', '_')

        return outcome_df

    dataframes['Outcome Paper'] = create_coutcome_table(source[source['SURVEY MODE'] == 'Paper'])
    dataframes['Outcome Online'] = create_coutcome_table(source[source['SURVEY MODE'] == 'Online'])
    dataframes['Outcome Total'] = create_coutcome_table(source)

    # Organisation_Type

    hello3 = source[[breakdown_field, outcome_field]].groupby(breakdown_field).count()
    type_dict = {x: source[source[breakdown_field] == x][type_name_column].unique()[0] for x in hello3.index}
    hello3['Organisation Type'] = hello3.index.map(type_dict)
    hello3.index = level_prefix + hello3.index.str.replace('/', '_')
    hello3 = hello3.rename(columns={outcome_field: 'Count', breakdown_field: ''})
    organisation_type_df = hello3[['Organisation Type', 'Count']]
    dataframes['Organisation Type'] = organisation_type_df

    # count org type
    count_org_df = hello3.groupby('Organisation Type').count()
    dataframes['Count of Organisation Type'] = count_org_df

    # write all dfs to excell
    writer = pd.ExcelWriter(rf'C:\Users\steve.baker\Desktop\NSS\SurveyInformation.xlsx',
                            engine='xlsxwriter')

    worksheet = writer.book.add_worksheet('Management Report')
    writer.sheets['Management Report'] = worksheet

    row = 0
    for table in dataframes:
        title = f'TABLE: {table}'
        worksheet.write(row, 0, title)
        dataframes[table].to_excel(writer, sheet_name='Management Report', startcol=0, startrow=row + 2)
        row = row + len(dataframes[table]) + 4

    writer.save()


def improvement_maps(source, questions, breakdown_field, suppression_threshold, level_prefix):
    category_dict = {
        'SECTION B': {'B4': 0.555,
                      'B6': 0.788,
                      'B8': 0.636,
                      'B9': 0.802,
                      'B10': 0.875,
                      'B11': 0.700,
                      'B12': 0.395,
                      'B13': 0.589,
                      'B14': 0.271,
                      'B15': 0.713,
                      'B16': 0.611},
        'SECTION C-D': {'C1': 0.682,
                        'C2': 0.864,
                        'C10': 0.354,
                        'C11': 0.577,
                        'C12': 0.856,
                        'C14': 0.640,
                        'C15': 0.854,
                        'C16': 0.891,
                        'C17': 0.811,
                        'C18': 0.893,
                        'C19': 0.950,
                        'C20': 0.886,
                        'C21': 0.631,
                        'D2': 0.285,
                        'D4': 0.652,
                        'D5': 0.691,
                        'D6': 0.753,
                        'D7': 0.250,
                        'D8': 0.556},

        'SECTION E-F': {'E2': 0.451,
                        'E3': 0.622,
                        'F1': 0.571,
                        'F2': 0.574,
                        'F3': 0.750,
                        'F6': 0.518,
                        'F7': 0.677,
                        'F8': 0.746,
                        'F9': 0.826,
                        'F10': 0.790,
                        'F12': 0.775,
                        'F13': 0.686,
                        'F14': 0.762,
                        'F15': 0.640,
                        'F16': 0.681,
                        'F17': 0.805,
                        'F18': 0.629
                        }}
    scored_df = get_score_df(source, questions, breakdown_field, ['pos'], period='P')
    mean_df = get_mean_df(scored_df, breakdown_field)

    # suppress mean_df
    count_df = scored_df \
        .groupby(breakdown_field) \
        .count() \
        .transpose()

    # apply suppression mask to mean df
    mask = (count_df < suppression_threshold)
    mean_df = mean_df.mask(mask)

    if level_prefix is not None:
        mean_df.columns = (level_prefix) + (mean_df.columns.str.replace("/", "_"))

    dfinput = mean_df.transpose()

    writer = pd.ExcelWriter(rf'C:\Users\steve.baker\Desktop\MAT Nonsense\output\etabs\hello\ImprovementMaps_All.xlsx',
                            engine='xlsxwriter')

    for category in category_dict:
        category_qs = category_dict[category]

        pos_columns = [i + '_pos' for i in category_qs]

        df = dfinput[pos_columns]

        df['ID_CODE'] = df.index
        df = df.melt(id_vars='ID_CODE')
        df = df.rename({'variable': 'QUESTION', 'value': 'POS_SCORE'}, axis=1)

        question_list = questions.questions_dict['P']
        pos_text_mapping_dict = {n.get_qid(): n.q_pos_text for n in question_list}

        group_df = df[['QUESTION', 'POS_SCORE']].groupby('QUESTION').mean()

        group_df = group_df.rename({'POS_SCORE': 'AVERAGE'}, axis=1)

        group_df['SECTION'] = category
        group_df['CORRELATION'] = category_qs.values()

        group_df['MIN'] = np.nanmin(group_df['CORRELATION'])
        group_df['MAX'] = np.nanmax(group_df['CORRELATION'])
        group_df['RANGE'] = np.nanmax(group_df['CORRELATION']) - np.nanmin(group_df['CORRELATION'])

        df_new = pd.merge(left=df, right=group_df, how='left', left_on='QUESTION', right_on=group_df.index)

        df_new = df_new.sort_values('ID_CODE')

        df_new['QLABEL'] = df_new['QUESTION'].str.rstrip('_pos')
        df_new['SHORT_TEXT'] = df_new['QLABEL'].map(pos_text_mapping_dict)

        df_new['IMPORTANCE'] = (df_new['CORRELATION'] - df_new['MIN']) / (df_new['RANGE'])

        # handle NaNs here perhaps...
        df_new['CENTRED_SCORE'] = (df_new['POS_SCORE'] - df_new['AVERAGE'])

        trusts = df_new['ID_CODE'].unique().tolist()

        trusts_list = []

        for trust in trusts:
            trust_df = df_new[df_new['ID_CODE'] == trust]
            xmin = np.nanmin(trust_df['CENTRED_SCORE'])
            xmax = np.nanmax(trust_df['CENTRED_SCORE'])

            xaxiscalcmin = -20 if (xmin > -20 or np.isnan(xmin)) else xmin
            # round up
            trust_df['XAXISCALCMIN'] = math.floor(xaxiscalcmin)

            xaxiscalcmax = 20 if (xmax < 20 or np.isnan(xmax)) else xmax
            trust_df['XAXISCALCMAX'] = math.ceil(xaxiscalcmax)

            xaxismax = max(abs(xaxiscalcmin), abs(xaxiscalcmax))
            xaxismin = -1 * xaxismax

            trust_df['XAXIS_MIN'] = math.floor(xaxismin)
            trust_df['XAXIS_MAX'] = math.ceil(xaxismax)

            trust_df['XAXIS_UNIT'] = math.ceil(xaxismax)
            trust_df['XAXIS_MID'] = 0

            trusts_list.append(trust_df)

        combineddf = trusts_list[0]

        for i, x in enumerate(trusts_list):
            if i != 0:
                combineddf = combineddf.append(x)

        combineddf['QUADRANT'] = ''

        for i, row in combineddf.iterrows():
            if row['CENTRED_SCORE'] >= 0 and row['IMPORTANCE'] > 0.5:
                combineddf.loc[i, 'QUADRANT'] = 'MAINTAIN'
            if row['CENTRED_SCORE'] >= 0 and row['IMPORTANCE'] <= 0.5:
                combineddf.loc[i, 'QUADRANT'] = 'MONITOR'
            if row['CENTRED_SCORE'] < 0 and row['IMPORTANCE'] > 0.5:
                combineddf.loc[i, 'QUADRANT'] = 'DEVELOP'
            if row['CENTRED_SCORE'] < 0 and row['IMPORTANCE'] <= 0.5:
                combineddf.loc[i, 'QUADRANT'] = 'MANAGE'

        combineddf['SUM'] = 1

        combineddf.to_excel(writer, index=False, sheet_name=category)

    writer.save()
    pass
