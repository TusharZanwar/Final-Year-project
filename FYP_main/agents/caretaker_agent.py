# agents/caretaker_agent.py
import os
import json
import random
import time
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
MODEL = os.getenv("MODEL", "mistralai/mistral-7b-instruct:free")

class CaretakerAgent:
    """
    Holds ground-truth patient facts (from patient_caretaker_db.json).
    Nurse will ask the Caretaker agent for patient details. The Caretaker responds
    using direct lookup and (optionally) an LLM to produce human-like utterances.
    """

    def __init__(self, db_path="patient_caretaker_db.json"):
        self.db_path = db_path
        self.db = self._load_patient_db()

    def _load_patient_db(self):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"{self.db_path} not found.")
        with open(self.db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("patient_caretaker_db.json must contain a list of patient records.")
        return data

    def provide_new_patient(self):
        """Simulate caretaker giving a new patient's profile.
           For the demo we pick a random patient from the db.
        """
        patient = random.choice(self.db)
        # produce a human-like message (LLM if API key present)
        utter = self._llm_describe_patient(patient, new_visit=True)
        # return both machine-readable dict and utterance
        return patient, utter

    def provide_patient_by_id(self, patient_id):
        for p in self.db:
            if str(p.get("PatientID")) == str(patient_id):
                utter = self._llm_describe_patient(p, new_visit=False)
                return p, utter
        return None, "RECORD NOT FOUND."

    def answer_question_about_patient(self, patient_id, question):
        p, _ = self.provide_patient_by_id(patient_id)
        if p is None:
            return "RECORD NOT FOUND."
        # Simple field lookup attempt
        q = question.lower()
        if "breakfast" in q:
            return p.get("Breakfast_Today", "RECORD NOT FOUND.")
        if "age" in q:
            return str(p.get("Age", "RECORD NOT FOUND."))
        if "education" in q:
            return p.get("Education", "RECORD NOT FOUND.")
        # fallback: call LLM to produce a human-like answer summarizing what's known
        return self._llm_describe_patient(p, new_visit=False)

    def _llm_describe_patient(self, patient, new_visit=True):
        if not OPENROUTER_API_KEY:
            # simple simulated sentence
            if new_visit:
                return f"Hello, I'm the caretaker. Patient {patient.get('Name')} (ID {patient.get('PatientID')}) came with {patient.get('Companion')}."
            else:
                return f"I can confirm {patient.get('Name')} is {patient.get('Age')} years old with diagnosis: {patient.get('Diagnosis')}."
        # Build a short system/user prompt
        prompt_system = (
            "You are a factual caretaker. Provide short conversational statements "
            "about the patient using the facts provided. Be brief and clear."
        )
        prompt_user = f"Facts: {json.dumps(patient)}\n\nPlease respond as the caretaker in 1-2 short sentences."
        try:
            resp = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": prompt_system},
                        {"role": "user", "content": prompt_user}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 200
                },
                timeout=15
            )
            j = resp.json()
            return j["choices"][0]["message"]["content"].strip()
        except Exception as e:
            # fallback sentence
            return f"[Caretaker simulator] patient {patient.get('Name')} (ID {patient.get('PatientID')}) - error contacting LLM: {e}"
