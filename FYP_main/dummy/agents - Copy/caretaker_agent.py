# agents/caretaker_agent.py
import os
import json
import random
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or None
MODEL = os.getenv("MODEL", "mistralai/mistral-7b-instruct:free")
BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")

class CaretakerAgent:
    """
    CaretakerAgent: holds (and supplies) ground-truth patient profiles.
    This DB (patient_caretaker_db.json) is used ONLY by Caretaker and Patient.
    """

    def __init__(self, patient_db_path="patient_caretaker_db.json"):
        self.path = patient_db_path
        self.db = self._load_patient_db()

    def _load_patient_db(self):
        if not os.path.exists(self.path):
            # create an empty list by default
            with open(self.path, "w") as f:
                json.dump([], f, indent=2)
            return []
        with open(self.path, "r") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("patient_caretaker_db.json must be a list of patient dicts")
                return data
            except Exception:
                # fallback to empty list
                return []

    def _call_llm(self, prompt):
        if not API_KEY:
            return None
        url = f"{BASE}/chat/completions"
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a factual caretaker assistant. Answer concisely."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=12)
            r.raise_for_status()
            j = r.json()
            return j["choices"][0]["message"]["content"]
        except Exception:
            return None

    def provide_new_patient(self):
        """
        Simulate caretaker sending a new patient profile.
        If DB has entries, pick one at random and return a nicely shaped dict containing required fields.
        If LLM available we could format the data, otherwise return dict from DB or a generated sample.
        """
        if len(self.db) == 0:
            # return a small generated sample profile
            sample = {
                "PatientName": "Arthur",
                "Age": 80,
                "Gender": "M",
                "Diagnosis": "Unknown",
                "Education_Level": "University Degree",
                "Breakfast_Today": "Oatmeal with blueberries",
                "Companion": "Daughter Sarah",
                "Contact": "N/A"
            }
            return sample

        raw = random.choice(self.db)
        # Ensure required keys exist (provide defaults if missing)
        profile = {
            "PatientName": raw.get("PatientName") or raw.get("name") or raw.get("Patient_Name") or "Unknown",
            "Age": raw.get("Age") or raw.get("age") or 0,
            "Gender": raw.get("Gender") or raw.get("gender") or "U",
            "Diagnosis": raw.get("Diagnosis") or raw.get("diagnosis") or "Unknown",
            "Education_Level": raw.get("Education_Level") or raw.get("education") or "Unknown",
            "Breakfast_Today": raw.get("Breakfast_Today") or raw.get("Breakfast_Today_Truth") or raw.get("breakfast") or "Unknown",
            "Companion": raw.get("Companion") or raw.get("companion") or "Unknown",
            "Contact": raw.get("Contact") or raw.get("contact") or "N/A"
        }
        return profile

    def get_patient_by_id(self, patient_id):
        # patient_id in this simple system will be stringified name + idx, but allow searching
        for p in self.db:
            if str(p.get("PatientID", "") ) == str(patient_id):
                return p
            # also allow PatientName match
            if str(p.get("PatientName", "")).lower() == str(patient_id).lower():
                return p
        return None
