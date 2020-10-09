# Frequency Table Format
BASE_FORMAT = {'font_name': 'Arial', 'font_color': '#4d4639', 'border_color': '#4d4639', 'valign': 'vcenter'}

FORMATS = {'QUESTION': {**BASE_FORMAT, **{'bold': True}},
           'HEADER': {**BASE_FORMAT, **{'align': 'center', 'bold': True, 'text_wrap': True, 'border': 1,
                                        'border_color': 'white', 'font_color': 'white', 'bg_color': '#5b4173'}},
           'VALUE': {**BASE_FORMAT, **{'align': 'right', 'border': 1}},
           'VALUE_TOTAL': {**BASE_FORMAT, **{'bold': True, 'align': 'right', 'border': 1}},
           'PERCENT': {**BASE_FORMAT, **{'align': 'right', 'border': 1, 'num_format': '0.0'}},
           'PERCENT_TOTAL': {**BASE_FORMAT, **{'bold': True, 'align': 'right', 'border': 1, 'num_format': '0.0'}},
           'OPTION': {**BASE_FORMAT, **{'border': 1, 'border_color': '#4d4639', 'text_wrap': True,
                                        'font_color': '#4d4639'}},
           'OPTION_TOTAL': {**BASE_FORMAT, **{'bold': True, 'border': 1,
                                              'text_wrap': True}},
           'SUBTITLE': {**BASE_FORMAT, **{'bold': True}},
           'POS_SQUARE': {**BASE_FORMAT, **{'bg_color': '#00a03c', 'border': 1}},
           'NEU_SQUARE': {**BASE_FORMAT, **{'bg_color': '#ffaa00', 'border': 1}},
           'NEG_SQUARE': {**BASE_FORMAT, **{'bg_color': '#fc1420', 'border': 1}},
           'IGNORE_SQUARE': {**BASE_FORMAT, **{'bg_color': '#9c9b8e', 'border': 1}},
           'LEVEL_TITLE': {**BASE_FORMAT, **{'bold': True, 'align': 'right', 'indent': 1}}}


# Picker logo
LOGO_PATH = r'C:\Users\steve.baker\Desktop\MAT Nonsense\picker2.png'

#Spacing
ROWS_AFTER_QUESTION = 4
