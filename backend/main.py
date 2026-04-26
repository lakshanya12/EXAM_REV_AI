# main.py — FastAPI entry point with detailed error logging

import os
import shutil
import traceback

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Exam Revision Assistant")

# Allow all origins so localhost:5175 can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ------------------------------------------------------------------
# Lazy imports — we import agents only when needed so startup errors
# don't crash the whole server before we can see what went wrong
# ------------------------------------------------------------------
def get_ocr():
    from ocr.ocr_router import extract_text_from_file
    return extract_text_from_file

def get_embedder():
    from rag.embedder import embed_and_store
    return embed_and_store

def get_revision_agent():
    from agents.revision_agent import create_revision_plan
    return create_revision_plan

def get_flashcard_agent():
    from agents.flashcard_agent import generate_flashcards
    return generate_flashcards

def get_quiz_agent():
    from agents.quiz_agent import generate_quiz
    return generate_quiz

def get_qa_agent():
    from agents.qa_agent import answer_question
    return answer_question


# ------------------------------------------------------------------
# Health check — visit http://localhost:8000/ to confirm it's running
# ------------------------------------------------------------------
@app.get("/")
def health_check():
    return {"status": "Backend is running ✅"}


# ------------------------------------------------------------------
# POST /upload — accepts file, runs OCR, stores in ChromaDB
# ------------------------------------------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        print(f"\n📥 Received file: {file.filename}")

        # Save file to disk
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        print(f"✅ File saved to: {file_path}")

        # Run OCR
        print("🔍 Running OCR...")
        extract_text_from_file = get_ocr()
        extracted_text = extract_text_from_file(file_path)
        print(f"✅ Extracted {len(extracted_text)} characters")

        if not extracted_text or len(extracted_text.strip()) < 10:
            return JSONResponse(
                status_code=400,
                content={"error": "Could not extract meaningful text. Try a clearer image or PDF."}
            )

        # Embed into ChromaDB
        print("💾 Embedding into ChromaDB...")
        embed_and_store = get_embedder()
        embed_and_store(extracted_text, source=file.filename)
        print("✅ Stored in ChromaDB")

        return {
            "message": "File processed successfully",
            "preview": extracted_text[:500],
            "full_text": extracted_text
        }

    except Exception as e:
        # Print full traceback in backend terminal so you can see the real error
        print("\n❌ UPLOAD ERROR:")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ------------------------------------------------------------------
# POST /revision-plan
# ------------------------------------------------------------------
@app.post("/revision-plan")
async def revision_plan(
    topic: str = Form(...),
    days_until_exam: int = Form(7),
    use_full_notes: str = Form("true")   # comes as string from FormData
):
    try:
        print(f"\n📅 Revision plan — topic: '{topic}', days: {days_until_exam}, full_notes: {use_full_notes}")
        create_revision_plan = get_revision_agent()

        # Convert string "true"/"false" to boolean
        full_notes_bool = use_full_notes.lower() == "true"

        plan = create_revision_plan(topic, days_until_exam, full_notes_bool)
        return {"plan": plan}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# POST /flashcards
@app.post("/flashcards")
async def flashcards(
    topic: str = Form(...),
    use_full_notes: str = Form("true"),
    confirmed_external: str = Form("false")   # user confirmed they want external
):
    try:
        print(f"\n🃏 Flashcards — topic: '{topic}', full_notes: {use_full_notes}, confirmed_external: {confirmed_external}")
        generate_flashcards = get_flashcard_agent()
        result = generate_flashcards(
            topic,
            use_full_notes.lower() == "true",
            confirmed_external.lower() == "true"
        )
        return result
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

# POST /quiz
@app.post("/quiz")
async def quiz(
    topic: str = Form(...),
    use_full_notes: str = Form("true"),
    confirmed_external: str = Form("false")
):
    try:
        print(f"\n🧠 Quiz — topic: '{topic}', full_notes: {use_full_notes}, confirmed_external: {confirmed_external}")
        generate_quiz = get_quiz_agent()
        result = generate_quiz(
            topic,
            use_full_notes.lower() == "true",
            confirmed_external.lower() == "true"
        )
        return result
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ------------------------------------------------------------------
# POST /ask
# ------------------------------------------------------------------
@app.post("/ask")
async def ask(question: str = Form(...)):
    try:
        print(f"\n💬 Question: {question}")
        answer_question = get_qa_agent()
        answer = answer_question(question)
        return {"answer": answer}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ------------------------------------------------------------------
# GET /notes-text — returns all stored notes text
# ------------------------------------------------------------------
@app.get("/notes-text")
async def get_notes_text():
    try:
        from rag.retriever import get_all_notes_text
        text = get_all_notes_text(max_chunks=100)
        return {"text": text}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

# Add this import at top if not already there
from rag.retriever import get_notes_count, clear_all_notes

# ── Update the /upload endpoint — clear old notes before storing new ones ──
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        print(f"\n📥 Received file: {file.filename}")

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        print(f"✅ File saved to: {file_path}")

        print("🔍 Running OCR...")
        extract_text_from_file = get_ocr()
        extracted_text = extract_text_from_file(file_path)
        print(f"✅ Extracted {len(extracted_text)} characters")

        if not extracted_text or len(extracted_text.strip()) < 10:
            return JSONResponse(
                status_code=400,
                content={"error": "Could not extract meaningful text. Try a clearer image or PDF."}
            )

        # Clear old notes so new upload doesn't mix with previous file
        print("🗑️ Clearing previous notes from ChromaDB...")
        clear_all_notes()

        print("💾 Embedding into ChromaDB...")
        embed_and_store = get_embedder()
        embed_and_store(extracted_text, source=file.filename)

        # Confirm how many chunks were stored
        count = get_notes_count()
        print(f"✅ Stored {count} chunks in ChromaDB")

        return {
            "message": "File processed successfully",
            "preview": extracted_text[:500],
            "full_text": extracted_text,
            "chunks_stored": count          # send this to frontend
        }

    except Exception as e:
        print("\n❌ UPLOAD ERROR:")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Add this new endpoint to check notes status ──
@app.get("/notes-status")
async def notes_status():
    """
    Returns how many chunks are stored in ChromaDB.
    Frontend uses this to warn user if no notes are uploaded.
    """
    try:
        count = get_notes_count()
        return {
            "chunks": count,
            "has_notes": count > 0,
            "message": f"{count} chunks stored" if count > 0 else "No notes uploaded yet"
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})