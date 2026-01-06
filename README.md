# Agentic Debugger

**Agentic Debugger** is a self-improving AI agent that iteratively debugs Python code by executing programs, analyzing runtime errors, applying fixes, and learning from past debugging sessions.

Unlike one-shot code assistants, this system follows an **agentic loop**: it runs buggy code in a sandboxed environment, forms hypotheses about failures, attempts fixes, re-runs the code, and repeats until the issue is resolved or a stopping condition is met. Successful debugging sessions are stored as structured traces and reused via retrieval and fine-tuning to improve future performance.

---

## Motivation

Debugging is repetitive, time-consuming, and often follows similar patterns across projects. While modern LLM-based tools can suggest fixes, they are typically **stateless** and do not learn from prior debugging experience.

This project explores a different direction:

- Can an AI agent **debug by execution**, not just suggestion?
- Can it **learn debugging strategies from its own successful runs**?
- How much do **memory (RAG)** and **fine-tuning** improve agentic debugging performance over time?

---

## High-Level Architecture

At a high level, the system consists of:

1. **Execution Sandbox**  
   Runs Python code safely and captures runtime errors, outputs, and traces.

2. **Agent Loop**  
   Iteratively performs:
   - Error analysis  
   - Hypothesis generation  
   - Fix application  
   - Re-execution and evaluation  

3. **Debugging Memory (RAG)**  
   Stores successful debugging traces and retrieves similar past fixes to guide future attempts.

4. **Learning Loop (Fine-Tuning)**  
   Periodically fine-tunes a code-focused LLM on high-quality debugging trajectories collected by the agent.

5. **Evaluation Suite**  
   Benchmarks agent performance across different bug categories and tracks improvement over time.

---

## Current Status

🚧 **Work in progress**

Planned milestones:
- [ ] Basic agent loop with execution and retry logic  
- [ ] Sandboxed code execution  
- [ ] Structured logging of debugging traces  
- [ ] Retrieval over past debugging sessions  
- [ ] Fine-tuning on self-generated traces  
- [ ] Evaluation on a fixed Python bug benchmark  

---

## Scope (Initial)

- **Language:** Python  
- **Bug types (initial focus):**
  - Syntax errors  
  - Name / variable errors  
  - Type errors  
  - Index / key errors  
  - Simple runtime exceptions  

This project does **not** aim to solve all debugging problems or complex algorithmic logic bugs. The goal is to study **agentic debugging behavior in a controlled setting**.

---

## Research Questions

Some of the questions this project explores:

- Does retrieval over past debugging experiences improve success rates?
- Does fine-tuning on self-generated debugging traces lead to measurable gains?
- Which bug categories benefit most from memory vs fine-tuning?
- What failure modes emerge in agentic debugging systems?

---

## Tech Stack (Planned)

- Python 3.11+
- LangChain (agent framework)
- Docker (sandboxed execution)
- Hugging Face Transformers + PEFT (LoRA fine-tuning)
- Sentence Transformers (embeddings)
- Chroma / FAISS (vector database)
- FastAPI / CLI (interface)

---

## Disclaimer

This is a research and learning project.  
The system is **not intended to replace professional debugging tools** and may produce incorrect or incomplete fixes.

---

## License

MIT
