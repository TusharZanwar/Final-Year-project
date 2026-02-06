from llm.llm_client import call_llm
from database.db import get_connection
from config.prompts import ANALYZER_PROMPT


# -----------------------------
# Stage confidence computation
# -----------------------------
def compute_stage_confidence(memory, orientation, caretaker, latency):
    raw = (
        0.4 * memory +
        0.25 * orientation +
        0.2 * caretaker +
        0.15 * latency
    )
    return round(raw * 100, 1)


# -----------------------------
# Main report generator
# -----------------------------
def generate_report(patient_id):
    conn = get_connection()
    cur = conn.cursor()

    # ---- Fetch patient info ----
    cur.execute(
        "SELECT name, age, gender, education, language, living_situation FROM patient WHERE id=?",
        (patient_id,)
    )
    patient = cur.fetchone()

    # ---- Fetch caretaker Q&A ----
    cur.execute(
        "SELECT question, answer FROM nurse_qna WHERE patient_id=?",
        (patient_id,)
    )
    nurse_data = cur.fetchall()

    # ---- Fetch MMSE Q&A + latency ----
    cur.execute(
        "SELECT question, answer, latency FROM mmse_qna WHERE patient_id=?",
        (patient_id,)
    )
    mmse_data = cur.fetchall()

    conn.close()

    # -----------------------------
    # Latency calculation
    # -----------------------------
    latencies = [row[2] for row in mmse_data if row[2] is not None]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

    # -----------------------------
    # Screening-based scoring
    # -----------------------------

    # Memory score
    memory_score = 0.0
    for _, answer, _ in mmse_data:
        if answer.strip().lower() in ["ok", "not sure", "dont know", "don't know", "no idea"]:
            memory_score = 0.5
            break

    # Orientation score
    orientation_score = 0.5 if any(
        "date" in q.lower() or "day" in q.lower() or "where" in q.lower()
        for q, _, _ in mmse_data
    ) else 0.0

    # Caretaker concern score
    caretaker_text = " ".join(a for _, a in nurse_data).lower()
    if "forget" in caretaker_text or "miss" in caretaker_text:
        caretaker_score = 1.0
    elif caretaker_text:
        caretaker_score = 0.5
    else:
        caretaker_score = 0.0

    # Latency score
    if avg_latency > 8:
        latency_score = 1.0
    elif avg_latency > 5:
        latency_score = 0.5
    else:
        latency_score = 0.0

    # -----------------------------
    # Final stage confidence
    # -----------------------------
    stage_confidence = compute_stage_confidence(
        memory_score,
        orientation_score,
        caretaker_score,
        latency_score
    )
    total_questions = len(mmse_data)
    slow_answers = sum(1 for _, _, l in mmse_data if l and l > 7)
    vague_answers = sum(
        1 for _, a, _ in mmse_data
        if a.strip().lower() in ["ok", "not sure", "dont know", "don't know"]
    )


    # -----------------------------
    # Content sent to LLM
    # -----------------------------
    content = f"""
Patient Details:
Name: {patient[0]}
Age: {patient[1]}
Lives: {patient[5]}

Summary of Test Performance:
- Total questions asked: {total_questions}
- Slow responses (>7s): {slow_answers}
- Unclear responses: {vague_answers}

Caretaker Summary:
{nurse_data}

Average Response Time:
{avg_latency} seconds

Estimated Cognitive Stage:
Choose ONE from the allowed stages.

Stage Confidence:
{stage_confidence}%

Explain the result clearly using the above facts.
"""

    messages = [
        {"role": "system", "content": ANALYZER_PROMPT},
        {"role": "user", "content": content}
    ]

    return call_llm(messages, temperature=0.2)
