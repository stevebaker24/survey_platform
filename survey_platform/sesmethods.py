import pandas as pd
from report import get_agg_df

sesmap = {5: 10, 4: 7.5, 3: 5, 2: 2.5, 1: 0}
ses_questions_dict = {'SESCAT1': ['B5', 'B13', 'B15'], 'SESCAT2': ['C18', 'C21', 'D1'], 'SESCAT3': ['D4', 'D8', 'E3']}


def get_ses_questions(questions_dict: dict) -> list:
    """Gets a list of questions from the ses_questrions dictionary of structure {'Category': [List of Qs]}"""
    return sum([value for value in questions_dict.values()], [])


def ses_map_data(data: pd.DataFrame, questions: list, map_dict: dict) -> pd.DataFrame:
    """Maps the recode values to the corresponding SES value for each SES question (ses_questions_list) accordinbg to
    the ses_map dictionary """
    for question in questions:
        data[question] = data[question].map(map_dict)
    return data


def create_category_ses_df(data: pd.DataFrame, breakdown, suppression_threshold: int):
    """creates a ses dataframe with all of the questions in a category and an overall row"""
    df = create_category_ses_df(data, breakdown, suppression_threshold)
    catergoy_overall = create_average_ses(df, 'Overall')
    return df.append(catergoy_overall)


def create_ses_df(data, breakdown=None, suppression_threshold=10) -> pd.DataFrame:
    """Creates the SES score dataframe, with an overall row, with or without a breakdown suppressed to the
    suppression threshold. Typically useful for a single category. Calculates the count of responses and the sum of the
    mapped ses value. sum/count gives SES score. Values are suppressed accoding to the count df."""

    countdf = get_agg_df(data, breakdown, 'count')
    sumdf = get_agg_df(data, breakdown, 'sum')
    return (sumdf / countdf).mask(countdf < suppression_threshold)


def create_average_ses(data: pd.DataFrame, series_name: str) -> pd.Series:
    """Creeates an overall ses row (average). If a column contains no blanks (i.e. suppressed or missing data), the
    overall score is the average of the individual scores. """

    return data.mean().mask(data.count() < len(data)).rename(series_name)


def create_total_ses_df(data: pd.DataFrame, breakdown, questions_dict: dict,
                        suppression_threshold: int) -> pd.DataFrame:
    """Creeates an overall ses data frame, with all categories (with summary) and an overall SES row. Fills na values
    (i.e. missing or suppressed) with '*'"""

    #Creates a list of dfs for each category and combined them.
    category_dfs = []
    for questions in questions_dict.values():
        df = data[questions] if breakdown is None else data[breakdown + questions]
        category_df = create_category_ses_df(df, breakdown, suppression_threshold)
        category_dfs.append(category_df)
    combineddf = pd.concat(category_dfs)

    # Adds a total staff engagement score row
    total_ses = create_average_ses(combineddf.loc['Overall'], 'Staff Engagement Score')

    return combineddf.append(total_ses).fillna('*')
