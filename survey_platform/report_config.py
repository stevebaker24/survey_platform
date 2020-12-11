# Frequency Table Format
BASE_FORMAT = {'font_name': 'Arial', 'font_color': '#4d4639', 'border_color': '#4d4639', 'valign': 'vcenter'}

FORMATS = {'QUESTION': {**BASE_FORMAT, **{'bold': True}},
           'HEADER': {**BASE_FORMAT, **{'align': 'center', 'bold': True, 'border': 1,
                                        'border_color': 'white', 'font_color': 'white', 'bg_color': '#5b4173',
                                        'text_wrap': True}},
           'VALUE': {**BASE_FORMAT, **{'align': 'right', 'border': 1}},
           'VALUE_TOTAL': {**BASE_FORMAT, **{'bold': True, 'align': 'right', 'border': 1}},
           'PERCENT': {**BASE_FORMAT, **{'align': 'right', 'border': 1, 'num_format': '0.0'}},
           'PERCENT_TOTAL': {**BASE_FORMAT, **{'bold': True, 'align': 'right', 'border': 1, 'num_format': '0.0'}},
           'OPTION': {**BASE_FORMAT, **{'border': 1, 'border_color': '#4d4639', 'text_wrap': True,
                                        'font_color': '#4d4639'}},
           'OPTION_TOTAL': {**BASE_FORMAT, **{'bold': True, 'border': 1,
                                              'text_wrap': True}},
           'TARGETED_HEADER': {**BASE_FORMAT, **{'bold': True, 'font_size': 20}},
           'SUBTITLE': {**BASE_FORMAT, **{'bold': True}},
           'POS_SQUARE': {**BASE_FORMAT, **{'bg_color': '#00a03c', 'border': 1}},
           'NEU_SQUARE': {**BASE_FORMAT, **{'bg_color': '#ffaa00', 'border': 1}},
           'NEG_SQUARE': {**BASE_FORMAT, **{'bg_color': '#fc1420', 'border': 1}},
           'IGNORE_SQUARE': {**BASE_FORMAT, **{'bg_color': '#9c9b8e', 'border': 1}},
           'LEVEL_TITLE': {**BASE_FORMAT, **{'bold': True, 'align': 'right', 'indent': 1, 'text_wrap': True}},
           'RAG_POS': {**BASE_FORMAT,
                       **{'font_color': '#ffffff', 'bg_color': '#00a03c', 'border': 1, 'num_format': '0%'}},
           'RAG_NEU': {**BASE_FORMAT,
                       **{'font_color': '#000000', 'bg_color': '#ffaa00', 'border': 1, 'num_format': '0%',
                          'align': 'center'}},
           'RAG_NEG': {**BASE_FORMAT,
                       **{'font_color': '#ffffff', 'bg_color': '#fc1420', 'border': 1, 'num_format': '0%'}},
           'RAG_SUPP': {**BASE_FORMAT, **{'font_color': '#000000', 'bg_color': '#ffffff', 'border': 1}},
           'RAG_Q_TEXT': {**BASE_FORMAT, **{'align': 'left', 'border': 1,

                                            'text_wrap': True, 'indent': 1}},
           'RAG_Q_NUM': {**BASE_FORMAT, **{'align': 'center', 'text_wrap': True, 'border': 1,
                                           }},
           'SET_PERCENT': {**BASE_FORMAT, **{'align': 'center', 'border': 2, 'bold': True, 'font_color': '#5b4173',
                                             'border_color': '#5b4173'
                                             }},
           'RAG_GUIDANNCE': {**BASE_FORMAT, **{'text_wrap': True}},
           'RAG_GUIDANNCE_BOLD': {**BASE_FORMAT, **{'text_wrap': True, 'bold': True}},
           'SES_POS': {**BASE_FORMAT,
                       **{'font_color': '#ffffff', 'bg_color': '#00a03c', 'border': 1, 'num_format': '0.0'}},
           'SES_NEU': {**BASE_FORMAT,
                       **{'font_color': '#000000', 'bg_color': '#ffaa00', 'border': 1, 'num_format': '0.0',
                          'align': 'center'}},
           'SES_NEG': {**BASE_FORMAT,
                       **{'font_color': '#ffffff', 'bg_color': '#fc1420', 'border': 1, 'num_format': '0.0'}},
           'RAG_CMP': {**BASE_FORMAT,
                       **{'font_color': '#000000', 'bg_color': '#cbbba0', 'border': 1, 'num_format': '0%',
                          'align': 'center'}},
           'RAG_SET_POINT_TEXT': {**BASE_FORMAT, **{'bold': True, 'align': 'center'}},
           'SES_CMP': {**BASE_FORMAT,
                       **{'font_color': '#000000', 'bg_color': '#cbbba0', 'border': 1, 'num_format': '0.0',
                          'align': 'center'}}
           }

# Picker logo
LOGO_PATH = r'C:\Users\steve.baker\Desktop\MAT Nonsense\picker.png'

# Spacing
ROWS_AFTER_QUESTION = 4

# Header row height
HEADER_ROW_HEIGHT = 45
