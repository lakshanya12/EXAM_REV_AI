import os
import json
from groq import Groq
from dotenv import load_dotenv

from rag.retriever import (
    get_all_notes_text,
    retrieve_relevant_chunks,
    get_notes_count
)

# Load ENV

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Trim (used only for ALL notes mode)

def trim_text(text: str, max_chars: int = 3500) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n...[trimmed]...\n\n" + text[-half:]

# Call Groq

def call_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=1500
    )
    return response.choices[0].message.content.strip()

# Parse JSON safely

def parse_json(raw: str) -> list:
    try:
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw output: {raw[:300]}")
        return []



# Quiz from notes

def generate_quiz_from_notes(notes_text: str, topic_label: str) -> list:
    prompt = f"""You are a quiz generator for exam preparation.

Generate 5 multiple-choice questions based STRICTLY on the notes below.
Do NOT use any external knowledge.

Notes:
---
{notes_text}
---

Return ONLY a valid JSON array.

Each object must contain:
- "topic"
- "question"
- "options" (4 options)
- "answer"
- "explanation"
- "source": "notes"
"""

    raw = call_groq(prompt)
    questions = parse_json(raw)

    for q in questions:
        q["source"] = "notes"

    print(f"Generated {len(questions)} quiz questions from notes")
    return questions


# Quiz from general knowledge

def generate_quiz_from_general(topic: str) -> list:
    prompt = f"""Generate 5 MCQ questions about "{topic}" using general knowledge.

Return ONLY JSON array.

Each object must contain:
- topic
- question
- options
- answer
- explanation
- source: "external"
"""

    raw = call_groq(prompt)
    questions = parse_json(raw)

    for q in questions:
        q["source"] = "external"

    print(f"Generated {len(questions)} external questions")
    return questions


# MAIN FUNCTION

def generate_quiz(topic: str, use_full_notes: bool = True, confirmed_external: bool = False) -> dict:

    # No notes case
    if get_notes_count() == 0:
        return {
            "status": "no_notes",
            "quiz": [],
            "topic": topic,
            "message": "No notes uploaded yet."
        }

   
    # ALL NOTES MODE
  
    if use_full_notes:
        notes_text = trim_text(get_all_notes_text())

        if not notes_text.strip():
            return {
                "status": "no_notes",
                "quiz": [],
                "topic": topic,
                "message": "Notes are empty."
            }

        print("Generating quiz from ALL notes")
        questions = generate_quiz_from_notes(notes_text, "All Topics")

        return {
            "status": "ok",
            "quiz": questions,
            "topic": "All Topics",
            "message": "Generated from all uploaded notes."
        }

   
    # TOPIC MODE
   

    # If user already confirmed external
    if confirmed_external:
        return {
            "status": "ok",
            "quiz": generate_quiz_from_general(topic),
            "topic": topic,
            "message": "Generated from general knowledge."
        }

    # Semantic retrieval (FIXED)
    print(f"Searching notes for: {topic}")
    retrieved_text = retrieve_relevant_chunks(topic, k=4)

    if retrieved_text.strip():
        print("Found relevant content in notes")

        questions = generate_quiz_from_notes(retrieved_text, topic)

        return {
            "status": "ok",
            "quiz": questions,
            "topic": topic,
            "message": "Generated from your notes."
        }

    # Not found case
    print("Topic not found in notes")
    return {
        "status": "not_found",
        "quiz": [],
        "topic": topic,
        "message": f"Topic '{topic}' not found in notes."
    }