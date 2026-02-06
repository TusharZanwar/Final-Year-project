class CaretakerInterview:
    def __init__(self):
        self.answers = {}
        self.summary = ""

class CognitiveSession:
    def __init__(self):
        self.qna = []          # [{"q":..., "a":..., "latency":...}]
        self.total_latency = []
        self.observations = ""

class PatientRecord:
    def __init__(self):
        self.profile = {}
        self.caretaker_interview = CaretakerInterview()
        self.cognitive_session = CognitiveSession()
