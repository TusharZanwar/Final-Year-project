# # main.py

# import os
# import json
# from dotenv import load_dotenv

# load_dotenv()

# # === IMPORT AGENTS ===
# from agents.patient_agent import PatientAgent
# from agents.caretaker_agent import CaretakerAgent
# from agents.mmse_agent import MMSEAgent
# from agents.analyzer_agent import AnalyzerAgent
# from agents.nurse_agent import NurseAgent


# # === DATABASE PATHS ===
# PATIENT_CARETAKER_DB = "patient_caretaker_db.json"   # only caretaker + patient use this
# CLINIC_DB = "clinic_db.json"                         # nurse, mmse, analyzer use this


# # -----------------------------------------------------------
# #               DB HELPERS
# # -----------------------------------------------------------

# def ensure_db(path, template):
#     if not os.path.exists(path):
#         with open(path, "w") as f:
#             json.dump(template, f, indent=2)
#         print(f"[DB] Created {path}")

# def load_db(path):
#     with open(path, "r") as f:
#         return json.load(f)

# def save_db(path, data):
#     with open(path, "w") as f:
#         json.dump(data, f, indent=2)


# # -----------------------------------------------------------
# #               DB STRUCTURES
# # -----------------------------------------------------------

# PATIENT_CARETAKER_TEMPLATE = []   # list of patient dicts

# CLINIC_DB_TEMPLATE = {
#     "patients": {},          # patientID → dict
#     "interactions": {},      # conversation logs
#     "mmse_scores": {},       # list of tests
#     "reports": {}            # report text
# }


# # -----------------------------------------------------------
# #                   MAIN APP
# # -----------------------------------------------------------

# def main():

#     ensure_db(PATIENT_CARETAKER_DB, PATIENT_CARETAKER_TEMPLATE)
#     ensure_db(CLINIC_DB, CLINIC_DB_TEMPLATE)

#     clinic_db = load_db(CLINIC_DB)

#     # ---------------- CREATE AGENTS ----------------
#     caretaker = CaretakerAgent(PATIENT_CARETAKER_DB)
#     patient_agent = PatientAgent(PATIENT_CARETAKER_DB)
#     mmse_agent = MMSEAgent(CLINIC_DB)
#     analyzer = AnalyzerAgent(CLINIC_DB)

#     nurse = NurseAgent(
#         caretaker_agent=caretaker,
#         clinic_db_path=CLINIC_DB
#     )

#     print("""
# =================== Alzheimer’s Multi-Agent System ===================
# Commands:
#   new        → new patient visit (Nurse ↔ Caretaker)
#   return     → load an existing patient
#   mmse       → run MMSE test (Patient ↔ MMSE)
#   report     → generate analyzer report
#   exit       → quit
# ======================================================================
# """)

#     current_patient_id = None

#     # ====================== LOOP ======================
#     while True:

#         cmd = input("\nCommand → ").strip().lower()

#         # =====================================================
#         # NEW PATIENT VISIT
#         # =====================================================
#         if cmd == "new":
#             print("\n[Nurse] Requesting new patient from Caretaker...\n")

#             patient_data = caretaker.provide_new_patient()

#             print("[Caretaker → Nurse] Sending patient profile.")

#             current_patient_id = nurse.register_new_patient(patient_data)

#             print(f"[System] Registered new patient with ID: {current_patient_id}")

#             clinic_db = load_db(CLINIC_DB)
#             save_db(CLINIC_DB, clinic_db)

#         # =====================================================
#         # RETURNING PATIENT
#         # =====================================================
#         elif cmd == "return":
#             pid = input("Enter existing clinic patient ID: ").strip()

#             clinic_db = load_db(CLINIC_DB)
#             if pid not in clinic_db["patients"]:
#                 print("❌ No such patient.")
#                 continue

#             current_patient_id = pid
#             name = clinic_db["patients"][pid].get("Name", "Unknown")
#             print(f"[System] Loaded patient {pid} ({name}).")

#         # =====================================================
#         # RUN MMSE TEST
#         # =====================================================
#         elif cmd == "mmse":
#             if not current_patient_id:
#                 print("❌ No patient selected. Use 'new' or 'return'.")
#                 continue

#             print(f"\n[MMSE] Conducting MMSE for clinic patient {current_patient_id}\n")

#             # FIX HERE — pass the full patient object, not the ID
#             clinic_db = load_db(CLINIC_DB)
#             patient_obj = clinic_db["patients"][current_patient_id]

#             patient_agent.set_patient(patient_obj)

#             result = mmse_agent.conduct_mmse_test(patient_agent, current_patient_id)

#             clinic_db = load_db(CLINIC_DB)
#             clinic_db["mmse_scores"].setdefault(current_patient_id, []).append(result)
#             save_db(CLINIC_DB, clinic_db)

#             print("[MMSE] Completed and saved.")

#         # =====================================================
#         # ANALYZER REPORT
#         # =====================================================
#         elif cmd == "report":
#             if not current_patient_id:
#                 print("❌ No active patient.")
#                 continue

#             report = analyzer.generate_patient_report(current_patient_id)

#             clinic_db = load_db(CLINIC_DB)
#             clinic_db["reports"][current_patient_id] = report
#             save_db(CLINIC_DB, clinic_db)

#             print("\n========== AI ANALYZER REPORT ==========\n")
#             print(report)
#             print("\n========================================")

#         # =====================================================
#         # EXIT
#         # =====================================================
#         elif cmd == "exit":
#             print("Exiting. Clinic DB saved.")
#             break

#         else:
#             print("Unknown command.")


# # -----------------------------------------------------------
# if __name__ == "__main__":
#     main()





# main.py

import os
import json
from dotenv import load_dotenv

load_dotenv()

# === IMPORT AGENTS ===
from agents.patient_agent import PatientAgent
from agents.caretaker_agent import CaretakerAgent
from agents.mmse_agent import MMSEAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.nurse_agent import NurseAgent


# === DATABASE PATHS ===
PATIENT_CARETAKER_DB = "patient_caretaker_db.json"   # only caretaker + patient use this
CLINIC_DB = "clinic_db.json"                         # nurse, mmse, analyzer use this


# -----------------------------------------------------------
#               DB HELPERS
# -----------------------------------------------------------

def ensure_db(path, template):
    """Creates the DB file with template data if it doesn't exist."""
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(template, f, indent=2)
        print(f"[DB] Created {path}")

def load_db(path):
    with open(path, "r") as f:
        return json.load(f)

def save_db(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# -----------------------------------------------------------
#               DB STRUCTURES
# -----------------------------------------------------------

# FIX: Added seed data so the Caretaker doesn't crash on an empty list
PATIENT_CARETAKER_TEMPLATE = [
    {
        "PatientID": "P1001",
        "Name": "Arthur",
        "Age": 80,
        "Education": "University Degree",
        "Diagnosis": "MCI",
        "Breakfast_Today": "Oatmeal with blueberries",
        "Companion": "Daughter Sarah",
        "KnownConditions": ["Hypertension", "MCI"]
    },
    {
        "PatientID": "P1002",
        "Name": "Betty",
        "Age": 76,
        "Education": "High School",
        "Diagnosis": "MCI",
        "Breakfast_Today": "Toast and tea",
        "Companion": "Husband John",
        "KnownConditions": ["Arthritis", "MCI"]
    }
]

CLINIC_DB_TEMPLATE = {
    "patients": {},          # patientID → dict
    "interactions": {},      # conversation logs
    "mmse_scores": {},       # list of tests
    "reports": {}            # report text
}


# -----------------------------------------------------------
#                   MAIN APP
# -----------------------------------------------------------

def main():

    # 1. Ensure databases exist with the templates above
    ensure_db(PATIENT_CARETAKER_DB, PATIENT_CARETAKER_TEMPLATE)
    ensure_db(CLINIC_DB, CLINIC_DB_TEMPLATE)

    # 2. Initialize Agents
    caretaker = CaretakerAgent(PATIENT_CARETAKER_DB)
    patient_agent = PatientAgent(PATIENT_CARETAKER_DB)
    mmse_agent = MMSEAgent(CLINIC_DB)
    analyzer = AnalyzerAgent(CLINIC_DB)

    nurse = NurseAgent(
        caretaker_agent=caretaker,
        clinic_db_path=CLINIC_DB
    )

    print("""
=================== Alzheimer’s Multi-Agent System ===================
Commands:
  new        → new patient visit (Nurse ↔ Caretaker)
  return     → load an existing patient
  mmse       → run MMSE test (Patient ↔ MMSE)
  report     → generate analyzer report
  exit       → quit
======================================================================
""")

    current_patient_id = None

    # ====================== LOOP ======================
    while True:

        cmd = input("\nCommand → ").strip().lower()

        # =====================================================
        # NEW PATIENT VISIT
        # =====================================================
        if cmd == "new":
            mode = input("Choose patient mode: (1) Simulation  (2) Human → ").strip()

            if mode == "2":
                # Human provides patient details directly to Nurse
                current_patient_id = nurse.register_new_patient_human()
            else:
                print("\n[Nurse] Requesting new patient from Caretaker...\n")

                patient_data, utterance = caretaker.provide_new_patient()
                print(f"[Caretaker → Nurse] Sending patient profile.")

                current_patient_id = nurse.register_new_patient((patient_data, utterance))

            print(f"[System] Registered new patient with ID: {current_patient_id}")

            clinic_db = load_db(CLINIC_DB)
            save_db(CLINIC_DB, clinic_db)


        # =====================================================
        # RETURNING PATIENT
        # =====================================================
        elif cmd == "return":
            pid = input("Enter existing clinic patient ID: ").strip()

            clinic_db = load_db(CLINIC_DB)
            if pid not in clinic_db["patients"]:
                print("❌ No such patient.")
                continue

            current_patient_id = pid
            name = clinic_db["patients"][pid].get("Name", "Unknown")
            print(f"[System] Loaded patient {pid} ({name}).")

        # =====================================================
        # RUN MMSE TEST
        # =====================================================
        elif cmd == "mmse":
            if not current_patient_id:
                print("❌ No patient selected. Use 'new' or 'return'.")
                continue
            print(f"\n[MMSE] Conducting MMSE for clinic patient {current_patient_id}\n")

            clinic_db = load_db(CLINIC_DB)
            patient_obj = clinic_db["patients"][current_patient_id]

            mode = input("Choose MMSE mode: (1) Simulated Patient  (2) Human Patient → ").strip()

            if mode == "2":
                from agents.human_interface import HumanInterface
                patient_source = HumanInterface()
            else:
                patient_agent.set_patient(patient_obj)
                patient_source = patient_agent

            result = mmse_agent.conduct_mmse_test(patient_source, current_patient_id)

            clinic_db = load_db(CLINIC_DB)
            clinic_db["mmse_scores"].setdefault(current_patient_id, []).append(result)
            save_db(CLINIC_DB, clinic_db)

            print("[MMSE] Completed and saved.")


        # =====================================================
        # ANALYZER REPORT
        # =====================================================
        elif cmd == "report":
            if not current_patient_id:
                print("❌ No active patient.")
                continue

            report = analyzer.generate_patient_report(current_patient_id)

            clinic_db = load_db(CLINIC_DB)
            clinic_db["reports"][current_patient_id] = report
            save_db(CLINIC_DB, clinic_db)

            #print("\n========== AI ANALYZER REPORT ==========\n")
            print(report)
            print("\n========================================")

        # =====================================================
        # EXIT
        # =====================================================
        elif cmd == "exit":
            print("Exiting. Clinic DB saved.")
            break

        else:
            print("Unknown command.")


# -----------------------------------------------------------
if __name__ == "__main__":
    main()