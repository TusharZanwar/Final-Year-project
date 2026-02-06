from agents.nurse_agent import nurse_ask
from database.db import get_connection

def run_nurse_session(patient_record):
    conn = get_connection()
    cur = conn.cursor()

    print("\n🩺 Nurse Interview (Caretaker)\n")

    # Step 1: Basic patient details
    basic_fields = [
        "What is the patient's name or ID?",
        "What is the patient's age?",
        "What is the patient's gender?",
        "What is the highest education level completed?",
        "What language does the patient speak most comfortably?",
        "Does the patient live alone or with family?"
    ]

    patient_data = {}

    for q in basic_fields:
        print(f"Nurse: {q}")
        a = input("Caretaker: ")
        patient_data[q] = a

    cur.execute("""
        INSERT INTO patient (name, age, gender, education, language, living_situation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, tuple(patient_data.values()))

    patient_record.patient_id = cur.lastrowid
    print(f"Patient registered with ID: {patient_record.patient_id}")


    # Step 2: Caretaker observations (LLM-driven)
    context = ""
    for _ in range(5):
        question = nurse_ask(context)
        print(f"Nurse: {question}")
        answer = input("Caretaker: ")

        cur.execute("""
            INSERT INTO nurse_qna (patient_id, question, answer)
            VALUES (?, ?, ?)
        """, (patient_record.patient_id, question, answer))

        context += f"\nQ:{question}\nA:{answer}"

    conn.commit()
    conn.close()
