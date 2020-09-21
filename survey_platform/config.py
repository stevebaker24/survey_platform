output_path = r'C:\Users\steve.baker\Desktop\MAT Nonsense'

scoring_terms_dict = {'pos': {'value': 1, 'string': 'Positive', 'suffix': '_pos'},
                      'neu': {'value': 2, 'string': 'Neutral', 'suffix': '_neu'},
                      'neg': {'value': 3, 'string': 'Negative', 'suffix': '_neg'},
                      'ignore': {'value': 4, 'string': 'Exclude', 'suffix': None}}

scoring_ignore_value = scoring_terms_dict['ignore']['value']
scored_values = [scoring_terms_dict[i]['value'] for i in scoring_terms_dict if i != 'ignore']
score_suffixes = [scoring_terms_dict[i]['suffix'] for i in scoring_terms_dict if i != 'ignore']

output_path = Path(config.output_path)

survey_periods = {
    'P': '2020',
    'P-1': '2019',
    'P-2': '2018',
    'P-3': '2017',
    'P-4': '2016'
}

l0_name_map = {'RTK': 'Ashford and St Peter\'s Hospitals NHS Foundation Trust',
                  'R1H': 'Barts Health NHS Trust',
                  'RXQ': 'Buckinghamshire Healthcare NHS Trust',
                  'RN7': 'Dartford and Gravesham NHS Trust',
                  'RTE': 'Gloucestershire Hospitals NHS Foundation Trust',
                  'RN5': 'Hampshire Hospitals NHS Foundation Trust',
                  'RXN': 'Lancashire Teaching Hospitals NHS Foundation Trust',
                  'RJ2': 'Lewisham and Greenwich NHS Trust',
                  'R1K': 'London North West University Healthcare NHS Trust',
                  'R0A': 'Manchester University NHS Foundation Trust',
                  'RXF': 'Mid Yorkshire Hospitals NHS Trust',
                  'RX1': 'Nottingham University Hospitals NHS Trust',
                  'RQW': 'The Princess Alexandra Hospital NHS Trust',
                  'RH8': 'Royal Devon and Exeter NHS Foundation Trust'}

l1_name_map = {'R0A05': 'ST MARY\'S HOSPITAL',
                 'R0A07': 'WYTHENSHAWE HOSPITAL',
                 'R1H12': 'THE ROYAL LONDON HOSPITAL',
                 'R1H41': 'BARKING BIRTH CENTRE',
                 'R1H90': 'BLT BIRTH CENTRE',
                 'R1HKH': 'WHIPPS CROSS UNIVERSITY HOSPITAL',
                 'R1HNH': 'NEWHAM GENERAL HOSPITAL',
                 'RJ224': 'UNIVERSITY HOSPITAL LEWISHAM',
                 'RJ231': 'QUEEN ELIZABETH HOSPITAL',
                 'RN506': 'BASINGSTOKE AND NORTH HAMPSHIRE HOSPITAL',
                 'RN541': 'ROYAL HAMPSHIRE COUNTY HOSPITAL',
                 'RN542': 'ANDOVER WAR MEMORIAL HOSPITAL',
                 'RTE01': 'CHELTENHAM GENERAL HOSPITAL',
                 'RTE03': 'GLOUCESTERSHIRE ROYAL HOSPITAL',
                 'RTE27': 'STROUD MATERNITY HOSPITAL',
                 'RTK01': 'ST PETER\'S HOSPITAL',
                 'RX1CC': 'NOTTINGHAM UNIVERSITY HOSPITALS NHS TRUST - CITY CAMPUS',
                 'RX1RA': 'NOTTINGHAM UNIVERSITY HOSPITALS NHS TRUST - QUEEN\'S MEDICAL CENTRE CAMPUS',
                 'RXF03': 'PONTEFRACT GENERAL INFIRMARY',
                 'RXF05': 'PINDERFIELDS GENERAL HOSPITAL',
                 'RXF10': 'DEWSBURY & DISTRICT HOSPITAL',
                 'RXN01': 'CHORLEY & SOUTH RIBBLE HOSPITAL',
                 'RXN02': 'ROYAL PRESTON HOSPITAL',
                 'RXQ02': 'STOKE MANDEVILLE HOSPITAL',
                 'RXQ50': 'WYCOMBE HOSPITAL',
                 'RH801': 'ROYAL DEVON & EXETER HOSPITAL (WONFORD)',
                 'RN707': 'DARENT VALLEY'}
