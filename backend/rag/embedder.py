import chromadb
from sentence_transformers import SentenceTransformer
import uuid


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


chroma_client = chromadb.PersistentClient(path="./chroma_db")


collection = chroma_client.get_or_create_collection(name="notes")


# Chunking Function

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    """
    Splits text into overlapping chunks.
    """

    words = text.split()
    chunks = []

    step = chunk_size - overlap

    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks



# Embed + Store

def embed_and_store(text: str, source: str):
    """
    Splits text → generates embeddings → stores in ChromaDB
    """

    chunks = chunk_text(text)

    if not chunks:
        print("No chunks to embed.")
        return

    print(f"Creating {len(chunks)} chunks...")

    # Generate embeddings (batch)
    embeddings = embedding_model.encode(chunks).tolist()

    # Store all at once (FASTER than loop)
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=[
            {"source": source, "chunk_index": i}
            for i in range(len(chunks))
        ],
        ids=[str(uuid.uuid4()) for _ in range(len(chunks))]
    )

    print(f"Stored {len(chunks)} chunks from '{source}' into ChromaDB.")