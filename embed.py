"""Milestone 4 — Embed chunks and store them in ChromaDB.

Loads chunks from the ingestion pipeline, embeds each with all-MiniLM-L6-v2,
and stores them in a local persistent ChromaDB collection ("ulm_reviews")
with source + professor metadata.

    python embed.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import load_documents

EMBED_MODEL = "all-MiniLM-L6-v2"
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "ulm_reviews"


def build_collection():
    chunks = load_documents()
    texts = [c["text"] for c in chunks]

    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # Recreate from scratch so re-runs don't collide on existing ids.
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # cosine distance, 0 = identical
    )

    collection.add(
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {"source": c["source"], "professor": c["professor"]}
            for c in chunks
        ],
        ids=[f"chunk_{i}" for i in range(len(chunks))],
    )

    print(f"Embedded and stored {collection.count()} chunks "
          f"in collection '{COLLECTION_NAME}' at {CHROMA_PATH}/")


if __name__ == "__main__":
    build_collection()
