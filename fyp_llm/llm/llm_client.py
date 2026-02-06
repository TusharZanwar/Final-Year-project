import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def call_llm(messages, temperature=0.3):
    response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct",
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content.strip()
