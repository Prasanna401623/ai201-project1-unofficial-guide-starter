"""Milestone 4 — Retrieval against the ChromaDB collection.

Embeds a query with the same all-MiniLM-L6-v2 model used at ingestion time
and returns the top-k most similar chunks with their distance scores.

    python retrieve.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

from embed import CHROMA_PATH, COLLECTION_NAME, EMBED_MODEL

# Load the model and collection once at import so repeated retrieve() calls
# (e.g. from the query interface) don't reopen them every time.
_model = SentenceTransformer(EMBED_MODEL)
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_collection(COLLECTION_NAME)


def retrieve(query, n_results=5):
    """Return the top-n chunks most similar to `query`.

    Each result is a dict: {text, source, professor, distance}.
    Lower distance = more similar (cosine distance; below ~0.5 is a good match).
    """
    query_embedding = _model.encode([query]).tolist()
    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text": doc,
            "source": meta["source"],
            "professor": meta["professor"],
            "distance": dist,
        })
    return hits


if __name__ == "__main__":
    queries = [
        "What do students say about Wiedemeier's exams?",
        "Is April Picard good for students who struggle with math?",
        "What are the main complaints about Thibodeaux?",
    ]

    for query in queries:
        print(f"\n{'=' * 70}\nQUERY: {query}\n{'=' * 70}")
        for i, hit in enumerate(retrieve(query), 1):
            print(f"\n[{i}] distance={hit['distance']:.3f} | "
                  f"{hit['professor']} ({hit['source']})")
            print(f"    {hit['text']}")
