# Agentic Debugger

A self-improving AI agent that debugs Python and C++ code by running programs, analyzing runtime errors, applying fixes, and learning from past sessions.

Unlike one-shot code assistants, it follows an agentic loop: run buggy code in a sandbox, form a hypothesis about the failure, attempt a fix, re-run, and repeat — until the issue is resolved or a stopping condition is met. Successful debugging sessions are stored as structured traces, then reused via retrieval and fine-tuning to improve future runs.

---

## Motivation

Traditional LLM-based code tools are stateless. They analyze code statically, suggest edits, and carry no memory of prior runtime failures. This project takes an execution-driven approach and addresses three core questions:

- **Debugging by Execution** — Can an agent converge on correct code purely through sandboxed trial, error-trace evaluation, and iterative patching?
- **Evolutionary Memory** — Does semantic retrieval over past successful trajectories reduce multi-turn reasoning overhead for recurring exception patterns?
- **Ablation Under Bounds** — Which exception profiles (e.g., semantic logic bugs vs. structural syntax errors) benefit most from a vector memory layer vs. raw model inference?

---

## Architecture

The system separates its **Control Plane** (state management and orchestration) from its **Compute Plane** (isolated, transient execution environments) to guarantee host isolation, zero side-effects, and horizontal scaling.

```
                           [ EVALUATION SUITE ]
                                    │
                Spawns multiple parallel test instances
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                        │
│  Ingests multi-tenant code submissions & manages task queues      │
│  via BackgroundTasks                                              │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────┐
│                 ORCHESTRATION PLANE (Agent Core)                  │
│  Drives the event FSM, captures system state metrics,             │
│  logs training trajectories                                       │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌──────────────────────────┐                   ┌───────────────────────────────┐
│     COMPUTE SANDBOX      │                   │      EVOLUTIONARY MEMORY      │
│  Isolated, transient     │                   │  ChromaDB vector persistence  │
│  Docker container        │                   │  for multi-agent historical   │
│  runtimes                │                   │  lookups                      │
└──────────────────────────┘                   └───────────────────────────────┘
```

### Core Subsystems

| Plane | Component | Role |
|---|---|---|
| Control | FSM Orchestrator | Drives a closed-loop, event-driven state machine via a lightweight transition engine. Eliminates loop deadlocks by enforcing deterministic state changes via explicit execution tokens. |
| Compute | Isolation Sandbox | Abstracts language runtimes through a unified factory runner. All compilation and execution cycles run inside temporary, unprivileged Docker containers. |
| Memory | Vector RAG Core | Indexes successful multi-step trajectory repairs into a vector space, surfacing past solutions to inform current debugging passes. |
| Data | Telemetry Tracer | Profiles state execution intervals, code mutation magnitude, and token expenditure per job. |
| Learning | Dataset & Tuning Pipeline | Curates successful multi-turn trajectory logs into ShareGPT format and runs parameter-efficient optimization via low-rank adapters. |

---

## Production Infrastructure

### 1. Compute Sandboxing

Untrusted code is mounted and executed via the Docker SDK inside an isolated Linux container built on `python:3.11-slim`.

- **Security constraints:** Containers run with network disabled (`network_disabled=True`), a hard memory ceiling (`mem_limit="128m"`), and a non-root system profile (`sandbox_user`).
- **Volume isolation:** Target directories are absolute-resolved and mounted as read-only (`mode: "ro"`).
- **Chained execution (C++):** Multi-step workflows (compile + run) are piped into a single bash payload that redirects outputs to an isolated scratch partition:

```bash
/bin/sh -c "g++ -Wall target.cpp -o /tmp/temp_exec && /tmp/temp_exec"
```

- **Fault-tolerant named pipes:** Windows pipe connection drops (`ConnectionError` / `ReadTimeout`) on hard processing timeouts are caught, the runaway process is force-killed, and the lifecycle state maps to POSIX exit code `124`.

---

### 2. Event-Driven Finite State Machine

The agent loop transitions across a strict state graph via Python pattern matching, avoiding the fragility of generic prompt chains.

| State | Action |
|---|---|
| `READY` | Invokes `RunnerFactory` to map the runtime context and trigger containerized execution. |
| `OBSERVED` | Evaluates the captured `ExecutionResult` to trigger either a progress or halting vector. |
| `EVALUATED` | Reads fresh file text from disk and queries vector memory for context injection. |
| `ACTION_SELECTED` | Queries the local Ollama daemon (`qwen2.5-coder:7b`) with temperature locked to `0.0`. |
| `ACTED` | Applies regex parsing to isolate the code fence and overwrites the disk scratch path in-place. |
| `TERMINATED` | Sink state — resource de-allocation, metric calculation, and trajectory dataset serialization. |

---

### 3. Vector Memory Cache

When a complex exception is resolved across multiple iterations, the initial `stderr` footprint is indexed alongside the working patch in a local ChromaDB persistence layer.

- **Semantic vectorization:** Raw text maps to a 384-dimensional dense vector using `all-MiniLM-L6-v2` (SentenceTransformers).
- **Heuristic filter gate:** Distance lookups apply a cosine similarity threshold (≤ 0.55) to prevent false-positive context injection.

---

### 4. Async Multi-Tenant Web Gateway

The platform implements an async job-polling pattern via FastAPI and Uvicorn.

- Multi-tenant payloads are ingested via async endpoints, mapped to unique filesystem workspaces, and offloaded to worker pools via `BackgroundTasks`.
- Clients receive an immediate `202 Accepted` tracking token.

---

### 5. Trajectory Curation & PEFT Fine-Tuning

**`build_dataset.py`** — Processes raw telemetry logs, isolates successful traces, parses prompt-response pairs from `ACTION_SELECTED` frames, and compiles them into a ShareGPT JSONL dataset.

**`finetune.py`** — Runs a parameter-efficient training harness targeting base models (e.g., `Qwen/Qwen2.5-Coder-1.5B`). Features `bfloat16`/`fp16` precision, gradient checkpointing, and LoRA adapters targeting attention layers (`q_proj`, `v_proj`, `k_proj`, `o_proj`).

---

## Telemetry & Metrics

The tracer layer (`agent/telemetry.py`) records execution graphs per job.

**Code Mutation Magnitude** — Measures how structurally different the patched code is from the initial broken snapshot:

```
ΔCode Similarity = 1.0 - SequenceMatcher(initial_code, patched_code).ratio()
```

**Token Expenditure Estimate** — Character-to-token heuristic for local offline endpoint usage:

```
Estimated Tokens = len(string) / 4
```

**Token Expenditure Efficiency Score** — Combined resource optimization weight:

```
Efficiency Score = (ΔCode Similarity / Total Tokens Expended) × 1000
```

---

## Benchmarking

`evaluate.py` duplicates target code assets into isolated execution spaces, schedules parallel evaluation runs, aggregates telemetry, and compiles reports with visualization scatter plots.

```
[+] Automated markdown metric report compiled → evaluation_report.md
[+] System analytics visualization rendered  → analytics_chart.png
```

### Sample Report (`evaluation_report.md`)

**High-Level Performance**

| Metric | Value |
|---|---|
| Overall System Convergence Rate | 88.89% |
| Average Python Latency | 3705.14 ms |
| Average C++ Latency | 62187.46 ms |

**RAG Cache Impact**

| Metric | Cache Hits | Cache Misses |
|---|---|---|
| Average Retry Loop Allocation | 1.00 cycles | 1.25 cycles |
| Token Expenditure Efficiency Score | 0.66 | 0.04 |

---

## Supported Exception Profiles

| Category | Examples |
|---|---|
| Syntax Breaks | Missing definitions, trailing block errors, invalid syntax boundaries |
| Name Crashes | Reference faults, uninitialized variables (`NameError`) |
| Type Inconsistencies | Multi-type concatenations, illegal primitive conversions (`TypeError`) |
| Boundary Exceptions | Out-of-bounds iterable operations, key mapping misses (`IndexError`, `KeyError`) |

---

## Scope & Limitations

This is a research-focused MLOps artifact for studying agentic optimization behavior under strict constraints. It does not target:

- Multi-file architectural defects
- Complex distributed deadlocks
- Deep algorithmic or logical bugs where execution passes but semantic intent is broken

---

## Repository Structure

```
agentic-debugger/
├── agent/
│   ├── agent.py            # FSM loop orchestrator (telemetry & memory hooks)
│   ├── states.py           # Event-driven state machine transition gates
│   ├── memory.py           # ChromaDB cosine vector space memory
│   ├── telemetry.py        # High-precision tracer & code delta calculation
│   ├── llm_agent.py        # Stateless Ollama client completion API wrapper
│   └── evaluate.py         # Empirical benchmarking framework
├── core/
│   ├── sandbox/
│   │   ├── Dockerfile      # Secure non-root Linux container configuration
│   │   └── docker_engine.py# Docker SDK fault-tolerant sandbox mounter
│   ├── runners/            # Decoupled language runners (python_runner.py / cpp_runner.py)
│   └── patcher.py          # Regex fenced markdown parsing & file overwriter
├── train/
│   ├── build_dataset.py    # Trajectory filtering & ShareGPT JSONL compiler
│   └── finetune.py         # PEFT LoRA Hugging Face training harness
├── data/
│   ├── benchmarks/         # Source error asset suite
│   ├── evaluation_scratch/ # Isolated runtime temporary directories
│   ├── telemetry/          # Serialized JSON trajectory logs
│   ├── chroma_db/          # Persistent local vector storage
│   └── tuning_dataset.jsonl# Instruction fine-tuning dataset
├── models/
│   └── patched_qwen_lora/  # LoRA checkpoints & weights
└── app.py                  # Async FastAPI web gateway
```

---

## What Changed

The original project was a stateless outline — no real execution, no memory, no sandboxing. Here's what was built on top of it.

**FSM orchestration (was: simulated stubs)**
Ripped out the fake execution wheels and replaced them with a real event-driven FSM. States transition via Python pattern matching — `READY` → `OBSERVED` → `EVALUATED` and so on. No loose prompt chains, no state drift, no getting stuck in a loop.

**Docker sandboxing + Windows pipe handling (was: local script execution)**
Moved all code execution into Docker containers via the SDK. Volumes mount read-only, containers run as a non-root `sandbox_user`, memory is capped at 128MB, network is off. On Windows, named-pipe drops mid-execution (`ConnectionError` / `ReadTimeout`) were silently crashing runs — added a wrapper that catches those, kills the container cleanly, and surfaces a POSIX `124` timeout instead.

**Async API gateway (was: blocking CLI)**
Rewrote the entry point as a FastAPI + Uvicorn service. Each submission gets its own workspace, gets queued via `BackgroundTasks`, and returns a `202` immediately. No blocking, no queuing issues under parallel load.

**Telemetry (was: print statements)**
`agent/telemetry.py` now tracks per-job latency, code mutation magnitude (sequence similarity between input and patched output), and a token efficiency score. Useful for spotting which exception types cost the most.

**Vector memory / RAG (was: none)**
Each successfully resolved exception gets its `stderr` + working patch indexed into ChromaDB using `all-MiniLM-L6-v2`. On future runs, similar errors pull from cache instead of burning through retry cycles. The cosine similarity gate sits at ≤ 0.55 — below that it ignores the match rather than risk a bad injection. In benchmarks this pushed token efficiency from 0.04 to 0.66 — a **16.5x improvement** — and cut retries on repeat exceptions to a single cycle.

**Fine-tuning pipeline (was: none)**
`train/build_dataset.py` pulls successful traces out of telemetry logs and formats them as ShareGPT JSONL. `train/finetune.py` runs LoRA fine-tuning on top of `Qwen2.5-Coder-1.5B` — `bfloat16`/`fp16` and gradient checkpointing keep it runnable on consumer hardware.

---

## Dependencies

- **Python 3.11+**
- **Docker Desktop** — containers won't spin up without it
- **Ollama** — runs `qwen2.5-coder:7b` locally ([ollama.com](https://ollama.com))
- **Hugging Face** — `Qwen/Qwen2.5-Coder-1.5B` downloads automatically via `transformers` on first fine-tuning run

---

## Getting Started

### 1. Setup

Clone the repo, create a virtual environment, and install:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Pull the inference model:

```bash
ollama pull qwen2.5-coder:7b
```

---

### 2. Seed the Benchmarks

If `data/benchmarks/` is empty:

```bash
python generate_benchmarks.py
```

---

### 3. Run the Evaluation Suite

Runs the FSM across all 18 test scripts in Docker, collects metrics, and writes the charts:

```bash
python -m agent.evaluate
```

Outputs: `evaluation_report.md` (convergence metrics) and `analytics_chart.png` (latency vs. retry boundaries).

---

### 4. Start the Web Gateway

```bash
uvicorn app:app --reload --port 8000
```

Swagger UI at `http://127.0.0.1:8000/docs`.

---

### 5. Fine-Tuning

```bash
# Build the dataset from telemetry logs
python -m train.build_dataset

# Run LoRA fine-tuning
python -m train.finetune
```