from survey_platform import survey_platform as sp
import pandas as pd
import numpy as np

def positivescoretable_current(source, questions, comparator):

    # create list of columns
    columns = []
    for question in questions.get_scored_questions():
        columns.append(question.online_qid)
        continue

    # filter columns
    source = source.filter([comparator] + columns)

    # get scores
    scored_df = sp.calc_scores(source, questions, score_types=['pos', 'neu', 'neg']).drop(columns, axis=1)

    count_df = scored_df.rename(columns=lambda x: x+'.N' if x != comparator else x)\
                        .groupby(comparator)\
                        .count()\
                        .transpose()

    mean_df = scored_df.groupby(comparator)\
                       .mean()\
                       .transpose()

    # calculate the overall scores
    overall_dfs = []
    for suffix in sp.suffixes:
        overall_dfs.append(mean_df[mean_df.index.str.contains(suffix)].mean().rename(f'Overall{suffix}'))

    # apply suppression mask
    mask = (count_df < sp.suppression_threshold)
    mask.index = mask.index.str.strip('_N')
    mean_df = mean_df.mask(mask)

    # append all the different tables
    outdf = mean_df.append(count_df)
    for overall_df in overall_dfs:
        outdf.append(overall_df)

    # name the index column
    outdf.index.name = 'Question'

    # save csv
    outdf.to_csv(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\etabs\posscoretable.csv')


def minmeanmax(source, questions, comparator):
    # create list of columns
    columns = []
    for question in questions.get_scored_questions():
        columns.append(question.online_qid)
        continue

    # filter columns
    source = source.filter(columns + [comparator])

    # get scores
    scored_df = sp.calc_scores(source, questions).drop(columns, axis=1)

    mean_df = scored_df.groupby(comparator)\
                       .mean()\
                       .transpose()

    dfs = []
    for x in ['min', 'mean', 'max']:
        df = eval(f'mean_df.{x}(axis=1)')
        df.index = df.index.str.replace('_pos', f'_{x}')
        dfs.append(df)

    writer = pd.ExcelWriter(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\etabs\minmeanmax.xlsx', engine='xlsxwriter')
    dfs[0].to_excel(writer, sheet_name='Sheet1')
    writer.save()


def ez(source, questions, comparator):

    # create list of columns
    columns = []
    for question in questions.get_scored_questions():
        columns.append(question.online_qid)
        continue

    # filter columns
    source = source.filter([comparator] + columns)

    # get scores
    scored_df = sp.calc_scores(source, questions).drop(columns, axis=1)

    mean_df = scored_df.groupby(comparator)\
                       .mean()\
                       .transpose()

    mean_df_picker = mean_df.mean(axis=1)

    count_posn_df = scored_df.replace(0, np.nan)\
                             .groupby(comparator)\
                             .count()\
                             .transpose()

    count_scorable_df = scored_df.groupby(comparator)\
                                 .count()\
                                 .transpose()

    count_posn_df_picker = count_posn_df.sum(axis=1)

    count_scorable_df_picker = count_scorable_df.sum(axis=1)




    #calc z score
    p1 = (count_posn_df + 1) / (count_scorable_df + 2)
    p2 = (count_posn_df_picker + 1) / (count_scorable_df_picker + 2)

    nominator = p1.sub(p2, axis=0)

    denominator1 = (p1 * (1 - p1)) / (count_scorable_df + 2)
    denominator2 = (p2 * (1 - p2)) / (count_scorable_df_picker + 2)
    denominator_total = np.sqrt(denominator1.add(denominator2, axis=0))

    final = nominator / denominator_total


    #determine sig or not (buckets)
    conds = [final.values < -1.96 , final.values > 1.96]
    choices = [-1, 1]

    z_becketed_df = pd.DataFrame(np.select(conds, choices, default=0),
                 index=final.index,
                 columns=final.columns)


    #pos score absolute difference
    diff_p = mean_df.sub(mean_df_picker, axis=0)

    Z_SUMPOS = z_becketed_df.replace([0, -1], np.nan).count()
    Z_SUMNEG = z_becketed_df.replace([0, 1], np.nan).count()
    Z_SUMZERO = z_becketed_df.replace([1, -1], np.nan).count()

    # save csv
    final.to_csv(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\etabs\z.csv')

def response(source, comparator):

    source = source.filter([comparator, 'outcome'])

    outcome_options = {
        'ineligible': [2, 3, 5, 7],
        'invited': [1, 2, 3, 4, 5, 6, 7],
        'nonresponse': [4, 6],
        'response': [1],
    }

    for outcome in outcome_options:
        source.loc[source['outcome'].isin(outcome_options[outcome]), outcome] = 1

    grouped = source.drop('outcome', axis=1).groupby(comparator).sum()

    grouped['eligible'] = grouped['invited'] - grouped['ineligible']
    grouped['rr'] = grouped['response'] / grouped['eligible']
    grouped['rrmean'] = grouped['rr'].mean()

    grouped.to_csv(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\etabs\response.csv')