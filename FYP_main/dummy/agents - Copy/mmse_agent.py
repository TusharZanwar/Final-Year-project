# agents/mmse_agent.py
import os
import json
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or None
MODEL = os.getenv("MODEL", "mistralai/mistral-7b-instruct:free")
BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")

class MMSEAgent:
    """
    Conducts a simple MMSE-like recall test (3-word recall + a few orientation q's).
    MMSEAgent reads clinic DB for nurse-provided facts and writes results in clinic DB.
    """

    def __init__(self, clinic_db_path="clinic_db.json"):
        self.clinic_db_path = clinic_db_path
        if not os.path.exists(self.clinic_db_path):
            with open(self.clinic_db_path, "w") as f:
                json.dump({"patients": {}, "interactions": {}, "mmse_scores": {}, "reports": {}}, f, indent=2)

    def _call_llm(self, prompt):
        if not API_KEY:
            return None
        url = f"{BASE}/chat/completions"
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"model": MODEL, "messages": [{"role":"system","content":"You are a polite MMSE clinician."},{"role":"user","content":prompt}], "temperature": 0.2}
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=12)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            return None

    def read_clinic_db(self):
        with open(self.clinic_db_path, "r") as f:
            return json.load(f)

    def write_clinic_db(self, data):
        with open(self.clinic_db_path, "w") as f:
            json.dump(data, f, indent=2)

    def conduct_mmse_test(self, patient_agent, patient_id):
        """
        Steps:
         - use nurse-provided facts from clinic_db to enrich questions
         - run 3-word memory: tell patient words, wait, ask recall
         - ask 2-3 orientation questions (some may be nurse-supplied facts)
         - compute simple recall score and store result in clinic_db["mmse_scores"][patient_id]
        """
        # ensure patient_agent set_current_patient
        patient_agent.set_current_patient(patient_id)

        clinic = self.read_clinic_db()
        patient_record = clinic["patients"].get(patient_id, {})
        # words to remember (fixed list)
        words = ["apple", "table", "penny"]

        # Step 1: instruct patient (LLM or local message)
        prompt = f"Tell patient to remember these words: {words}. Use short instruction."
        self._call_llm(prompt)  # we don't really need reply; mostly to record step with LLM

        time.sleep(2)  # simulate pause

        # Step 2: ask recall
        start = time.perf_counter()
        response = patient_agent.answer_question(f"Please recall the words I previously told you to remember: {words}")
        end = time.perf_counter()
        latency = round(end - start, 2)

        recall_score = 0
        lower = (response or "").lower()
        for w in words:
            if w in lower:
                recall_score += 1

        # Step 3: ask 2 short orientation questions, one of them can be from nurse-recorded facts
        qna = []
        orientation_questions = [
            "What year is it?",
            f"What is your companion's name?"  # this is likely in patient_caretaker DB and nurse copied it to clinic db
        ]
        for q in orientation_questions:
            ans = patient_agent.answer_question(q)
            qna.append({"question": q, "answer": ans})

        # build result object
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "words": words,
            "response": response,
            "recall_score": recall_score,
            "latency": latency,
            "orientation": qna
        }

        # save to clinic db
        clinic.setdefault("mmse_scores", {})
        clinic["mmse_scores"].setdefault(patient_id, []).append(result)
        # also store interaction logs
        clinic.setdefault("interactions", {})
        clinic["interactions"].setdefault(patient_id, []).append({
            "type": "mmse",
            "timestamp": result["timestamp"],
            "qna": [{"question": f"Recall words {words}", "answer": response}] + qna
        })

        self.write_clinic_db(clinic)
        return result
