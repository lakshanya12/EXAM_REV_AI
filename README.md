# Exam Revision AI

A web application powered by Generative AI that helps students prepare for exams using their own uploaded study materials. Instead of giving generic answers, the system reads the student's actual notes and generates personalized revision tools from them.

**Core idea:** Every AI response is first attempted from the student's own notes. External knowledge is only used as a fallback when the topic is not found in the uploaded material.

---

## What It Does

The application offers four main features:

1. **Smart Revision Planning** — Generates a day-by-day study schedule based on the student's notes and exam date. Hard topics get more time, easy topics get less.

2. **Flashcard Generation** — Creates interactive flip cards from the uploaded notes. Students can choose to generate cards for all topics or a specific topic.

3. **Quiz Generation** — Produces five multiple-choice questions with scoring, correct answer highlighting, and explanations.

4. **Intelligent Q&A** — Answers student questions by searching their notes first. If the topic is not in the notes, it falls back to general knowledge and clearly says so.

---

## How the System is Built

The application is split into four layers, each with a clear responsibility:

**Layer 1 — Frontend (React + Vite)**
The user interface where students upload notes, generate flashcards, take quizzes, and ask questions. Built with React 18 and Vite 5. Runs at `http://localhost:5175`.

**Layer 2 — Backend (FastAPI)**
A REST API that handles all requests from the frontend. Endpoints include `/upload`, `/flashcards`, `/quiz`, `/ask`, and `/revision-plan`. Runs at `http://localhost:8000`.

**Layer 3 — OCR Pipeline + RAG System**
Extracts text from uploaded files using OCR engines, then stores the content in a vector database (ChromaDB) so it can be searched semantically.

**Layer 4 — AI Agents (Groq LLaMA 3.3 70B)**
Four separate AI agents handle revision planning, flashcards, quizzes, and Q&A. Each agent has its own retrieval strategy and output format.

Each layer can be changed independently. For example, swapping ChromaDB for another vector database only affects Layer 3. Replacing Groq with another LLM only affects Layer 4.

---

## How File Upload Works

When a student uploads a file, the following steps happen:

1. The file is sent to the backend.
2. An OCR router detects the file type and picks the right engine.
3. If it is a digital PDF, text is extracted directly using **PyMuPDF**.
4. If the PDF appears scanned (very little text found), it is converted to images and processed with **EasyOCR**.
5. If the image has "handwritten" in the filename, **TrOCR** is used instead — a transformer model fine-tuned on handwriting.
6. For any image file, **OpenCV** preprocesses it first — converting to grayscale, removing noise, fixing lighting, and straightening tilted text.
7. The extracted text is split into chunks of roughly 300 words with 50-word overlaps.
8. Each chunk is converted into a vector (a list of 384 numbers) using the **all-MiniLM-L6-v2** embedding model.
9. Vectors are stored in **ChromaDB** on disk.
10. The full extracted text and chunk count are returned to the student.

---

## How the AI Finds the Right Content (RAG)

RAG stands for **Retrieval Augmented Generation**. Instead of sending the entire notes to the AI (which would exceed token limits), the system retrieves only the most relevant chunks.

When the student asks a question or generates flashcards on a topic:

1. The topic is converted into a vector using the same embedding model.
2. ChromaDB finds the top 4 most similar chunks by comparing vectors.
3. Each result has a distance score. Chunks with a score above **1.2** are rejected as irrelevant.
4. Only the relevant chunks are sent to the AI as context.
5. If no relevant chunks are found, the AI answers from general knowledge and clearly states this.

This approach keeps token usage low, keeps answers grounded in the student's material, and prevents the AI from fabricating answers unrelated to the notes.

---

## OCR Engines Used

| Engine | When Used | Why |
|---|---|---|
| PyMuPDF | Digital PDFs | Reads the text layer directly — fastest and most accurate |
| TrOCR | Handwritten images | Transformer model trained on handwriting datasets |
| EasyOCR | Printed images, scanned PDFs | Two-stage detection and recognition, handles real-world photos |
| OpenCV | Before EasyOCR or TrOCR | Cleans up the image so OCR reads it more accurately |

---

## The Four AI Agents

Each feature is handled by a dedicated agent — not a single chatbot.

**Revision Agent** — The most complex agent. It identifies all subtopics in the notes, rates each one as Hard, Medium, or Easy, and builds a day-by-day schedule. Hard topics get twice the time of easy topics.

**Flashcard Agent** — Generates 8 flip cards. The source of each card (notes or external knowledge) is set by the code, not trusted from the model's output — this guarantees accuracy of source labels.

**Quiz Agent** — Generates 5 multiple-choice questions in strict JSON format. Uses few-shot examples in the prompt to enforce structure, and strips markdown fences before parsing.

**Q&A Agent** — Two-path design. If relevant chunks are found, the model answers from those chunks. If not, it answers from general knowledge with a clear disclaimer.

---

## Technology Stack

| Technology | Role |
|---|---|
| React 18 + Vite 5 | Frontend UI |
| FastAPI + Uvicorn | Backend API server |
| Groq API (LLaMA 3.3 70B Versatile) | LLM for all AI features — free tier |
| ChromaDB | Local vector database for note storage |
| all-MiniLM-L6-v2 | Embedding model (384 dimensions) |
| PyMuPDF | Digital PDF text extraction |
| TrOCR | Handwritten text recognition |
| EasyOCR | Printed and scanned image OCR |
| OpenCV | Image preprocessing |
| sentence-transformers | Python wrapper to run embedding model locally |
| python-dotenv | Loads environment variables from .env file |

---

## Why These Technologies Were Chosen

**Groq + LLaMA 3.3 70B** — Free to use, no credit card required, and runs at around 300 tokens per second thanks to Groq's custom hardware. The 70B model is large enough to produce reliable JSON output, which the smaller 8B model fails to do consistently.

**ChromaDB** — Runs locally with no extra server or cloud account needed. Data is saved to disk so it survives backend restarts. A single `pip install` is all that is required.

**Vite instead of Create-React-App** — Starts in under 500 ms (versus 10–30 seconds for CRA), updates components in under 50 ms on save, and is the current recommended build tool by the React team. CRA was deprecated in 2023.

**FastAPI instead of Flask or Django** — Built-in async support for handling file uploads and API calls concurrently. Auto-generates interactive API documentation at `/docs` from type hints alone.

---

## Error Handling

The system handles common failure cases gracefully:

- **Empty or unreadable file** — Returns an error message asking the student to try a different file.
- **Scanned PDF with no text** — Automatically switches to image-based OCR.
- **Topic not in notes** — Shows a yellow dialog asking if the student wants to use general knowledge instead.
- **No notes uploaded yet** — Shows a red banner and hides the generate button.
- **Response too long for Groq's limit** — Automatically trims the notes to the first and last section before sending.
- **Invalid JSON from the model** — Strips formatting, retries parsing, and returns an empty list rather than crashing.
- **Backend not running** — Frontend shows a clear message telling the student to start the backend on port 8000.
