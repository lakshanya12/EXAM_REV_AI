# retriever.py — Retrieves relevant chunks from ChromaDB for RAG

import chromadb
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_or_create_collection(name="student_notes")


def retrieve_relevant_chunks(query: str, top_k: int = 4) -> list:
    """
    Converts the query into a vector and finds the most similar stored chunks.
    Used for specific topic search — returns only what matches the query.
    """
    # Check if anything is stored at all first
    total = collection.count()
    if total == 0:
        print("⚠️ ChromaDB is empty — no notes uploaded yet")
        return []

    # Don't request more results than what's stored
    actual_k = min(top_k, total)

    query_embedding = embedding_model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=actual_k
    )

    chunks = results["documents"][0] if results["documents"] else []
    print(f"🔍 Retrieved {len(chunks)} chunks for query: '{query[:50]}'")
    return chunks


def get_all_notes_text(max_chars: int = 4000) -> str:
    """
    Returns ALL stored notes text joined together.
    Fetches every chunk stored and joins them.
    Caps at max_chars to avoid token limit issues with free Groq tier.
    """
    try:
        total = collection.count()
        print(f"📚 ChromaDB has {total} total chunks stored")

        if total == 0:
            print("⚠️ No notes found in ChromaDB")
            return ""

        # Fetch ALL chunks that are stored
        results = collection.get(limit=total)
        all_docs = results.get("documents", [])

        if not all_docs:
            return ""

        # Join all chunks into one big text
        full_text = "\n\n".join(all_docs)
        print(f"📄 Total notes text: {len(full_text)} characters from {len(all_docs)} chunks")

        # Trim smartly — take from start and end to get best coverage
        if len(full_text) > max_chars:
            half = max_chars // 2
            trimmed = full_text[:half] + "\n\n...[middle section trimmed]...\n\n" + full_text[-half:]
            print(f"✂️ Trimmed to {len(trimmed)} characters")
            return trimmed

        return full_text

    except Exception as e:
        print(f"❌ Error fetching notes: {e}")
        return ""


def get_notes_count() -> int:
    """Returns how many chunks are stored — useful for debugging."""
    try:
        return collection.count()
    except:
        return 0


def clear_all_notes():
    """Clears all stored notes — useful when uploading a new file."""
    try:
        global collection
        chroma_client.delete_collection("student_notes")
        collection = chroma_client.get_or_create_collection(name="student_notes")
        print("🗑️ Cleared all notes from ChromaDB")
    except Exception as e:
        print(f"Error clearing notes: {e}")