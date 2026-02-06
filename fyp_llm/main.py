from data_models import PatientRecord
from sessions.nurse_session import run_nurse_session
from sessions.mmse_session import run_mmse_session
from agents.analyzer_agent import generate_report
from database.db import init_db

def main():
    init_db()
    patient = PatientRecord()

    run_nurse_session(patient)
    run_mmse_session(patient)

    print("\n📊 Generating Alzheimer’s Risk Report...\n")
    report = generate_report(patient.patient_id)

    print("🧾 REPORT\n")
    print(report)

if __name__ == "__main__":
    main()
