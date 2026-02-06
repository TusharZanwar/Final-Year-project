import time
from agents.mmse_agent import mmse_ask
from database.db import get_connection

# ---- Configuration ----
LATENCY_THRESHOLD = 7.0
MAX_FOLLOWUPS = 2

# MMSE cognitive domains (STRUCTURE, not questions)
MMSE_DOMAINS = [
    "orientation_time",
    "orientation_place",
    "registration",
    "attention_backward",
    "recall",
    "routine_memory",
    "executive_function"
]


def looks_like_failure(answer, latency):
    if not answer:
        return True

    a = answer.strip().lower()
    if a in ["", "ok", "dont know", "don't know", "not sure", "maybe", "no idea"]:
        return True

    if latency >= LATENCY_THRESHOLD:
        return True

    return False


def run_mmse_session(patient_record):
    conn = get_connection()
    cur = conn.cursor()

    print("\n🧠 Cognitive Assessment (Patient)\n")

    caretaker_summary = patient_record.caretaker_interview.summary

    domain_index = 0
    followups_used = 0

    while domain_index < len(MMSE_DOMAINS):
        current_domain = MMSE_DOMAINS[domain_index]

        # Ask MMSE question for this domain
        question = mmse_ask(
            domain=current_domain,
            caretaker_summary=caretaker_summary
        )
        print(f"MMSE: {question}")

        start = time.time()
        answer = input("Patient: ")
        latency = round(time.time() - start, 2)

        # Store Q&A with domain
        cur.execute("""
            INSERT INTO mmse_qna (patient_id, domain, question, answer, latency)
            VALUES (?, ?, ?, ?, ?)
        """, (
            patient_record.patient_id,
            current_domain,
            question,
            answer,
            latency
        ))

        # ---- FAILURE HANDLING ----
        if looks_like_failure(answer, latency):
            if followups_used < MAX_FOLLOWUPS:
                followups_used += 1
                # follow-up stays in SAME domain
                continue
            else:
                # HARD STOP probing this domain
                followups_used = 0
                domain_index += 1
                continue

        # ---- SUCCESS ----
        followups_used = 0
        domain_index += 1

    conn.commit()
    conn.close()
