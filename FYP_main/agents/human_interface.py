import time

class HumanInterface:
    """
    Allows a real human to answer MMSE questions.
    Mimics PatientAgent interface.
    """

    def answer_question(self, question):
        #print(f"\n[MMSE → Human] {question}")
        start = time.time()
        answer = input("[Human → MMSE] ")
        latency = round(time.time() - start, 2)

        # Ensure realistic latency
        if latency < 0.5:
            time.sleep(0.8)
            latency = 1.0

        return answer, latency
