def get_rag(source,
            seperate_by_field='trust_id',
            seperator=None,
            group_by=None,
            questions=None,
            score_type='pos'):

    #check for single layer or multi group by
    if isinstance(group_by, str):
        columns_for_scoring, columns_output = [group_by], [group_by]
        number_groups = 1
    elif isinstance(group_by, list):
        columns_for_scoring, columns_output = group_by.copy(), group_by.copy()
        number_groups = len(group_by)

    #iteratre trough questions to select columns and theme mapping
    topic_dict = {}
    for question in questions.scored_questions:
        topic_dict[question.get_qid() + scoring_terms_dict[score_type]['suffix']] = questions.questions_dict[question.get_qid()].category

        columns_for_scoring.append(question.get_qid())
        columns_output.append(question.get_qid() + scoring_terms_dict[score_type]['suffix'])

    # check type of input, either reporting, survey or just a df
    if isinstance(source, Reporting):
        df = (source.df[source.df[seperate_by_field] == seperator])[columns_output]
    elif isinstance(source, Survey):
        df = (source.reporting.df[source.reporting.df[seperate_by_field] == seperator])[columns_output]
    else:
        df = (source[source[seperate_by_field] == seperator])[columns_for_scoring]
        df = calc_scores(df, questions, [score_type])[columns_output]


    df_mean = df.groupby(group_by).mean().transpose()
    df_count = df.groupby(group_by).count().transpose()

    # suppression
    suppression_mask = df_count < 11
    df_mean_suppressed = df_mean.mask(suppression_mask)

    overall_df_mean = df_mean_suppressed.mean(axis=1).rename('Overall')
    overall_df_count = df_count.sum(axis=1).rename('Overall')

    combined_df_mean_suppressed = df_mean_suppressed.join(overall_df_mean)
    combined_df_count = df_count.join(overall_df_count)



    # write to excel
    writer = pd.ExcelWriter(output_path/f'{seperator}_RAG_{group_by}.xlsx', engine='xlsxwriter')
    (combined_df_mean_suppressed/100).replace(np.nan, '*').to_excel(writer, sheet_name='Sheet1')
    worksheet = writer.sheets['Sheet1']
    writer.save()

    return output_path / f'{seperator}_RAG_{group_by}.xlsx'