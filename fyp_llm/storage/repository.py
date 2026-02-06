from storage.serializers import save_json

def save_session(patient_record, session_id):
    save_json(f"data/sessions/{session_id}.json", patient_record.__dict__)
