# Agentic Debugger

An autonomous, multi-tenant MLOps platform engineered to securely sandbox, evaluate, and self-correct runtime and compilation exceptions using an event-driven Finite State Machine (FSM), local vector memory caching (RAG), and deterministic open-source LLM orchestration.

Unlike stateless one-shot code assistants, this platform treats debugging as an evolutionary optimization process — isolating untrusted execution footprints inside strict container boundaries and recording structural trajectory states to learn from past debugging sessions.

---

## Motivation & Research Paradigm

Traditional LLM-based extensions are typically stateless: they analyze code statically, suggest free-form adjustments, and hold no cognitive memory of prior runtime or compilation failures. This project shifts the paradigm toward an execution-driven approach, addressing core research questions critical to modern autonomous systems design:

- **Debugging by Execution** — Can an AI agent converge on production-grade code modifications entirely through deterministic trial, sandboxed validation, and error-trace evaluation?
- **Evolutionary Memory** — Does semantic retrieval over past successful trajectories reduce multi-turn reasoning overhead and minimize token budgets for recurring exception patterns?
- **Ablation Under Bounds** — Which exception profiles (e.g., semantic logic bugs vs. structural syntax breaks) benefit most from a vectorized memory layer vs. raw model inference?

---

## System Architecture

The platform cleanly decouples its **Control Plane** (state management and orchestration) from its **Compute Plane** (isolated, transient execution micro-environments) to guarantee complete host isolation, zero side-effects, and horizontal runtime scaling.

```
                              [ EVALUATION SUITE ]
                                      │
                  Spawns multiple parallel test instances
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY (FastAPI)                        │
│  Ingests multi-tenant code submissions & manages task queues        │
│  via BackgroundTasks                                                │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION PLANE (Agent Core)                  │
│  Drives the event FSM, captures system state metrics,               │
│  logs training trajectories                                         │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
┌──────────────────────────────┐     ┌───────────────────────────────┐
│       COMPUTE SANDBOX        │     │      EVOLUTIONARY MEMORY      │
│  Isolated, transient Docker  │     │  ChromaDB vector persistence  │
│  container runtimes          │     │  for multi-agent historical   │
│                              │     │  lookups                      │
└──────────────────────────────┘     └───────────────────────────────┘
```

---

## Core Execution Subsystems

| Plane | Component | Role |
|---|---|---|
| Control | FSM Orchestrator | Drives a closed-loop, event-driven state matrix via a custom lightweight transition engine, eliminating loop deadlocks by enforcing deterministic state changes based on explicit execution tokens |
| Compute | Isolation Sandbox | Abstracted through a unified language factory runner; forces all compilation and runtime cycles into temporary, unprivileged Docker containers |
| Memory | Vector RAG Core | Indexes successful multi-step trajectory repairs into a vector space, surfacing past solutions to guide current debugging passes |
| Data | Telemetry Tracer | Profiles high-precision state execution intervals, code mutation magnitude, and token expenditure efficiency metrics per job |

---

## Production Infrastructure Stack

### 1. Hardened Compute Sandboxing

Untrusted source payloads are mounted and executed via the official Docker SDK within an isolated Linux container built on `python:3.11-slim`.

- **Security Constraints:** Containers execute with disabled network interfaces (`network_disabled=True`), strict runtime memory ceilings (`mem_limit="128m"`), and a dedicated non-root system profile (`sandbox_user`) to guarantee container escape prevention.
- **Volume Isolation:** Target directories are absolute-resolved and bound to the container as strictly read-only paths (`mode: "ro"`).
- **Chained Multi-Step Execution (C++):** To execute multi-step workflows (e.g., compiling via `g++` and running the binary) without violating read-only storage permissions, commands are piped into a unified bash payload redirecting outputs to isolated scratch partitions:

```bash
/bin/sh -c "g++ -Wall target.cpp -o /tmp/temp_exec && /tmp/temp_exec"
```

---

### 2. Event-Driven Finite State Machine (FSM)

The agent loop transitions sequentially across a strict structural graph via Python pattern matching, avoiding the architectural fragility of generic agentic prompt chains.

| State | Operational Action |
|---|---|
| `READY` | Invokes `RunnerFactory` to map runtime contexts and trigger containerized execution |
| `OBSERVED` | Evaluates the captured `ExecutionResult` to trigger either progress or halting vectors |
| `EVALUATED` | Reads fresh file text from disk and queries vector memory for context injection |
| `ACTION_SELECTED` | Queries the local Ollama daemon (`qwen2.5-coder:7b`) with temperature locked to `0.0` |
| `ACTED` | Applies regex string parsing to isolate the code fence and overwrite the disk scratch path in-place |
| `TERMINATED` | Sink state — safe resource de-allocation and trajectory dataset serialization |

---

### 3. Local Vector Memory Cache

When a complex exception is successfully resolved across multi-turn iterations, the initial `stderr` footprint is indexed alongside the working patch payload within a local ChromaDB persistence layer.

- **Semantic Vectorization:** Maps raw text onto a 384-dimensional dense coordinate matrix using a local Hugging Face `all-MiniLM-L6-v2` SentenceTransformer.
- **Heuristic Filter Gate:** Distance lookups are constrained by an explicit cosine similarity threshold ($\leq 0.55$) to prevent false-positive context pollution.

---

### 4. Asynchronous Multi-Tenant Web Gateway

To scale beyond blocking single-file command-line execution, the platform implements an **Asynchronous Job-Polling Pattern** via FastAPI and Uvicorn.

- **Non-Blocking Queueing:** Multi-tenant payloads are ingested via async endpoints, mapped to unique filesystem workspaces, and offloaded to worker pools via `BackgroundTasks`. Clients receive an immediate `202 Accepted` tracking token.

---

## Telemetry & Mathematical Optimization Metrics

The analytical tracer layer (`agent/telemetry.py`) records precise execution graphs per job.

### Code Mutation Magnitude

Measures how structurally distinct the repaired code asset is from its initial broken snapshot:

$$\Delta \text{Code Similarity} = 1.0 - \text{SequenceMatcher}(\text{initial\_code},\ \text{patched\_code}).\text{ratio}()$$

### Token Expenditure Efficiency Index

Character-to-token allocation heuristic for estimating local offline endpoint usage:

$$\text{Estimated Tokens} = \frac{\text{Length of String in Characters}}{4}$$

Combined resource optimization weight score:

$$\text{Token Expenditure Efficiency Score} = \frac{\Delta \text{Code Similarity}}{\text{Total Combined Tokens Expended}} \times 1000$$

---

## Empirical Benchmarking Suite

The validation harness (`evaluate.py`) duplicates target code assets into isolated execution spaces, schedules parallel evaluation runs, aggregates telemetry, and compiles structural reports alongside visualization scatter plots.

```
[+] Automated markdown metric report compiled successfully → evaluation_report.md
[+] System analytics visualization asset rendered securely → analytics_chart.png
```

### Sample Report (`evaluation_report.md`)

**High-Level Performance Summary**

| Metric | Value |
|---|---|
| Overall System Convergence Rate | 66.67% |
| Average Python Latency | 1250.20 ms |
| Average C++ Latency | 4500.50 ms |

**RAG Cache Optimization Gains**

| Metric Dimension | Cache Hits (Active Memory) | Cache Misses (Cold Cache) |
|---|---|---|
| Average Retry Loop Allocation | 1.00 cycles | 3.00 cycles |
| Token Expenditure Efficiency Score | 85.50 | 0.00 |

---

## Platform Boundaries & Scope

### Supported Exception Profiles

| Category | Examples |
|---|---|
| Syntax Breaks | Missing definitions, trailing block errors, invalid syntax boundaries |
| Environment Name Crashes | Reference faults, uninitialized variables (`NameError`) |
| Type System Inconsistencies | Multi-type concatenations, illegal primitive conversions (`TypeError`) |
| Boundary Exceptions | Out-of-bounds iterable operations, key mapping misses (`IndexError`, `KeyError`) |

### Guardrails & Limitations

This system is a research-focused MLOps artifact designed for studying agentic optimization behavior under strict constraints. It does not target multi-file architectural defects, complex distributed deadlocks, or deep algorithmic/logical business bugs where execution output passes cleanly but semantic intent is broken.

---

## Repository Architecture

```
agentic-debugger/
├── agent/
│   ├── agent.py            # FSM Loop Orchestrator (Telemetry & Memory Hooks)
│   ├── states.py           # Event-Driven State Matrix Transition Gates
│   ├── memory.py           # ChromaDB Cosine Vector Space Memory Integration
│   ├── telemetry.py        # High-Precision Tracer & Code Delta Calculation
│   └── llm_agent.py        # Stateless Ollama Client Completion API Wrapper
├── core/
│   ├── sandbox/
│   │   ├── Dockerfile      # Secure Non-Root Linux Isolation Container Configuration
│   │   └── docker_engine.py# Docker SDK Resource Constraint Volume Mounter
│   ├── runners/            # Decoupled Language Interpreters (python_runner.py / cpp_runner.py)
│   └── patcher.py          # Regex Fenced Markdown Parsing Target Overwriter
├── data/
│   ├── benchmarks/         # Base Directory for Source Error Assets Suite
│   ├── evaluation_scratch/ # Isolated Runtime Temporary Directories
│   ├── telemetry/          # Serialized Structural JSON Trajectory Logs
│   └── chroma_db/          # Persistent Local Vector Storage Binaries
├── app.py                  # Async FastAPI Microservice Web Gateway
├── evaluate.py             # Empirical System Benchmarking Framework
└── generate_benchmarks.py  # Automation Target Suite Bug Creator
```