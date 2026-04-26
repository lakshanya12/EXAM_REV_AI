# embedder.py — Converts extracted text into vector embeddings and stores in ChromaDB
# This is the "memory" of our RAG system

import chromadb
from sentence_transformers import SentenceTransformer
import uuid

# Load a lightweight but effective embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Set up ChromaDB client with persistent storage
chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_or_create_collection(name="student_notes")

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    """
    Splits long text into overlapping chunks.
    Overlap helps preserve context at chunk boundaries.
    """
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


def embed_and_store(text: str, source: str):
    """
    Takes the full extracted text, splits it into chunks,
    generates embeddings, and saves everything to ChromaDB.
    """
    chunks = chunk_text(text)

    if not chunks:
        print("No chunks to embed.")
        return

    # Generate embeddings for all chunks at once (batch is faster)
    embeddings = embedding_model.encode(chunks).tolist()

    # Store each chunk with a unique ID
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[{"source": source, "chunk_index": i}],
            ids=[str(uuid.uuid4())]
        )

    print(f"Stored {len(chunks)} chunks from '{source}' into ChromaDB.")