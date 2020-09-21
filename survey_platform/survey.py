class Survey:

    def __init__(self, name, survey_type, questions_path, responses_path, sample_path):
        self.name = name
        self.survey_type = survey_type
        self.questions = Questions(questions_path)
        self.sample = Sample(sample_path)
        self.responses = Responses(responses_path)
        self.combined = Combined(self.sample, self.responses, self.questions)
        self.reporting = Reporting(self.combined, self.questions)