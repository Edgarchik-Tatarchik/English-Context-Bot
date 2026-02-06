from __future__ import annotations
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

client = OpenAI()

RESPONSE_SCHEMA = {
    "name": "english_context_result",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "term": {"type": "string"},
            "simple_explanation": {"type": "string"},
            "examples": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 10,
                "maxItems": 10
            }
        },
        "required": ["term", "simple_explanation", "examples"]
    },
    "strict": True
}

def generate_explanation_and_examples(term: str) -> dict:
    prompt = f"""
You are an English tutor.
Term: "{term}"

Return JSON ONLY with:
- term (string)
- simple_explanation: explain in very simple English (CEFR B1), 1–2 short sentences
- examples: EXACTLY 10 natural sentences (B1–B2), each MUST include the term EXACTLY as written.
Make the examples varied: daily life, work, study, emotions, online chat.
No extra keys. No markdown.
""".strip()

    response = client.responses.create(
        model="gpt-5.2", 
        input=prompt,
        text={
        "format": {
            "type": "json_schema",
            "name": "english_context_result",
            "schema": RESPONSE_SCHEMA["schema"],
            "strict": True
        }
        },
        max_output_tokens=500
    )

    import json
    return json.loads(response.output_text)
