# agents/patient_agent.py
import os
import json
import requests
from dotenv import load_dotenv
import time

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or None
MODEL = os.getenv("MODEL", "mistralai/mistral-7b-instruct:free")
BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")

class PatientAgent:
    """
    PatientAgent responds to MMSE questions using LLM, seeded with patient's static profile
    from patient_caretaker_db.json. PatientAgent must be told which patient to act as via
    set_current_patient(patient_id) or set_current_profile(profile_dict).
    """

    def __init__(self, patient_db_path="patient_caretaker_db.json"):
        self.db_path = patient_db_path
        self._load_db()
        self.current_profile = None

    def _load_db(self):
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump([], f, indent=2)
        with open(self.db_path, "r") as f:
            try:
                self.db = json.load(f)
            except Exception:
                self.db = []

    def set_current_patient(self, patient_id):
        # find by PatientName or PatientID
        for p in self.db:
            if str(p.get("PatientID", "") ) == str(patient_id):
                self.current_profile = p
                return True
            if str(p.get("PatientName", "")).lower() == str(patient_id).lower():
                self.current_profile = p
                return True
        # if not found, allow patient_id to be a full profile dict
        if isinstance(patient_id, dict):
            self.current_profile = patient_id
            return True
        return False

    def _call_llm(self, system_prompt, user_prompt):
        if not API_KEY:
            return None
        url = f"{BASE}/chat/completions"
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=12)
            r.raise_for_status()
            j = r.json()
            return j["choices"][0]["message"]["content"]
        except Exception:
            return None

    def answer_question(self, question):
        """
        Return patient's answer string. If LLM available, use it with the patient's profile.
        Otherwise produce a deterministic/simple simulated response.
        """
        if not self.current_profile:
            return "I don't know who I am."

        system_prompt = (
            f"You are role-playing a patient named {self.current_profile.get('PatientName','Patient')}, "
            f"age {self.current_profile.get('Age','?')}, diagnosed: {self.current_profile.get('Diagnosis','Unknown')}. "
            "Answer questions naturally, using short sentences. If unsure, say 'I don't remember'."
        )

        user_prompt = f"Question: {question}\nAnswer naturally as the patient."

        llm_reply = self._call_llm(system_prompt, user_prompt)
        if llm_reply:
            return llm_reply.strip()

        # fallback deterministic answer generation using known facts if question mentions them:
        qlow = question.lower()
        if "breakfast" in qlow:
            return str(self.current_profile.get("Breakfast_Today", "I don't remember."))
        if "age" in qlow:
            return str(self.current_profile.get("Age", "I don't remember."))
        if "name" in qlow:
            return str(self.current_profile.get("PatientName", "I don't remember."))
        # default placeholder
        return "I don't remember exactly, sorry."
