import chromadb
from sentence_transformers import SentenceTransformer


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="notes")

# Relevance threshold

RELEVANCE_THRESHOLD = 1.2

# MAIN FUNCTION

def retrieve_relevant_chunks(query: str, k: int = 4) -> str:
    """
    Returns top-k relevant chunks as a SINGLE STRING.
    Filters out weak matches using distance threshold.
    """

    try:
        total = collection.count()

        if total == 0:
            print("No notes in DB")
            return ""

        actual_k = min(k, total)

        # Encode query
        query_embedding = embedding_model.encode(query).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_k,
            include=["documents", "distances"]
        )

        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]

        relevant_chunks = []

        for doc, dist in zip(documents, distances):
            print(f"Distance: {dist:.4f}")

            if dist <= RELEVANCE_THRESHOLD:
                relevant_chunks.append(doc)
            else:
                print(f"Rejected (dist {dist:.4f})")

        print(f"Query: '{query}' → {len(relevant_chunks)} relevant chunks")

        if not relevant_chunks:
            return ""

        #return STRING (not list)
        return "\n\n".join(relevant_chunks)

    except Exception as e:
        print(f"Retrieval error: {e}")
        return ""


# Get ALL notes

def get_all_notes_text(max_chars: int = 4000) -> str:
    try:
        total = collection.count()

        if total == 0:
            return ""

        results = collection.get(limit=total)
        docs = results.get("documents", [])

        if not docs:
            return ""

        full_text = "\n\n".join(docs)

        # Optional trimming
        if len(full_text) > max_chars:
            half = max_chars // 2
            return full_text[:half] + "\n\n...[trimmed]...\n\n" + full_text[-half:]

        return full_text

    except Exception as e:
        print(f"Error fetching notes: {e}")
        return ""



# Utility functions

def get_notes_count() -> int:
    try:
        return collection.count()
    except:
        return 0


def clear_all_notes():
    global collection
    try:
        chroma_client.delete_collection("notes")
        collection = chroma_client.get_or_create_collection(name="notes")
        print("Cleared all notes")
    except Exception as e:
        print(f"Error clearing notes: {e}")