from llm.llm_client import call_llm
from config.prompts import MMSE_PROMPT

def mmse_ask(domain, caretaker_summary):
    messages = [
        {
            "role": "system",
            "content": MMSE_PROMPT
        },
        {
            "role": "user",
            "content": f"""
Current cognitive domain: {domain}

Caretaker context (optional):
{caretaker_summary}

Ask ONE MMSE-style question from this domain.
Do NOT repeat domains already used.
"""
        }
    ]

    return call_llm(messages, temperature=0.3)
