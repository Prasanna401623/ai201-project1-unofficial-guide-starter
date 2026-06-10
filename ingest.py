"""Milestone 3 — Document ingestion and chunking.

Loads every .txt file from documents/, splits each into individual review
blocks on the `---` delimiter, and chunks each block into overlapping
character windows with source metadata attached.

Run directly to print 5 random chunks for verification:
    python ingest.py
"""

import glob
import os
import random
import re

DOCUMENTS_DIR = "documents"
MAX_CHUNK_SIZE = 800


def parse_header(block):
    """Pull the professor name and department from a file's header block.

    The first block of each file looks like:
        Professor: Paul Wiedemeier
        Department: Computer Science
        Overall Quality: 1.3/5
        ...
    Returns (professor, department), falling back to "Unknown" if absent.
    """
    professor = "Unknown"
    department = "Unknown"
    for line in block.splitlines():
        if line.lower().startswith("professor:"):
            professor = line.split(":", 1)[1].strip()
        elif line.lower().startswith("department:"):
            department = line.split(":", 1)[1].strip()
    return professor, department


def chunk_text(text, max_chunk_size=MAX_CHUNK_SIZE):
    """Return a review block as one chunk, splitting only if it is too long.

    Each `---`-delimited review block is already a complete, self-contained
    review (typically 50–400 characters), so it is kept whole. Only blocks
    longer than `max_chunk_size` are split — and then on sentence boundaries,
    never mid-word — so every chunk is a readable fragment, never a leftover
    like "ompletely unfair.".
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chunk_size:
        return [text]

    # Split into sentences, then greedily pack them into chunks that stay
    # under the size limit. A single sentence longer than the limit becomes
    # its own chunk rather than being cut.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = ""
    for sentence in sentences:
        if not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= max_chunk_size:
            current += " " + sentence
        else:
            chunks.append(current.strip())
            current = sentence
    if current.strip():
        chunks.append(current.strip())
    return chunks


def load_documents(documents_dir=DOCUMENTS_DIR):
    """Read all .txt files, split into review blocks, and chunk each block.

    Returns a list of dicts, one per chunk:
        {
            "text": str,           # the chunk content
            "source": str,         # source filename, e.g. "paul_wiedemeier.txt"
            "professor": str,      # parsed from the file header
            "department": str,     # parsed from the file header
            "chunk_index": int,    # position within the whole file
        }
    The header block (ratings summary) is treated as the file's first block so
    that overall-rating queries can still match it.
    """
    chunks = []
    paths = sorted(glob.glob(os.path.join(documents_dir, "*.txt")))

    for path in paths:
        source = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        # Split on a `---` line into blocks (header + individual reviews).
        blocks = [b.strip() for b in raw.split("\n---\n")]
        blocks = [b for b in blocks if b]
        if not blocks:
            continue

        professor, department = parse_header(blocks[0])

        chunk_index = 0
        for block in blocks:
            for chunk in chunk_text(block):
                chunks.append({
                    "text": chunk,
                    "source": source,
                    "professor": professor,
                    "department": department,
                    "chunk_index": chunk_index,
                })
                chunk_index += 1

    return chunks


if __name__ == "__main__":
    all_chunks = load_documents()
    print(f"Loaded {len(all_chunks)} chunks from {DOCUMENTS_DIR}/\n")

    sample = random.sample(all_chunks, min(5, len(all_chunks)))
    for i, c in enumerate(sample, 1):
        print(f"--- Sample chunk {i} "
              f"[{c['professor']} | {c['source']} | idx {c['chunk_index']}] "
              f"({len(c['text'])} chars) ---")
        print(c["text"])
        print()
