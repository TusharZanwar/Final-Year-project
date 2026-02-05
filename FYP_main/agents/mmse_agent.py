# # agents/mmse_agent.py
# import os
# import json
# import time
# import requests
# from dotenv import load_dotenv

# load_dotenv()
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# OPENROUTER_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
# MODEL = os.getenv("MODEL", "mistralai/mistral-7b-instruct:free")

# # a short set of MMSE-style questions for demo
# STANDARD_MMSE_QUESTIONS = [
#     "What is the year today?",
#     "What is the season right now?",
#     "Please repeat these words after me: apple, table, penny.",
#     "Please recall the three words I asked you to remember earlier.",
#     "What is 100 minus 7?",
#     "What is the name of the place we are in (clinic)?"
# ]

# class MMSEAgent:
#     """
#     Conducts a simplified MMSE using the PatientAgent.
#     It pulls some items from clinic DB (e.g., known patient facts) to ask personalised questions.
#     Results get written to clinic_db_path under mmse_scores and interactions.
#     """

#     def __init__(self, clinic_db_path="clinic_db.json"):
#         self.clinic_db_path = clinic_db_path

#     def _load_clinic_db(self):
#         with open(self.clinic_db_path, "r", encoding="utf-8") as f:
#             return json.load(f)

#     def _save_clinic_db(self, data):
#         with open(self.clinic_db_path, "w", encoding="utf-8") as f:
#             json.dump(data, f, indent=2)

#     def _ask_patient(self, patient_agent, q):
#         # print visible question
#         print(f"\n[MMSE → Patient] {q}")
#         start = time.perf_counter()
#         answer = patient_agent.answer_question(q)
#         end = time.perf_counter()
#         latency = round(end - start, 2)
#         print(f"[Patient → MMSE] {answer}  (latency: {latency}s)")
#         return answer, latency

#     def conduct_mmse_test(self, patient_agent, patient_id):
#         clinic = self._load_clinic_db()
#         # ensure patient record exists
#         clinic.setdefault("mmse_scores", {})
#         clinic.setdefault("interactions", {})
#         clinic.setdefault("patients", {})

#         patient_meta = clinic["patients"].get(patient_id, {})
#         # Prepare test: mix standard questions plus some derived from nurse data if available
#         questions = STANDARD_MMSE_QUESTIONS.copy()
#         # if nurse stored 'Breakfast' or 'Companion', ask about them
#         if patient_meta.get("Breakfast_Today"):
#             questions.insert(0, "What did you eat for breakfast today?")
#         if patient_meta.get("Companion"):
#             questions.insert(1, "Who accompanied you to the clinic today?")

#         result = {
#             "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
#             "patient_id": patient_id,
#             "qa_pairs": [],
#             "recall_count": 0,
#             "avg_latency": 0.0
#         }

#         latencies = []
#         recall_words = []
#         # we'll track the three words in step where we asked the patient to remember them
#         remembered_words = []

#         for q in questions:
#             ans, latency = self._ask_patient(patient_agent, q)
#             latencies.append(latency)
#             result["qa_pairs"].append({"question": q, "answer": ans, "latency": latency})
#             # simple scoring rules:
#             if "recall" in q.lower() and "apple" in (ans or "").lower():
#                 # patient managed to recall at least one expected word
#                 # count words present
#                 count = sum(1 for w in ["apple","table","penny"] if w in (ans or "").lower())
#                 result["recall_count"] = count
#             # capture personalized fields: if we asked breakfast and answer matches, store match
#             if "breakfast" in q.lower() and patient_meta.get("Breakfast_Today"):
#                 if patient_meta["Breakfast_Today"].lower() in (ans or "").lower():
#                     clinic["patients"].setdefault(patient_id, {}).setdefault("validation", {})["breakfast_match"] = True
#                 else:
#                     clinic["patients"].setdefault(patient_id, {}).setdefault("validation", {})["breakfast_match"] = False

#         # finalize
#         result["avg_latency"] = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

#         # append into clinic DB
#         clinic["mmse_scores"].setdefault(patient_id, []).append(result)
#         clinic["interactions"].setdefault(patient_id, []).extend(result["qa_pairs"])
#         # optionally store a simple mmse_score field in patients
#         clinic["patients"].setdefault(patient_id, {})["last_mmse_recall"] = result["recall_count"]
#         clinic["patients"].setdefault(patient_id, {})["last_mmse_avg_latency"] = result["avg_latency"]

#         self._save_clinic_db(clinic)
#         return result






# agents/mmse_agent.py
import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
MODEL = os.getenv("MODEL", "mistralai/mistral-7b-instruct:free")

# a short set of MMSE-style questions for demo
STANDARD_MMSE_QUESTIONS = [
    "What is the year today?",
    "What is the season right now?",
    "Please repeat these words after me: apple, table, penny.",
    "What is 100 minus 7?",
    "What is the name of the place we are in (clinic)?",
    "Please recall the three words I asked you to remember earlier.",
    "Can you subtract 7 again from that number?",
    "Spell the word WORLD backwards."
]

class MMSEAgent:
    """
    Conducts a simplified MMSE using the PatientAgent.
    It pulls some items from clinic DB (e.g., known patient facts) to ask personalised questions.
    Results get written to clinic_db_path under mmse_scores and interactions.
    """

    def __init__(self, clinic_db_path="clinic_db.json"):
        self.clinic_db_path = clinic_db_path

    def _load_clinic_db(self):
        with open(self.clinic_db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_clinic_db(self, data):
        with open(self.clinic_db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _ask_patient(self, patient_agent, q):
        # print visible question
        print(f"\n[MMSE → Patient] {q}")
        
        # Call the patient agent
        # EXPECTED RETURN: (text_reply, latency_value)
        raw_response = patient_agent.answer_question(q)
        
        # UNPACK TUPLE SAFELY
        if isinstance(raw_response, tuple):
            answer_text = raw_response[0]
            latency = raw_response[1]
        else:
            answer_text = str(raw_response)
            latency = 0.0

        print(f"[Patient → MMSE] {answer_text}  (latency: {latency}s)")
        return answer_text, latency

    def conduct_mmse_test(self, patient_agent, patient_id):
        clinic = self._load_clinic_db()
        # ensure patient record exists
        clinic.setdefault("mmse_scores", {})
        clinic.setdefault("interactions", {})
        clinic.setdefault("patients", {})

        patient_meta = clinic["patients"].get(patient_id, {})
        # Prepare test: mix standard questions plus some derived from nurse data if available
        questions = STANDARD_MMSE_QUESTIONS.copy()
        
        # if nurse stored 'Breakfast' or 'Companion', ask about them
        if patient_meta.get("Breakfast_Today"):
            questions.insert(0, "What did you eat for breakfast today?")
        if patient_meta.get("Companion"):
            questions.insert(1, "Who accompanied you to the clinic today?")

        result = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "patient_id": patient_id,
            "qa_pairs": [],
            "recall_count": 0,
            "avg_latency": 0.0
        }

        latencies = []
        
        for q in questions:
            # THIS CALL NOW RETURNS CLEAN TEXT AND LATENCY
            ans, latency = self._ask_patient(patient_agent, q)
            
            latencies.append(latency)
            result["qa_pairs"].append({"question": q, "answer": ans, "latency": latency})
            
            # SCORING LOGIC
            # Now 'ans' is strictly a string, so .lower() works fine
            if "recall" in q.lower():
                # Check for the 3 words
                count = 0
                for w in ["apple", "table", "penny"]:
                    if w in (ans or "").lower():
                        count += 1
                result["recall_count"] = count

            # BREAKFAST VALIDATION LOGIC
            if "breakfast" in q.lower() and patient_meta.get("Breakfast_Today"):
                expected_bf = patient_meta["Breakfast_Today"].lower()
                actual_ans = (ans or "").lower()
                # Simple check if the main word is in the answer
                if expected_bf in actual_ans or any(word in actual_ans for word in expected_bf.split()):
                    clinic["patients"].setdefault(patient_id, {}).setdefault("validation", {})["breakfast_match"] = True
                else:
                    clinic["patients"].setdefault(patient_id, {}).setdefault("validation", {})["breakfast_match"] = False

        # finalize
        result["avg_latency"] = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

        # append into clinic DB
        clinic["mmse_scores"].setdefault(patient_id, []).append(result)
        clinic["interactions"].setdefault(patient_id, []).extend(result["qa_pairs"])
        
        # optionally store a simple mmse_score field in patients
        clinic["patients"].setdefault(patient_id, {})["last_mmse_recall"] = result["recall_count"]
        clinic["patients"].setdefault(patient_id, {})["last_mmse_avg_latency"] = result["avg_latency"]

        self._save_clinic_db(clinic)
        return result