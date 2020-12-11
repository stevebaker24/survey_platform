import survey_platform as sp
import rag
import freq_table as ft
import sesreport
import report

questions = sp.Questions.from_file(
    r"C:\Users\steve.baker\Desktop\MAT Nonsense\NMEC20 POS SCORE MAPPING V1.1 RAG format SB.xlsx")

responses = sp.Responses(
    r"C:\Users\steve.baker\Desktop\MAT Nonsense\FINAL NMEC DATA\NMEC20 COMBINED RESPONSES CLEANED.csv", indexcol='PRN')
sample = sp.Sample(r"C:\Users\steve.baker\Desktop\MAT Nonsense\FINAL NMEC DATA\NMEC20 FINAL SAMPLE.xlsx",
                   indexcol='Record number')
combined = sp.Combined(sample, responses)
combined.df = combined.df[combined.df['Outcome'] == 1]

# ft.get_frequency_table(source=combined.df, questions=questions, sheet_breakdown_fields=['Place of birth: NHS site code'], suppression_threshold=30, output_path=r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\freq')

# ft.create_ft(source=combined.df, questions=questions, sheet_breakdown_fields=['Extra2'], suppression_threshold=30, output_path=r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\freq')

# rag.create_rag(source=combined.df, questions=questions, sheet_breakdown_fields=[['Extra1', 'Extra2'], 'Extra1'], suppression_threshold=30, output_path=r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\freq')

for trust in combined.df['Trust code'].unique():
    trustdata = combined.df[combined.df['Trust code'] == trust]

    #trust code into file name.

    sesreport.create_ses(source=trustdata, questions=questions, sheet_breakdown_fields=[['Extra1', 'Extra2'], 'Extra1'],
                         suppression_threshold=10, output_path=r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\freq',
                         external_comparator=combined.df, comparator_text='Picker Average',
                         overall_text='Your Organisation')

# responses_histroic_all = sp.Responses(r"C:\Users\steve.baker\PycharmProjects\python-scripts\historicmatcleanoutput.csv", indexcol='Recordnumber')
# responses_histroic_p_1 = responses_histroic_all.df[responses_histroic_all.df['SURVEY'] == 'MAT19']
# responses_histroic_p_2 = responses_histroic_all.df[responses_histroic_all.df['SURVEY'] == 'MAT18']
# responses_histroic_p_3 = responses_histroic_all.df[responses_histroic_all.df['SURVEY'] == 'MAT17']
# responses_histroic_p_4 = responses_histroic_all.df[responses_histroic_all.df['SURVEY'] == 'MAT15']
# responses_histroic_p_5 = responses_histroic_all.df[responses_histroic_all.df['SURVEY'] == 'MAT13']

# combined.df.to_csv(r"C:\Users\steve.baker\Desktop\MAT Nonsense\output\combined2.csv")

# need to ensure that outcome is accounted for with these reports (no need, if there's responses, it is reported for MAT)

# sp.get_frequency_table(source=combined.df, questions=questions, file_breakdown_field='Trust code', sheet_breakdown_fields=['Total', 'Place of birth: NHS site', 'CCG code', 'Extra1', 'Extra2'], suppression_threshold=30)
# sp.get_freetext(source=combined.df, questions=questions, file_breakdown_field='Trust code', sheet_breakdown_fields=['Trust code'], suppression_framework='patient', suppression_threshold=30)

# scores for Steve S Factor Analysis
# scored = sp.calc_scores(combined.df, questions, score_types=['pos'], period='P')
# scored.to_csv(r'C:\Users\steve.baker\Desktop\MAT Nonsense\output\scored.csv')

# management
# etabs.positivescoretable(combined.df, questions, breakdown_field='Trust code', suppression_threshold=30, filename='PositiveScoreTable_CURRENT', level_prefix='L0')
# etabs.positivescoretable(responses_histroic_p_1, questions, breakdown_field='Trustcode', suppression_threshold=30, filename='PositiveScoreTable_Y-1', period='P-1', level_prefix='L0')
# etabs.positivescoretable(responses_histroic_p_2, questions, breakdown_field='Trustcode', suppression_threshold=30, filename='PositiveScoreTable_Y-2', period='P-1', level_prefix='L0')
# etabs.positivescoretable(responses_histroic_p_3, questions, breakdown_field='Trustcode', suppression_threshold=30, filename='PositiveScoreTable_Y-3', period='P-1', level_prefix='L0')
# etabs.positivescoretable(responses_histroic_p_4, questions, breakdown_field='Trustcode', suppression_threshold=30, filename='PositiveScoreTable_Y-4', period='P-1', level_prefix='L0')

# etabs.ez(combined.df, responses_histroic_p_1, questions, source_breakdown_field='Trust code', other_source_breakdown_field='Trustcode', level_prefix='L0', suppression_threshold=30, filename='SignificanceTable_ALL')

# etabs.positivescoretable(combined.df, questions, breakdown_field='Place of birth: NHS site code', suppression_threshold=30, filename='SiteScores_CURRENT', level_prefix='L1')

# etabs.minmeanmax(combined.df, questions, breakdown_field='Trust code', suppression_threshold=30)
# etabs.site_n(combined.df, questions, breakdown_field='Place of birth: NHS site code', l0_field='Trust code')

# etabs.response(combined.df, comparator='Trust code', outcome_field='Outcome', filename='RespRates_CURRENT', level_prefix='L0')
# etabs.response(responses_histroic_p_1, comparator='Trustcode', outcome_field='Outcome', filename='RespRates_HISTORIC', level_prefix='L0')

# etabs.survey_information(combined.df, breakdown_field='Trust code', outcome_field='Outcome', level_prefix='L0')

# etabs.improvement_maps(combined.df, questions, breakdown_field='Trust code', suppression_threshold=30, level_prefix='L0')


# site
# etabs.minmeanmax(combined.df, questions, breakdown_field='Trust code', suppression_threshold=30)
# etabs.positivescoretable(combined.df, questions, breakdown_field='Trust code', suppression_threshold=30, filename='PositiveScoreTable_CURRENT', level_prefix='L0')

### has been manually tweaked after to show RR mean as mean for the sites specific trust, need to implement.
# etabs.response(combined.df, comparator='Place of birth: NHS site code', outcome_field='Outcome', filename='RespRates_CURRENT', level_prefix='L1')
# etabs.response(responses_histroic_p_1, comparator='PlaceofbirthNHSsitecode', outcome_field='Outcome', filename='RespRates_HISTORIC', level_prefix='L1')
##

# spun off a speperatemethod as a quick fix to allow for comparison to trust instead of picker average, need to implement properly
# etabs.ez_site(combined.df, responses_histroic_p_1, questions, source_breakdown_field='Place of birth: NHS site code', other_source_breakdown_field='PlaceofbirthNHSsitecode', level_prefix='L1', suppression_threshold=30, filename='SignificanceTable_SITE')
#

###
# etabs.site_n(combined.df, questions, breakdown_field='Place of birth: NHS site code', l0_field='Trust code')
# etabs.positivescoretable(combined.df, questions, breakdown_field='Place of birth: NHS site code', suppression_threshold=30, filename='SiteScores_CURRENT', level_prefix='L1')
# etabs.positivescoretable(responses_histroic_p_2, questions, breakdown_field='PlaceofbirthNHSsitecode', suppression_threshold=30, filename='SiteScoreTable_Y-2', period='P-1', level_prefix='L1')
# etabs.positivescoretable(responses_histroic_p_3, questions, breakdown_field='PlaceofbirthNHSsitecode', suppression_threshold=30, filename='SiteScoreTable_Y-3', period='P-1', level_prefix='L1')
# etabs.positivescoretable(responses_histroic_p_4, questions, breakdown_field='PlaceofbirthNHSsitecode', suppression_threshold=30, filename='SiteScoreTable_Y-4', period='P-1', level_prefix='L1')
# #
# etabs.survey_information(combined.df, breakdown_field='Place of birth: NHS site code', outcome_field='Outcome', level_prefix='L1')
