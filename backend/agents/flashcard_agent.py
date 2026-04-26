# flashcard_agent.py
# Flow:
#   ALL TOPICS  → get everything from ChromaDB → generate from notes only
#   SPECIFIC    → semantic search in ChromaDB first
#                 → found?  generate from notes, badge = "notes"
#                 → not found? return flag so frontend can ask user first

import os
import json
from groq import Groq
from dotenv import load_dotenv
from rag.retriever import get_all_notes_text, retrieve_relevant_chunks, get_notes_count

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def trim_text(text: str, max_chars: int = 3500) -> str:
    """Trim notes to stay inside Groq free tier token limits."""
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n...[trimmed for token limit]...\n\n" + text[-half:]


def call_groq(prompt: str) -> str:
    """Single place to call Groq so it's easy to swap models later."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=1500
    )
    return response.choices[0].message.content.strip()


def parse_json(raw: str) -> list:
    """Safely parse JSON array from LLM response."""
    try:
        # Strip markdown fences if model added them
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


def generate_from_notes(notes_text: str, topic_label: str) -> list:
    """
    Generates flashcards strictly from the provided notes text.
    topic_label is just used for the card's topic field.
    """
    prompt = f"""You are a flashcard creator for exam preparation.

Generate 8 flashcards based STRICTLY on the notes below.
Do NOT add any information from outside the notes.
Every question and answer must come directly from the content below.

Notes:
---
{notes_text}
---

Return ONLY a valid JSON array. No explanation, no markdown fences.
Each object must have:
  "topic"    : the specific subtopic this card is about (from the notes)
  "question" : a clear exam-style question
  "answer"   : a concise answer taken from the notes
  "source"   : always "notes"

Example:
[
  {{
    "topic": "Neural Networks",
    "question": "What is an activation function?",
    "answer": "A function that introduces non-linearity into a neural network, allowing it to learn complex patterns.",
    "source": "notes"
  }}
]"""

    raw = call_groq(prompt)
    cards = parse_json(raw)

    # Force source = "notes" regardless of what model says
    for card in cards:
        card["source"] = "notes"

    print(f"✅ Generated {len(cards)} flashcards from notes")
    return cards


def generate_from_general(topic: str) -> list:
    """
    Generates flashcards from general AI knowledge.
    Used ONLY when topic is confirmed not found in notes.
    """
    prompt = f"""You are a flashcard creator for exam preparation.

Generate 8 flashcards about "{topic}" using your general knowledge.
This topic was NOT found in the student's uploaded notes.

Return ONLY a valid JSON array. No explanation, no markdown fences.
Each object must have:
  "topic"    : "{topic}"
  "question" : a clear exam-style question
  "answer"   : a concise accurate answer
  "source"   : always "external"

Example:
[
  {{
    "topic": "{topic}",
    "question": "What is ...?",
    "answer": "It is ...",
    "source": "external"
  }}
]"""

    raw = call_groq(prompt)
    cards = parse_json(raw)

    # Force source = "external" regardless of what model says
    for card in cards:
        card["source"] = "external"

    print(f"✅ Generated {len(cards)} flashcards from general knowledge")
    return cards


def generate_flashcards(topic: str, use_full_notes: bool = True, confirmed_external: bool = False) -> dict:
    """
    Main entry point for flashcard generation.

    Returns a dict:
    {
      "status": "ok" | "not_found" | "no_notes",
      "flashcards": [...],          # filled when status = "ok"
      "topic": topic,               # filled when status = "not_found"
      "message": "..."              # human readable message
    }

    Status meanings:
      "ok"          → cards generated, return them
      "not_found"   → topic not in notes, frontend should ask user
      "no_notes"    → ChromaDB is empty, nothing uploaded
    """

    # ── Check if anything is uploaded at all ──
    if get_notes_count() == 0:
        return {
            "status": "no_notes",
            "flashcards": [],
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
                "flashcards": [],
                "topic": topic,
                "message": "Notes appear empty. Try uploading your file again."
            }

        print(f"📄 Generating flashcards from ALL notes ({len(notes_text)} chars)")
        cards = generate_from_notes(notes_text, "All Topics")

        return {
            "status": "ok",
            "flashcards": cards,
            "topic": "All Topics from Notes",
            "message": f"Generated {len(cards)} flashcards from your uploaded notes."
        }

    # ════════════════════════════════════════
    # SPECIFIC TOPIC MODE
    # ════════════════════════════════════════

    # If user already confirmed they want external knowledge, skip search
    if confirmed_external:
        print(f"🌐 User confirmed — generating '{topic}' from general knowledge")
        cards = generate_from_general(topic)
        return {
            "status": "ok",
            "flashcards": cards,
            "topic": topic,
            "message": f"Generated from general knowledge (not in your notes)."
        }

    # Step 1: Semantic search in ChromaDB
    print(f"🔍 Searching notes for topic: '{topic}'")
    relevant_chunks = retrieve_relevant_chunks(topic, top_k=4)

    # Step 2: Filter out low-quality / irrelevant chunks
    # A chunk must have more than 80 chars to be considered useful
    useful_chunks = [c for c in relevant_chunks if len(c.strip()) > 80]
    print(f"📊 Found {len(relevant_chunks)} chunks, {len(useful_chunks)} are useful")

    if useful_chunks:
        # Topic found in notes → generate from notes
        notes_content = trim_text("\n\n".join(useful_chunks))
        print(f"✅ Topic found in notes — generating from notes content")
        cards = generate_from_notes(notes_content, topic)

        return {
            "status": "ok",
            "flashcards": cards,
            "topic": topic,
            "message": f"Generated from your uploaded notes."
        }
    else:
        # Topic NOT found in notes → return "not_found" so frontend can ask user
        print(f"❌ Topic '{topic}' not found in notes")
        return {
            "status": "not_found",
            "flashcards": [],
            "topic": topic,
            "message": f"The topic '{topic}' was not found in your uploaded notes."
        }