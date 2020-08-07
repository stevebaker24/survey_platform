from survey_platform import survey_platform as sp
import pandas as pd
import numpy as np


def get_score_df(source, questions, comparator, score_types):
    source_columns = questions.columns_to_score

    # filter columns
    source = source.filter([comparator] + source_columns)

    # get scores
    scored_df = sp.calc_scores(source, questions, score_types=score_types) \
        .drop(source_columns, axis=1)

    return scored_df


def get_mean_df(scored_df, comparator):
    mean_df = scored_df.groupby(comparator)\
                       .mean()\
                       .transpose()
    return mean_df


def positivescoretable_current(source, questions, comparator, suppression_threshold):
    scored_df = get_score_df(source, questions, comparator, ['pos', 'neu', 'neg'])
    mean_df = get_mean_df(scored_df, comparator)

    count_df = scored_df.rename(columns=lambda x: x+'_n' if x != comparator else x)\
                        .groupby(comparator)\
                        .count()\
                        .transpose()


    # calculate the overall scores as dfs
    overall_dfs = []
    for suffix in sp.score_suffixes:
        overall_dfs.append(mean_df[mean_df.index.str.contains(suffix)].mean().rename(f'Overall{suffix}'))

    # apply suppression mask to mean df
    mask = (count_df < suppression_threshold)
    mask.index = mask.index.str.strip('_n')
    mean_df = mean_df.mask(mask)

    # append all the different dfs
    output_df = mean_df.append(count_df)

    for overall_df in overall_dfs:
        output_df = output_df.append(overall_df)

    # name the index column
    output_df.index.name = 'Question'

    # save csv
    output_df.to_csv(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\etabs\posscoretable.csv')


def minmeanmax(source, questions, comparator):
    scored_df = get_score_df(source, questions, comparator, ['pos'])
    mean_df = get_mean_df(scored_df, comparator)

    dataframes = []
    for aggregate_function in ['min', 'mean', 'max']:
        df = eval(f'mean_df.{aggregate_function}(axis=1)')
        df.index = df.index.str.replace('_pos', f'_{aggregate_function}')
        dataframes.append(df)

    # need to build this out to include all dfs with table names...
    writer = pd.ExcelWriter(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\etabs\minmeanmax.xlsx', engine='xlsxwriter')
    dataframes[0].to_excel(writer, sheet_name='Sheet1')
    writer.save()


def ez(source, questions, comparator):
    scored_df = get_score_df(source, questions, comparator, ['pos'])
    mean_df = get_mean_df(scored_df, comparator)

    # dataframe of number of positive respinses by comparator
    count_posn_df = scored_df.replace(0, np.nan)\
                             .groupby(comparator)\
                             .count()\
                             .transpose()

    # dataframe of number of scorable responses by comparator
    count_scorable_df = scored_df.groupby(comparator)\
                                 .count()\
                                 .transpose()

    # dataframe of number of positive responses averaged
    count_posn_df_picker = count_posn_df.sum(axis=1)

    # dataframe of number of scorable responses averaged
    count_scorable_df_picker = count_scorable_df.sum(axis=1)

    # calc z score (for historic need to be able to account for series and dataframes (although may work)
    p1 = (count_posn_df + 1) / (count_scorable_df + 2)
    p2 = (count_posn_df_picker + 1) / (count_scorable_df_picker + 2)

    nominator = p1.sub(p2, axis=0)

    denominator1 = (p1 * (1 - p1)) / (count_scorable_df + 2)
    denominator2 = (p2 * (1 - p2)) / (count_scorable_df_picker + 2)
    denominator_total = np.sqrt(denominator1.add(denominator2, axis=0))

    z_scored_df = nominator / denominator_total

    # determine sig or not (buckets)
    conds = [z_scored_df.values < -1.96, z_scored_df.values > 1.96]
    choices = [-1, 1]

    z_bucketed_df = pd.DataFrame(np.select(conds, choices, default=0),
                 index=z_scored_df.index,
                 columns=z_scored_df.columns)

    # pos score absolute difference
    mean_df_picker_average = mean_df.mean(axis=1)
    diff_p_df = mean_df.sub(mean_df_picker_average, axis=0)

    # count of significnace outcomes
    df_dict = {'Z_SUMPOS': [0, -1],
               'Z_SUMNEG': [0, 1],
               'Z_SUMZERO': [1, -1]}

    dataframes = []
    for x in df_dict:
        dataframes.append(z_bucketed_df.replace(df_dict[x], np.nan).count().rename(x))


    # save csv, need to append all dfs.
    z_scored_df.to_csv(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\etabs\z.csv')


def response(source, comparator, outcome_field):

    source = source.filter([comparator, outcome_field])

    outcome_options = {
        'ineligible': [2, 3, 5, 7],
        'invited': [1, 2, 3, 4, 5, 6, 7],
        'nonresponse': [4, 6],
        'response': [1],
    }

    for outcome in outcome_options:
        source.loc[source[outcome_field].isin(outcome_options[outcome]), outcome] = 1

    grouped_df = source.drop(outcome_field, axis=1).groupby(comparator).sum()

    grouped_df['eligible'] = grouped_df['invited'] - grouped_df['ineligible']
    grouped_df['rr'] = grouped_df['response'] / grouped_df['eligible']
    grouped_df['rrmean'] = grouped_df['rr'].mean()

    grouped_df.to_csv(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\etabs\response.csv')