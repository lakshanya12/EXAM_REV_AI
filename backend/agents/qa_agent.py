# qa_agent.py — The most important agent: answers student questions
# Strategy: search notes first (RAG), fallback to LLM general knowledge if nothing found

import os
from groq import Groq
from dotenv import load_dotenv
from rag.retriever import retrieve_relevant_chunks

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Add this helper in each agent file
def trim_text(text: str, max_chars: int = 3000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:1500] + "\n\n...[trimmed]...\n\n" + text[-1500:]
def answer_question(question: str) -> str:
    """
    1. Retrieves relevant chunks from the student's uploaded notes
    2. If good context found → answers from notes
    3. If notes are empty or irrelevant → answers from general knowledge
    """
    relevant_chunks = retrieve_relevant_chunks(question, top_k=4)

    # Check if we actually got useful context
    has_context = len(relevant_chunks) > 0 and any(len(c.strip()) > 20 for c in relevant_chunks)

    if has_context:
        context_text = trim_text("\n\n".join(relevant_chunks))

        prompt = f"""
You are a helpful study assistant. Use the student's notes below to answer the question.
If the notes contain the answer, use them. Otherwise, supplement with your knowledge and say so.

Student's Notes (retrieved):
---
{context_text}
---

Question: {question}

Answer clearly and helpfully. If you used the notes, mention it.
"""
    else:
        # No notes uploaded or nothing relevant found — use general knowledge
        prompt = f"""
You are a helpful study assistant. The student hasn't uploaded notes for this topic, 
so answer from your general knowledge.

Question: {question}

Note at the start: "I'm answering from general knowledge as no relevant notes were found."
Then give a clear, educational answer.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=800
    )

    return response.choices[0].message.content