# quiz_agent.py
# Same flow as flashcard_agent but generates MCQ questions instead

import os
import json
from groq import Groq
from dotenv import load_dotenv
from rag.retriever import get_all_notes_text, retrieve_relevant_chunks, get_notes_count

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def trim_text(text: str, max_chars: int = 3500) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n...[trimmed]...\n\n" + text[-half:]


def call_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=1500
    )
    return response.choices[0].message.content.strip()


def parse_json(raw: str) -> list:
    try:
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"Raw output: {raw[:300]}")
        return []


def generate_quiz_from_notes(notes_text: str, topic_label: str) -> list:
    """Generates MCQ questions strictly from the notes content."""
    prompt = f"""You are a quiz generator for exam preparation.

Generate 5 multiple-choice questions based STRICTLY on the notes below.
Do NOT add any information from outside the notes.
Every question and answer must come directly from the content below.

Notes:
---
{notes_text}
---

Return ONLY a valid JSON array. No explanation, no markdown fences.
Each object must have:
  "topic"       : the specific subtopic this question is from (from the notes)
  "question"    : the question text
  "options"     : exactly 4 options like ["A. ...", "B. ...", "C. ...", "D. ..."]
  "answer"      : the correct letter only, e.g. "B"
  "explanation" : one sentence from the notes explaining why that answer is correct
  "source"      : always "notes"

Example:
[
  {{
    "topic": "Machine Learning",
    "question": "What does gradient descent minimize?",
    "options": ["A. Accuracy", "B. Loss function", "C. Learning rate", "D. Epochs"],
    "answer": "B",
    "explanation": "Gradient descent minimizes the loss function by iteratively updating weights.",
    "source": "notes"
  }}
]"""

    raw = call_groq(prompt)
    questions = parse_json(raw)

    for q in questions:
        q["source"] = "notes"

    print(f"✅ Generated {len(questions)} quiz questions from notes")
    return questions


def generate_quiz_from_general(topic: str) -> list:
    """Generates MCQ questions from general AI knowledge."""
    prompt = f"""You are a quiz generator for exam preparation.

Generate 5 multiple-choice questions about "{topic}" using your general knowledge.
This topic was NOT found in the student's uploaded notes.

Return ONLY a valid JSON array. No explanation, no markdown fences.
Each object must have:
  "topic"       : "{topic}"
  "question"    : the question text
  "options"     : exactly 4 options like ["A. ...", "B. ...", "C. ...", "D. ..."]
  "answer"      : the correct letter only, e.g. "B"
  "explanation" : one sentence explaining why that answer is correct
  "source"      : always "external"

Example:
[
  {{
    "topic": "{topic}",
    "question": "What is ...?",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "answer": "A",
    "explanation": "Because ...",
    "source": "external"
  }}
]"""

    raw = call_groq(prompt)
    questions = parse_json(raw)

    for q in questions:
        q["source"] = "external"

    print(f"✅ Generated {len(questions)} quiz questions from general knowledge")
    return questions


def generate_quiz(topic: str, use_full_notes: bool = True, confirmed_external: bool = False) -> dict:
    """
    Main entry point for quiz generation.

    Returns:
    {
      "status": "ok" | "not_found" | "no_notes",
      "quiz": [...],
      "topic": topic,
      "message": "..."
    }
    """

    # Check if anything is uploaded
    if get_notes_count() == 0:
        return {
            "status": "no_notes",
            "quiz": [],
            "topic": topic,
            "message": "No notes uploaded yet. Please upload a file first."
        }

    # ════════════════════════════════════════
    # ALL TOPICS MODE
    # ════════════════════════════════════════
    if use_full_notes:
        notes_text = trim_text(get_all_notes_text())

        if not notes_text.strip():
            return {
                "status": "no_notes",
                "quiz": [],
                "topic": topic,
                "message": "Notes appear empty. Try uploading your file again."
            }

        print(f"📄 Generating quiz from ALL notes ({len(notes_text)} chars)")
        questions = generate_quiz_from_notes(notes_text, "All Topics")

        return {
            "status": "ok",
            "quiz": questions,
            "topic": "All Topics from Notes",
            "message": f"Generated {len(questions)} questions from your uploaded notes."
        }

    # ════════════════════════════════════════
    # SPECIFIC TOPIC MODE
    # ════════════════════════════════════════

    if confirmed_external:
        print(f"🌐 User confirmed — generating '{topic}' quiz from general knowledge")
        questions = generate_quiz_from_general(topic)
        return {
            "status": "ok",
            "quiz": questions,
            "topic": topic,
            "message": "Generated from general knowledge (not in your notes)."
        }

    # Semantic search in notes
    print(f"🔍 Searching notes for: '{topic}'")
    relevant_chunks = retrieve_relevant_chunks(topic, top_k=4)
    useful_chunks = [c for c in relevant_chunks if len(c.strip()) > 80]
    print(f"📊 Found {len(relevant_chunks)} chunks, {len(useful_chunks)} useful")

    if useful_chunks:
        notes_content = trim_text("\n\n".join(useful_chunks))
        print(f"✅ Topic found in notes — generating quiz from notes")
        questions = generate_quiz_from_notes(notes_content, topic)

        return {
            "status": "ok",
            "quiz": questions,
            "topic": topic,
            "message": "Generated from your uploaded notes."
        }
    else:
        print(f"❌ Topic '{topic}' not found in notes")
        return {
            "status": "not_found",
            "quiz": [],
            "topic": topic,
            "message": f"The topic '{topic}' was not found in your uploaded notes."
        }