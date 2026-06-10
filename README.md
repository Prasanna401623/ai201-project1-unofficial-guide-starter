# The Unofficial Guide — Project 1

A retrieval-augmented question-answering system over student reviews of ULM professors.

---

## Domain

ULM professor and course reviews. Students need honest opinions about professors before registering, but official channels don't provide this. Reviews from Rate My Professors are scattered and hard to search — this system makes them queryable in plain language.

---

## Document Sources

10 `.txt` files manually collected from Rate My Professors, one per professor.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors | Paul Wiedemeier (CS) | documents/paul_wiedemeier.txt (https://www.ratemyprofessors.com) |
| 2 | Rate My Professors | Bontty (History) | documents/bontty_history.txt (https://www.ratemyprofessors.com) |
| 3 | Rate My Professors | Mallory Benedetto (Biology) | documents/mallory_benedetto.txt (https://www.ratemyprofessors.com) |
| 4 | Rate My Professors | Neil White (Sociology) | documents/neil_white.txt (https://www.ratemyprofessors.com) |
| 5 | Rate My Professors | John Sutherlin (Political Science) | documents/john_sutherlin.txt (https://www.ratemyprofessors.com) |
| 6 | Rate My Professors | John Thibodeaux (Math) | documents/john_thibodeaux.txt (https://www.ratemyprofessors.com) |
| 7 | Rate My Professors | Stephanie Olmstead (Biology) | documents/stephanie_olmstead.txt (https://www.ratemyprofessors.com) |
| 8 | Rate My Professors | Siva Murru (Chemistry) | documents/siva_murru.txt (https://www.ratemyprofessors.com) |
| 9 | Rate My Professors | April Picard (Math) | documents/april_picard.txt (https://www.ratemyprofessors.com) |
| 10 | Rate My Professors | Ralph Brown (History) | documents/ralph_brown.txt (https://www.ratemyprofessors.com) |

---

## Chunking Strategy

Split on `---` delimiters first to isolate individual reviews, then character-based chunking at 400 characters with 50-character overlap. Reviews are short and self-contained, so delimiter splitting keeps them intact.

**Chunk size:** 400 characters

**Overlap:** 50 characters

**Why these choices fit your documents:** Each review in these documents is short and self-contained, so splitting on the `---` delimiter first isolates one review per block and prevents two professors' reviews from merging into one chunk. Character-based chunking is applied within each block as a fallback for longer reviews.

**Final chunk count:** 176 total chunks

**Sample chunks:**

- **[paul_wiedemeier.txt]** "Course: CSCI4011 | Date: Feb 19, 2025 | Grade: A — Genuinely terrible. Creates exam questions he wants people to get wrong. His exams are insane and completely unfair. Tags: TOUGH GRADER, LECTURE HEAVY, TEST HEAVY"
- **[april_picard.txt]** "Course: MATH1031 | Date: Jul 23, 2021 | Grade: B+ — Mrs. Picard is one of the best Calculus teachers I've ever had. She provides video lectures, responds to emails quickly and cares about her students. Tags: GIVES GOOD FEEDBACK, LOTS OF HOMEWORK"
- **[neil_white.txt]** "Course: SOC1001 | Date: Jun 21, 2023 | Grade: B — Dr. White's class is mandatory to attend. There is assigned seating and he checks every day. Do not have any electronic devices out in class. Tags: PARTICIPATION MATTERS, BEWARE OF POP QUIZZES"
- **[john_thibodeaux.txt]** "Course: MATH1016 | Date: May 6, 2026 | Grade: D+ — I will simply say that if you plan on taking Math 1016 (Statistics) and actually learn the material and do well in the class, do not take John. He refuses to answer questions, blatantly refuses to. And when he does, he does so condescendingly and will laugh or scoff at you. Tags: TOUGH GRADER, LECTURE HEAVY, TEST HEAVY"
- **[john_sutherlin.txt]** "Course: POLS1001 | Date: May 6, 2026 | Grade: A+ — Very approachable and nice. Extremely experienced. He made learning the material actually enjoyable. By far the best professor I have ever had. Tags: PARTICIPATION MATTERS, AMAZING LECTURES, CARING"

---

## Embedding Model

**Model used:** all-MiniLM-L6-v2 via sentence-transformers. Runs locally, no API key.

**Production tradeoff reflection:** OpenAI's text-embedding-3-small has longer context and higher accuracy but costs money. Multilingual models like paraphrase-multilingual-MiniLM-L12-v2 would be needed for non-English content.

**Retrieval test results:**

- Query "What do students say about Wiedemeier's exams?" → top chunks from paul_wiedemeier.txt (distance 0.426, 0.464, 0.469), relevant because they directly discuss his exam style and difficulty.
- Query "Is April Picard good for students who struggle with math?" → all 5 chunks from april_picard.txt (distances 0.375–0.427), relevant because they describe her teaching style and accessibility.
- Query "What are the main complaints about Thibodeaux?" → top chunk was a positive review (distance 0.579), retrieval failed because no chunks use the word "complaints" and distances were all above 0.5.

---

## Grounded Generation

**System prompt grounding instruction:** The system prompt instructs the LLM: "Answer the question using only the information in the provided documents. If the documents don't contain enough information to answer, say: I don't have enough information on that."

**How grounding is enforced in the pipeline:** Retrieved chunks are injected into the prompt as numbered documents, and the system prompt explicitly prohibits the model from drawing on outside knowledge.

**How source attribution is surfaced in the response:** Tested with the out-of-scope query "What is the best restaurant near ULM?" — the system correctly refused.

**Example responses:**

- **Q:** "What do students say about Wiedemeier's exams?" → **A:** "Students say his exams are insane and completely unfair. He creates questions designed to trick students and has tested on material covered after the exam. Sources: paul_wiedemeier.txt"
- **Q:** "What is the best restaurant near ULM?" → **A:** "I don't have enough information on that. The provided documents do not mention restaurants near ULM." Sources: unrelated professor files (retrieval noise)

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Verdict |
|---|----------|-----------------|------------------------------|---------|
| 1 | What do students say about Wiedemeier's exams? | Exams described as insane, unfair, designed to trick students | Correct content, sources slightly noisy (Bontty/Brown leaked in) | Accurate |
| 2 | Is April Picard good for students who struggle with math? | Yes, multiple reviews of students who previously failed math and succeeded with Picard | Correct, clean retrieval, all sources from april_picard.txt | Accurate |
| 3 | What are the main complaints about Thibodeaux? | Refuses questions condescendingly, can't explain material well, many students fail or withdraw | LLM inferred from metadata only, no actual complaint reviews retrieved | Inaccurate |
| 4 | Does Dr. Sutherlin give feedback on assignments? | Yes, multiple reviews mention quick grading and detailed feedback | Correct, cited multiple Sutherlin reviews | Accurate |
| 5 | What should students know before taking Neil White's sociology class? | No electronics, assigned seating, lectures have tangents but content appears on exams | Correct and thorough, 8 specific points grounded in reviews | Accurate |

4/5 accurate.

---

## Failure Case Analysis

**Question that failed:** "What are the main complaints about Thibodeaux?"

**What the system returned:** The top result was actually a positive Thibodeaux review (distance 0.579), and distances were all above 0.5. The LLM inferred from metadata only, with no actual complaint reviews retrieved.

**Root cause (tied to a specific pipeline stage):** Query 3 failed because the word "complaints" does not appear in any review. The embedding model could not match the query to relevant chunks — this is a vocabulary mismatch problem: students describe problems using words like "refuses to answer questions" or "can't explain" rather than "complaints."

**What you would change to fix it:** A hybrid search approach combining semantic and keyword (BM25) search would help here.

---

## Spec Reflection

**One way the spec helped you during implementation:** The planning.md spec helped by identifying the `---` delimiter structure early — that decision shaped the entire ingestion pipeline.

**One way your implementation diverged from the spec, and why:** The plan specified 400-char chunking with 50-char overlap, but in practice most reviews fit in one chunk naturally, so the overlap rarely triggered. The chunking is effectively per-review rather than per-character.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Documents section and Chunking Strategy from planning.md, asking it to implement `ingest.py` and `chunk.py`.
- *What it produced:* Claude generated the `---` delimiter split logic correctly but initially used pure character chunking, which produced mid-sentence fragments.
- *What I changed or overrode:* Overrode this to treat each review as one chunk unless it exceeded 800 characters.

**Instance 2**

- *What I gave the AI:* The Architecture diagram and Retrieval Approach section, asking it to implement `embed.py`, `retrieve.py`, `query.py`, and `app.py`.
- *What it produced:* The generated grounding prompt was correct, but the sources list included noise from weak retrieval matches.
- *What I changed or overrode:* Did not override this — documented it as a known limitation instead.

---

## Query Interface

A Gradio web UI at http://localhost:7860.

- **Input:** a textbox labeled "Your question"
- **Outputs:** "Answer" (8 lines) and "Sources" (4 lines)
- **Usage:** the user types a question and clicks **Ask** or presses Enter.
