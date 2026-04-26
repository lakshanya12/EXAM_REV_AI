import os
from groq import Groq
from dotenv import load_dotenv

from rag.retriever import retrieve_relevant_chunks

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def trim_text(text: str, max_chars: int = 3000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:1500] + "\n\n...[trimmed]...\n\n" + text[-1500:]


# MAIN FUNCTION

def answer_question(question: str) -> str:
    """
    1. Retrieve relevant chunks from notes (RAG)
    2. If found → answer using notes
    3. Else → fallback to general knowledge
    """

    try:
        # Semantic retrieval
        print(f"🔍 Searching notes for: {question}")
        retrieved_text = retrieve_relevant_chunks(question, k=4)

        # CASE 1: Notes found
       
        if retrieved_text and retrieved_text.strip():

            context_text = trim_text(retrieved_text)

            prompt = f"""
You are a helpful study assistant.

Use the student's notes below to answer the question.
If the notes contain the answer, prioritize them.
If needed, you may slightly supplement with general knowledge, but clearly mention it.

Student's Notes:
---
{context_text}
---

Question: {question}

Give a clear, structured answer.
Mention if the answer is based on the notes.
"""

        # CASE 2: No notes found
      
        else:
            print("⚠️ No relevant notes found — using general knowledge")

            prompt = f"""
You are a helpful study assistant.

No relevant notes were found for this question.

Start your answer with:
"I'm answering from general knowledge as no relevant notes were found."

Then provide a clear and educational answer.

Question: {question}
"""

     
        # Call LLM

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=800
        )

        return response.choices[0].message.content

    except Exception as e:
        print("QA Agent Error:", e)
        return "Error generating answer. Please try again."