"""Milestone 5 — Gradio query interface for The Unofficial Guide.

    python app.py
Then open http://localhost:7860
"""

import gradio as gr

from query import ask


def answer_question(question):
    if not question or not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"- {s}" for s in result["sources"])
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide — ULM Professor Reviews") as demo:
    gr.Markdown("# The Unofficial Guide\nAsk about ULM professors, "
                "answered only from student reviews.")
    question = gr.Textbox(label="Your question", lines=2)
    ask_btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Sources", lines=4)

    ask_btn.click(fn=answer_question, inputs=question,
                  outputs=[answer, sources])
    question.submit(fn=answer_question, inputs=question,
                    outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch(server_name="localhost", server_port=7860)
