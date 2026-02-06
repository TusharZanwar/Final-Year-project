from llm.llm_client import call_llm
from config.prompts import NURSE_PROMPT

def nurse_ask(context):
    messages = [
        {"role": "system", "content": NURSE_PROMPT},
        {"role": "user", "content": context},
        {"role": "user", "content": "Ask the next question to collect patient or caretaker information."}
    ]
    return call_llm(messages, temperature=0.2)
