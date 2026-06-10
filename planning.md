# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools to generate
> your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

ULM professor and course reviews across departments. This knowledge is valuable because students need honest, student-sourced opinions about professors before registering — information that official channels like course catalogs and university websites never provide. Rate My Professors reviews, Reddit threads, and word-of-mouth are the real sources students rely on, but they're scattered, hard to search, and require reading through dozens of posts to find a specific answer. This system makes that knowledge directly queryable in plain language.

---

## Documents

| # | Source | Description | Location |
|---|--------|-------------|----------|
| 1 | Rate My Professors | Paul Wiedemeier — CS | documents/paul_wiedemeier.txt |
| 2 | Rate My Professors | Bontty — History | documents/bontty_history.txt |
| 3 | Rate My Professors | Mallory Benedetto — Biology | documents/mallory_benedetto.txt |
| 4 | Rate My Professors | Neil White — Sociology | documents/neil_white.txt |
| 5 | Rate My Professors | John Sutherlin — Political Science | documents/john_sutherlin.txt |
| 6 | Rate My Professors | John Thibodeaux — Mathematics | documents/john_thibodeaux.txt |
| 7 | Rate My Professors | Stephanie Olmstead — Biology | documents/stephanie_olmstead.txt |
| 8 | Rate My Professors | Siva Murru — Chemistry | documents/siva_murru.txt |
| 9 | Rate My Professors | April Picard — Mathematics | documents/april_picard.txt |
| 10 | Rate My Professors | Ralph Brown — History | documents/ralph_brown.txt |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 50 characters

**Reasoning:**
Each review in these documents is short — typically 1 to 4 sentences covering one
specific opinion about a professor. A 400-character chunk is large enough to capture
a complete review in most cases, including any tags (e.g., TOUGH GRADER, TEST HEAVY)
that provide useful signal for retrieval. Going larger risks merging multiple unrelated
reviews into one chunk, which would dilute semantic meaning and make it harder to match
a specific query to the right content. Going smaller risks cutting a single review in
half, losing context.

The 50-character overlap ensures that if a review happens to fall across a chunk
boundary, the key content is still represented in at least one chunk. Reviews are
separated by `---` in the source files, which the ingestion pipeline will use as
natural split points before applying character-based chunking within each review block.

---

## Retrieval Approach

**Embedding model:** all-MiniLM-L6-v2 via sentence-transformers (runs locally, no API key)

**Top-k:** 5

**Production tradeoff reflection:**
For this project, all-MiniLM-L6-v2 is the right choice — it runs locally with no cost
or rate limits, and it performs well on short, informal English text like student reviews.
If deploying for real users at scale, I would weigh the following tradeoffs:

- **Context length:** all-MiniLM-L6-v2 has a 256-token limit, which is fine for short
  reviews but would truncate longer documents. A model like text-embedding-3-small from
  OpenAI supports up to 8191 tokens.
- **Accuracy on domain-specific text:** Student review language is informal and
  colloquial. A general-purpose model handles this reasonably well, but a model
  fine-tuned on educational or review text could improve retrieval precision.
- **Cost:** OpenAI embeddings cost per token. For a student project with moderate query
  volume, this is manageable, but for a high-traffic production system it adds up.
- **Latency:** Local models like all-MiniLM-L6-v2 avoid network round-trips, which
  matters for real-time query interfaces.
- **Multilingual support:** Not relevant here since all documents are in English, but
  a multilingual model like paraphrase-multilingual-MiniLM-L12-v2 would be needed for
  a broader deployment.

Top-k of 5 was chosen to give the LLM enough context to synthesize an answer across
multiple reviews without overwhelming the prompt with loosely related content. If
retrieval quality is poor, I will increase to 7 and re-evaluate.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Professor Wiedemeier's exams? | Exams are described as insanely difficult and unfair. Multiple reviews say he creates questions designed to trick students, and that his grading reflects his own views rather than objective correctness. |
| 2 | Is April Picard a good math professor for students who struggle with math? | Yes. Multiple reviews specifically mention students who previously failed or dropped math and succeeded with Picard. She is described as caring, accessible, and clear. |
| 3 | What are the main complaints about John Thibodeaux? | He refuses to answer questions or does so condescendingly. He knows the material but cannot explain it well. Many students fail or withdraw from his classes. |
| 4 | Does Dr. Sutherlin give feedback on assignments? | Yes. Multiple reviews say he grades quickly, provides detailed feedback, and will give early feedback if you submit ahead of the deadline so you can improve and resubmit. |
| 5 | What should students know before taking Neil White's sociology class? | No electronics are allowed. He gets sidetracked frequently and talks about personal stories, but the content from his lectures does appear on exams. Some reviews note uncomfortable comments toward certain students. |

---

## Anticipated Challenges

1. **Review splitting across chunk boundaries:** Some longer reviews in the documents
   span multiple sentences and could be cut mid-thought by the character-based chunker.
   This would produce a chunk that starts mid-sentence and lacks enough context to be
   retrieved accurately. Mitigation: use `---` delimiters as primary split points and
   only apply character chunking within each review block.

2. **Ambiguous professor references in queries:** A user might ask about "the math
   professor" or "the CS prof" without naming anyone. The embedding model would have
   no strong signal to match this to a specific professor's file, and retrieval could
   return a mix of reviews from multiple professors with low relevance scores. Mitigation:
   document this as a known limitation and instruct the LLM to ask for clarification
   when the query is ambiguous.

---

## Architecture

```
documents/*.txt
      |
      v
[ Document Ingestion ]
  Tool: Python (open / read)
  - Load each .txt file from the documents/ folder
  - Split on "---" delimiter to isolate individual reviews
  - Strip whitespace and remove empty blocks
      |
      v
[ Chunking ]
  Tool: Python (custom chunk_text function)
  - Chunk size: 400 characters
  - Overlap: 50 characters
  - Attach metadata: source filename, professor name, chunk index
      |
      v
[ Embedding + Vector Store ]
  Tool: sentence-transformers (all-MiniLM-L6-v2) + ChromaDB
  - Embed each chunk using SentenceTransformer("all-MiniLM-L6-v2")
  - Store vectors + metadata in a local ChromaDB collection
      |
      v
[ Retrieval ]
  Tool: ChromaDB query
  - Accept a plain-language user query
  - Embed the query using the same model
  - Return top-5 most similar chunks with source metadata
      |
      v
[ Generation ]
  Tool: Groq API (llama-3.3-70b-versatile)
  - Build a prompt with retrieved chunks as context
  - Instruct the model to answer only from provided context
  - Return answer + list of source documents
      |
      v
[ Query Interface ]
  Tool: Gradio
  - Text input for user query
  - Text output for answer
  - Text output for sources
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
I will give Claude this planning.md (the Documents section, Chunking Strategy section,
and Architecture diagram) and ask it to implement two things: (1) an `ingest.py` script
that loads all `.txt` files from the `documents/` folder, splits on `---` delimiters,
strips whitespace, and returns a list of review blocks with source metadata attached,
and (2) a `chunk_text()` function that takes a review block and splits it into chunks
of 400 characters with 50-character overlap. I will verify the output by printing 5
random chunks and confirming each one is a complete, readable review fragment with
source metadata attached.

**Milestone 4 — Embedding and retrieval:**
I will give Claude the Retrieval Approach section and Architecture diagram and ask it
to implement `embed.py`, which loads chunks from the ingestion pipeline, embeds them
using all-MiniLM-L6-v2 via sentence-transformers, and stores them in a ChromaDB
collection with source filename and professor name as metadata. I will also ask it to
implement a `retrieve()` function that accepts a query string and returns the top-5
chunks with their source info and distance scores. I will verify by running 3 of my
evaluation questions and checking that the returned chunks are visibly relevant and
that distance scores are below 0.5.

**Milestone 5 — Generation and interface:**
I will give Claude the Generation section of the Architecture diagram plus the grounding
requirement (answers from retrieved context only, with source attribution) and ask it
to implement `query.py` with an `ask()` function that takes a user question, retrieves
top-5 chunks, builds a grounded prompt, calls the Groq API, and returns a dict with
`answer` and `sources` keys. I will also ask it to implement `app.py` as a Gradio
interface with a question input, answer output, and sources output. I will verify
grounding by asking a question not covered by any document and confirming the system
says it does not have enough information rather than generating a plausible-sounding
answer.