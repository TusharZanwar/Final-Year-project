# agents/nurse_agent.py
import os
import json
import time
import uuid

class NurseAgent:
    """
    Nurse interacts with CaretakerAgent only to obtain patient facts.
    Nurse stores those facts into clinic_db.json and assigns a unique patient ID.
    Nurse does not interact with Patient directly.
    """

    def __init__(self, caretaker_agent, clinic_db_path="clinic_db.json"):
        self.caretaker = caretaker_agent
        self.clinic_db_path = clinic_db_path
        # ensure clinic DB exists (caller should create it)
        if not os.path.exists(self.clinic_db_path):
            raise FileNotFoundError("Clinic DB not found: " + clinic_db_path)

    def _load_clinic(self):
        with open(self.clinic_db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_clinic(self, data):
        with open(self.clinic_db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def register_new_patient(self, raw_patient_data):
        """
        raw_patient_data: (dict, utterance)
        raw_patient_data returned by caretaker_agent.provide_new_patient() is (patient_dict, utterance)
        returns assigned patient_id (string)
        """
        if isinstance(raw_patient_data, tuple) and len(raw_patient_data) == 2:
            pdata, utter = raw_patient_data
        else:
            pdata = raw_patient_data
            utter = None

        # display human-like exchange
        print("\n[Nurse → Caretaker] Do you have a new patient record for me?")
        time.sleep(0.6)
        print(f"[Caretaker → Nurse] {utter or 'Providing patient facts.'}")
        time.sleep(0.6)

        # assign a new unique clinic patient id
        clinic = self._load_clinic()
        # generate deterministic ID: use provided PatientID if available, else generate uuid
        provided_pid = str(pdata.get("PatientID") or pdata.get("ID") or "")
        if provided_pid:
            pid = provided_pid
        else:
            pid = "C-" + uuid.uuid4().hex[:8]

        # store into clinic DB under patients
        clinic.setdefault("patients", {})
        # ensure keys present and copy only allowed fields
        clinic["patients"][pid] = {
            "Name": pdata.get("Name"),
            "Age": pdata.get("Age"),
            "Education": pdata.get("Education"),
            "Diagnosis": pdata.get("Diagnosis"),
            "Breakfast_Today": pdata.get("Breakfast_Today"),
            "Companion": pdata.get("Companion"),
            "Notes": pdata.get("Notes"),
            "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        # ensure structures
        clinic.setdefault("interactions", {})
        clinic.setdefault("mmse_scores", {})
        clinic.setdefault("reports", {})

        self._save_clinic(clinic)
        return pid

    def ask_caretaker_for_field(self, patient_id, field):
        # nurse asks caretaker about some field of a patient
        print(f"\n[Nurse → Caretaker] Please confirm '{field}' for patient ID {patient_id}.")
        ans = self.caretaker.answer_question_about_patient(patient_id, f"What is the patient's {field}?")
        print(f"[Caretaker → Nurse] {ans}")
        return ans

    def register_new_patient_human(self):
        print("\n[Nurse] Please enter patient details:")

        pdata = {
            "Name": input("Name: "),
            "Age": int(input("Age: ")),
            "Education": input("Education: "),
            "Breakfast_Today": input("Breakfast Today: "),
            "Companion": input("Companion: "),
            "Notes": None
        }

        print("[Human → Nurse] Patient information recorded.")
        return self.register_new_patient((pdata, "Human provided patient data"))
