# agents/nurse_agent.py
import os
import json
import uuid
import time

class NurseAgent:
    """
    NurseAgent talks only to CaretakerAgent (not to user/patient).
    Responsibilities:
      - register_new_patient(patient_profile_from_caretaker)
      - register_returning(patient_id)
      - store nurse-provided / collected info in clinic DB (clinic_db.json)
    """

    def __init__(self, caretaker_agent, clinic_db_path="clinic_db.json"):
        self.caretaker = caretaker_agent
        self.clinic_db_path = clinic_db_path
        # ensure clinic DB exists
        if not os.path.exists(self.clinic_db_path):
            with open(self.clinic_db_path, "w") as f:
                json.dump({"patients": {}, "interactions": {}, "mmse_scores": {}, "reports": {}}, f, indent=2)

    def _read_db(self):
        with open(self.clinic_db_path, "r") as f:
            return json.load(f)

    def _write_db(self, data):
        with open(self.clinic_db_path, "w") as f:
            json.dump(data, f, indent=2)

    def _generate_patient_id(self):
        # create a short unique id
        return uuid.uuid4().hex[:8]

    def register_new_patient(self, raw_patient_data):
        """
        Called when caretaker sends a new patient profile.
        Nurse assigns a unique patient_id and stores the profile into clinic_db['patients'].
        Returns patient_id (string).
        """
        db = self._read_db()
        pid = self._generate_patient_id()
        # ensure minimal fields present
        patient_entry = {
            "PatientName": raw_patient_data.get("PatientName", "Unknown"),
            "Age": raw_patient_data.get("Age", 0),
            "Gender": raw_patient_data.get("Gender", "U"),
            "Diagnosis": raw_patient_data.get("Diagnosis", "Unknown"),
            "Education_Level": raw_patient_data.get("Education_Level", "Unknown"),
            "Breakfast_Today": raw_patient_data.get("Breakfast_Today", ""),
            "Companion": raw_patient_data.get("Companion", ""),
            "Contact": raw_patient_data.get("Contact", ""),
            "RegisteredAt": time.time()
        }
        db.setdefault("patients", {})[pid] = patient_entry
        db.setdefault("interactions", {})[pid] = []
        db.setdefault("mmse_scores", {})[pid] = []
        db.setdefault("reports", {})[pid] = {}
        self._write_db(db)

        # log nurse-caretaker exchange
        db["interactions"][pid].append({
            "type": "nurse_caretaker",
            "timestamp": time.time(),
            "caretaker_profile": raw_patient_data
        })
        self._write_db(db)
        return pid

    def register_returning(self, patient_id):
        """
        Called when a returning patient arrives. For now simply ensures patient exists and returns entry.
        """
        db = self._read_db()
        patient = db.get("patients", {}).get(patient_id)
        return patient

    def ask_caretaker(self, question, patient_id=None):
        """
        For completeness: nurse asks caretaker a question (returns the caretaker answer).
        This function expects caretaker agent to have some LLM capabilities; nurse routes question through caretaker.
        """
        # this is a thin wrapper - main code uses caretaker.provide_new_patient() directly usually
        return self.caretaker.get_patient_by_id(patient_id) if patient_id else None
