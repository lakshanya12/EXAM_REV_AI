import os
import json
from groq import Groq
from dotenv import load_dotenv

from rag.retriever import (
    get_all_notes_text,
    retrieve_relevant_chunks,
    get_notes_count
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def trim_text(text: str, max_chars: int = 3500) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n...[trimmed for token limit]...\n\n" + text[-half:]


# Call Groq

def call_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=1500
    )
    return response.choices[0].message.content.strip()



# Parse JSON
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



# From NOTES

def generate_from_notes(notes_text: str, topic_label: str) -> list:
    prompt = f"""You are a flashcard creator.

Generate 8 flashcards STRICTLY from the notes below.

Notes:
---
{notes_text}
---

Return ONLY JSON array.

Each object:
- topic
- question
- answer
- source: "notes"
"""

    raw = call_groq(prompt)
    cards = parse_json(raw)

    for c in cards:
        c["source"] = "notes"

    print(f"Generated {len(cards)} flashcards from notes")
    return cards



# From GENERAL

def generate_from_general(topic: str) -> list:
    prompt = f"""Generate 8 flashcards about "{topic}" using general knowledge.

Return ONLY JSON array.

Each object:
- topic
- question
- answer
- source: "external"
"""

    raw = call_groq(prompt)
    cards = parse_json(raw)

    for c in cards:
        c["source"] = "external"

    print(f"Generated {len(cards)} external flashcards")
    return cards



# MAIN FUNCTION

def generate_flashcards(topic: str, use_full_notes: bool = True, confirmed_external: bool = False) -> dict:

    # No notes uploaded
    if get_notes_count() == 0:
        return {
            "status": "no_notes",
            "flashcards": [],
            "topic": topic,
            "message": "No notes uploaded yet."
        }

    
    # ALL NOTES MODE

    if use_full_notes:
        notes_text = trim_text(get_all_notes_text())

        if not notes_text.strip():
            return {
                "status": "no_notes",
                "flashcards": [],
                "topic": topic,
                "message": "Notes are empty."
            }

        print("Generating flashcards from ALL notes")
        cards = generate_from_notes(notes_text, "All Topics")

        return {
            "status": "ok",
            "flashcards": cards,
            "topic": "All Topics",
            "message": "Generated from all notes."
        }

   
    # TOPIC MODE
    

    # If user confirmed external
    if confirmed_external:
        return {
            "status": "ok",
            "flashcards": generate_from_general(topic),
            "topic": topic,
            "message": "Generated from general knowledge."
        }

    # Semantic retrieval (FIXED)
    print(f"Searching notes for: {topic}")
    retrieved_text = retrieve_relevant_chunks(topic, k=4)

    if retrieved_text and retrieved_text.strip():
        print("Found relevant notes")

        cards = generate_from_notes(retrieved_text, topic)

        return {
            "status": "ok",
            "flashcards": cards,
            "topic": topic,
            "message": "Generated from your notes."
        }

    # Not found
    print("Topic not found in notes")
    return {
        "status": "not_found",
        "flashcards": [],
        "topic": topic,
        "message": f"Topic '{topic}' not found in notes."
    }