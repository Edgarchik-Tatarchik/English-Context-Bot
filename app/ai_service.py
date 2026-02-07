from __future__ import annotations
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DISTRACTORS_SCHEMA = {
    "name": "quiz_distractors",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "distractors": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 2
            }
        },
        "required": ["distractors"]
    },
    "strict": True
}

def generate_quiz_distractors(term: str, correct_expl: str) -> list[str]:
    prompt = f"""
You are an English teacher creating multiple-choice options.

Term: "{term}"
Correct explanation (DO NOT copy): "{correct_expl}"

Generate EXACTLY 2 plausible but WRONG explanations (CEFR B1), 1 sentence each.
Rules:
- Must not match the correct meaning.
- Must not be simple negations/opposites.
- Must be believable confusions.
Return JSON ONLY: {{"distractors": ["...", "..."]}}
""".strip()

    response = client.responses.create(
        model="gpt-5.2",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "quiz_distractors",
                "schema": DISTRACTORS_SCHEMA["schema"],
                "strict": True
            }
        },
        max_output_tokens=200
    )

    import json
    data = json.loads(response.output_text)
    distractors = data.get("distractors")


    if not isinstance(distractors, list) or len(distractors) != 2:
        return [
            "It describes something very expensive and luxurious.",
            "It means to stop doing something for a short time."
        ]
    return distractors


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

def generate_quiz_distractors(term: str, correct_expl: str) -> list[str]:
    """
    Return 2 plausible but incorrect short explanations (B1 level).
    """
    
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

    return json.loads(response.output_text)
