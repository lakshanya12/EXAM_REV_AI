# revision_agent.py — Generates smart revision plan, trims notes to fit token limits

import os
from groq import Groq
from dotenv import load_dotenv
from rag.retriever import get_all_notes_text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def trim_text(text: str, max_chars: int = 3000) -> str:
    """
    Trims the notes to fit within Groq's free tier token limit.
    3000 chars ≈ ~750 tokens, leaving plenty of room for the prompt + response.
    """
    if len(text) <= max_chars:
        return text
    # Take first 1500 chars and last 1500 chars so we get intro and ending context
    return text[:1500] + "\n\n... [middle trimmed to fit token limit] ...\n\n" + text[-1500:]


def create_revision_plan(topic: str, days_until_exam: int = 7, use_full_notes: bool = True) -> str:
    """
    Creates a day-by-day revision plan.
    - use_full_notes=True  → covers everything found in uploaded notes
    - use_full_notes=False → focuses only on the specific topic typed
    """
    # Get notes and trim to safe size for free tier
    notes_context = get_all_notes_text()
    trimmed_notes = trim_text(notes_context, max_chars=3000)

    # Build prompt based on mode
    if use_full_notes and trimmed_notes:
        scope_instruction = f"""
Cover ALL topics found in the student's notes.
Read the notes carefully, identify every subtopic, and schedule 
all of them across the {days_until_exam}-day plan.
"""
        context_block = f"""
Student's Notes:
---
{trimmed_notes}
---
"""
    else:
        scope_instruction = f"""
Focus ONLY on the specific topic: "{topic}"
Use the notes if relevant, otherwise use your general knowledge.
"""
        context_block = f"""
Student's Notes (use only parts relevant to "{topic}"):
---
{trimmed_notes if trimmed_notes else "No notes uploaded — use general knowledge."}
---
"""

    prompt = f"""You are an expert study coach. The student has {days_until_exam} days before their exam.

{scope_instruction}

{context_block}

Instructions:
1. Find all subtopics from the notes
2. Rate each: Hard / Medium / Easy  
3. Give MORE time to harder topics
4. Build a {days_until_exam}-day plan

Format:

## Topic Difficulty
| Topic | Difficulty | Days Needed |
|-------|-----------|-------------|
| ...   | Hard      | 2 days      |

## {days_until_exam}-Day Revision Plan

**Day 1 — [Topic] [Hard/Medium/Easy]**
- Morning (X hrs): what to study
- Evening (X hrs): what to revise
- Tip: one specific tip

(repeat for all {days_until_exam} days)

## Final Exam Tips
3 practical tips based on the notes.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000
    )

    return response.choices[0].message.content