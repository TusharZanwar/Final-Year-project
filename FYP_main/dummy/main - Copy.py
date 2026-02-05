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
PATIENT_CARETAKER_DB = "patient_caretaker_db.json"   # used ONLY by patient + caretaker
CLINIC_DB = "clinic_db.json"                         # used by nurse, mmse, analyzer


# -----------------------------------------------------------
#                DATABASE HELPERS
# -----------------------------------------------------------

def ensure_db(path, template):
    """Create DB if missing."""
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(template, f, indent=2)
        print(f"[DB] Created {path}")


def load_db(path):
    """Load JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def save_db(path, data):
    """Save JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# -----------------------------------------------------------
#                 DATABASE STRUCTURES
# -----------------------------------------------------------

PATIENT_CARETAKER_TEMPLATE = []   # a LIST of patients, each patient = dict of static info from caretaker

CLINIC_DB_TEMPLATE = {
    "patients": {},      # patientID → dynamic info filled by nurse
    "interactions": {},  # patientID → conversation logs
    "mmse_scores": {},   # patientID → list of mmse attempts
    "reports": {}        # patientID → analyzer reports
}


# -----------------------------------------------------------
#                     MAIN APPLICATION
# -----------------------------------------------------------

def main():

    # MAKE SURE DB FILES EXIST
    ensure_db(PATIENT_CARETAKER_DB, PATIENT_CARETAKER_TEMPLATE)
    ensure_db(CLINIC_DB, CLINIC_DB_TEMPLATE)

    # LOAD DBs
    clinic_db = load_db(CLINIC_DB)

    # -------------------------------------------------------
    #                INITIALIZE AGENTS
    # -------------------------------------------------------

    caretaker = CaretakerAgent(PATIENT_CARETAKER_DB)
    patient_agent = PatientAgent(PATIENT_CARETAKER_DB)   # patient replies using patient_caretaker_db
    mmse_agent = MMSEAgent(CLINIC_DB)                    # mmse reads/writes clinic DB
    analyzer = AnalyzerAgent(CLINIC_DB)

    nurse = NurseAgent(
        caretaker_agent=caretaker,
        clinic_db_path=CLINIC_DB       # <----- FIXED (string instead of dict)
    )

    print("""
=================== Alzheimer’s Multi-Agent System ===================
Commands:
  new        → new patient visit (nurse talks to caretaker)
  return     → returning patient visit
  mmse       → run MMSE test with patient
  report     → generate analyzer report
  exit       → quit system
======================================================================
""")

    # -------------------------------------------------------
    #                   MAIN LOOP
    # -------------------------------------------------------

    current_patient_id = None

    while True:
        cmd = input("\nCommand → ").strip().lower()

        # ---------------------------------------------------
        # NEW PATIENT VISIT
        # ---------------------------------------------------
        if cmd == "new":
            print("\n[Nurse → Caretaker] Requesting patient data...")
            patient_data = caretaker.provide_new_patient()
            print("[Caretaker → Nurse] Sending patient profile.")

            current_patient_id = nurse.register_new_patient(patient_data)

            # auto-save
            save_db(CLINIC_DB, load_db(CLINIC_DB))

            print(f"[Nurse] Patient registered with ID: {current_patient_id}")

        # ---------------------------------------------------
        # RETURNING PATIENT VISIT
        # ---------------------------------------------------
        elif cmd == "return":
            patient_id = input("Enter patient ID: ").strip()
            if patient_id not in clinic_db["patients"]:
                print("❌ Patient not found.")
                continue

            current_patient_id = patient_id
            print(f"[Nurse] Returning patient {patient_id} loaded.")

        # ---------------------------------------------------
        # RUN MMSE
        # ---------------------------------------------------
        elif cmd == "mmse":
            if current_patient_id is None:
                print("❌ No active patient. Use 'new' or 'return'.")
                continue

            print("\n[MMSEAgent] Running MMSE test...")

            result = mmse_agent.conduct_mmse_test(
                patient_agent=patient_agent,
                patient_id=current_patient_id
            )

            # Store in DB
            clinic_db = load_db(CLINIC_DB)
            clinic_db["mmse_scores"].setdefault(current_patient_id, []).append(result)
            save_db(CLINIC_DB, clinic_db)

            print("[MMSEAgent] Test completed and saved.")

        # ---------------------------------------------------
        # ANALYZER REPORT
        # ---------------------------------------------------
        elif cmd == "report":
            if current_patient_id is None:
                print("❌ No active patient.")
                continue

            report = analyzer.generate_patient_report(current_patient_id)

            clinic_db = load_db(CLINIC_DB)
            clinic_db["reports"][current_patient_id] = report
            save_db(CLINIC_DB, clinic_db)

            print("\n=== ANALYZER REPORT ===\n")
            print(report)

        # ---------------------------------------------------
        # EXIT SYSTEM
        # ---------------------------------------------------
        elif cmd == "exit":
            print("Exiting… DB saved.")
            break

        else:
            print("Unknown command.")


# -----------------------------------------------------------
# RUN MAIN
# -----------------------------------------------------------
if __name__ == "__main__":
    main()
