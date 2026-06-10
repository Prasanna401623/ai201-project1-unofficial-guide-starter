"""Milestone 5 — Grounded generation over retrieved reviews.

ask() retrieves the top-5 chunks for a question, builds a grounded prompt,
calls the Groq API (llama-3.3-70b-versatile), and returns the answer plus a
deduplicated list of sources.

    python query.py
"""

import os

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
SYSTEM_INSTRUCTION = (
    "Answer the question using only the information in the provided documents. "
    "If the documents don't contain enough information to answer, say: "
    "I don't have enough information on that."
)

_client = Groq(api_key=os.environ["GROQ_API_KEY"])


def _build_context(hits):
    """Format retrieved chunks into a numbered context block for the prompt."""
    blocks = []
    for i, hit in enumerate(hits, 1):
        blocks.append(
            f"[Document {i}] Professor: {hit['professor']} "
            f"(source: {hit['source']})\n{hit['text']}"
        )
    return "\n\n".join(blocks)


def ask(question, n_results=5):
    """Answer `question` grounded only in retrieved review chunks.

    Returns {"answer": str, "sources": list[str]}.
    """
    hits = retrieve(question, n_results=n_results)
    context = _build_context(hits)

    user_message = (
        f"Documents:\n{context}\n\n"
        f"Question: {question}"
    )

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )
    answer = response.choices[0].message.content.strip()

    # Deduplicate sources while preserving retrieval order.
    seen = set()
    sources = []
    for hit in hits:
        key = (hit["professor"], hit["source"])
        if key not in seen:
            seen.add(key)
            sources.append(f"{hit['professor']} ({hit['source']})")

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    for question in [
        "What do students say about Wiedemeier's exams?",
        "What is the best restaurant near ULM?",
    ]:
        result = ask(question)
        print(f"\n{'=' * 70}\nQ: {question}\n{'=' * 70}")
        print(f"ANSWER:\n{result['answer']}\n")
        print("SOURCES:")
        for s in result["sources"]:
            print(f"  - {s}")
