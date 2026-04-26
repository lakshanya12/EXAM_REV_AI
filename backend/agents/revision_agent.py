import os
from groq import Groq
from dotenv import load_dotenv

# Import semantic retrieval (RAG)
from rag.retriever import retrieve_relevant_chunks

# Load environment variables

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Revision Plan Generator

def create_revision_plan(topic: str, days_until_exam: int = 7, use_full_notes: bool = True) -> str:
    """
    Generates a structured revision plan using semantic retrieval (RAG)

    Args:
        topic (str): Topic entered by user
        days_until_exam (int): Number of days available
        use_full_notes (bool): Whether to cover full notes or only specific topic

    Returns:
        str: Generated revision plan
    """

    try:
       
        #Retrieve relevant chunks (RAG)
       
        query_for_search = topic if topic else "all topics in notes"
        retrieved_context = retrieve_relevant_chunks(query_for_search, k=5)

        # Build prompt dynamically
 
        if use_full_notes and retrieved_context:
            scope_instruction = f"""
Cover ALL topics found in the student's notes.
Read the notes carefully, identify every subtopic, and schedule 
all of them across the {days_until_exam}-day plan.
"""
            context_block = f"""
Student's Notes:
---
{retrieved_context}
---
"""
        else:
            scope_instruction = f"""
Focus ONLY on the specific topic: "{topic}".
Use the notes if relevant, otherwise use your general knowledge.
"""
            context_block = f"""
Student's Notes (filtered for "{topic}"):
---
{retrieved_context if retrieved_context else "No notes uploaded — use general knowledge."}
---
"""

       
        #Prompt Engineering
        prompt = f"""You are an expert study coach. The student has {days_until_exam} days before their exam.

{scope_instruction}

{context_block}

Instructions:
1. Identify all subtopics from the notes
2. Classify each as Hard / Medium / Easy
3. Allocate MORE time to harder topics
4. Build a clear and structured revision plan

Format:

## Topic Difficulty
| Topic | Difficulty | Days Needed |
|-------|-----------|-------------|

## {days_until_exam}-Day Revision Plan

**Day 1 — [Topic] [Difficulty]**
- Morning: Topics to study
- Evening: Revision tasks
- Tip: One useful tip

(Repeat for all days)

## Final Exam Tips
Provide 3 practical tips based on the notes.
"""

        #Call Groq LLM
      
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Revision Plan Error:", e)
        return "Error generating revision plan. Please try again."