# LUCY — Living Unified Cognitive Yield

> **Offline-first, deterministic, safety-gated cognitive operating assistant and modular multi-agent runtime foundation.**

![Python](https://img.shields.io/badge/Python-3.10%2B-00c8ff?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-00e5a0?style=flat-square&logo=flask&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-923%20Passing-00e5a0?style=flat-square)
![Mode](https://img.shields.io/badge/Runtime-Safe%20Local%20First-f5c842?style=flat-square)
![Status](https://img.shields.io/badge/Status-Recovered%20V0.1%20Checkpoint%20023-purple?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Overview

**LUCY** (*Living Unified Cognitive Yield*) is a local-first cognitive architecture designed around **strict human agency, transparent local state, and deterministic safety boundaries**.

Unlike opaque cloud wrappers or unconstrained autonomous loops, LUCY operates on a living spine configuration (`data/spine.json`) enforced by a deterministic **Guardian** gate (`backend/lucy_core/guardian.py`). Every command, file read, memory mutation, and agent orchestration step is evaluated against a 5-tier permission model before execution.

### Core Design Principles
- **Transparent Local Cognition (Not Consciousness):** All working thoughts, drives, focus states, and memory lessons are stored in human-readable local JSON stores (`data/lucy/`).
- **Deterministic Safety Gates (`GuardianCore`):** Hard-blocks silent file deletions, credential access, root shell execution, unauthorized financial/trading actions, and autonomous self-upgrades.
- **Sandboxed Workspace Awareness (`SafeFileToolbox`):** Read-only inspection restricted strictly to user-approved directories with automatic extension and sensitive-pattern filtering.
- **Multi-Provider LLM Isolation:** Supports optional external reasoning via **Groq**, **Google Gemini**, **NVIDIA NIM**, **OpenRouter**, and **SambaNova** with strict provider-identity boundaries and offline fallback.

---

## System Architecture

```text
                        ┌──────────────────────────────┐
                        │        data/spine.json       │
                        │ (Permissions, Rules, Agents) │
                        └──────────────┬───────────────┘
                                       │
       ┌───────────────────────────────┼───────────────────────────────┐
       ▼                               ▼                               ▼
┌─────────────┐                 ┌─────────────┐                 ┌─────────────┐
│  Web UI /   │                 │  CLI REPL   │                 │  Native UI  │
│  REST API   │                 │  & Runner   │                 │  (Tkinter)  │
│ (Port 7700) │                 │(run_lucy.py)│                 │ (Desktop)   │
└──────┬──────┘                 └──────┬──────┘                 └──────┬──────┘
       └───────────────────────────────┼───────────────────────────────┘
                                       ▼
                        ┌──────────────────────────────┐
                        │        CommandRouter         │
                        │  (Intent & Command Dispatch) │
                        └──────────────┬───────────────┘
                                       ▼
                        ┌──────────────────────────────┐
                        │        GuardianCore          │
                        │ (Levels 0-4 Safety Gate)     │
                        └──────────────┬───────────────┘
                                       ▼
                        ┌──────────────────────────────┐
                        │         LucyRuntime          │
                        │  Stages 1–34 Core Subsystems │
                        └──────────────┬───────────────┘
         ┌──────────────────┬──────────┴───────────┬──────────────────┐
         ▼                  ▼                      ▼                  ▼
  ┌─────────────┐    ┌─────────────┐        ┌─────────────┐    ┌─────────────┐
  │ Memory &    │    │ Safe File   │        │ Cognition & │    │ Sub-Agents  │
  │ Deep Recall │    │ Toolbox     │        │ Daily Brief │    │ & LLM APIs  │
  └─────────────┘    └─────────────┘        └─────────────┘    └─────────────┘
```

---

## 10-Part Build Series & Evolution Roadmap

LUCY is built in a disciplined, progressive multi-part architecture where each layer must be stabilized before introducing higher-autonomy capabilities:

```text
Part 0: Living Spine Config (Rules, Boundaries, Agent Map) ──► COMPLETE
Part 1: Core Runtime Prototype & Inactive Agent Foundation ─► COMPLETE
Part 2: Active Operator Foundation & Safe Local Tools ──────► COMPLETE
Part 3: Playground Review & Approval Pipeline ──────────────► COMPLETE
Part 4: NEXUS Routing & Provider Key Safety ────────────────► COMPLETE
Part 5: SABLE Safety Enforcer & Sandboxed Workspace Tools ──► COMPLETE
Part 6: ORBIT System Monitor & Memory-Aware Session Review ─► COMPLETE
Part 7: HAVEN Health Diagnostics & Pattern Detection ───────► COMPLETE
Part 8: LEDGER Expense & Project Tracking ──────────────────► COMPLETE
Part 9: Full Absorption & Continuity Checkpoint Engine ─────► COMPLETE (Stages 1-34)
```

| Part | Milestone | Description | Status |
| :---: | :--- | :--- | :---: |
| **0** | **Spine Config & Living API** | Foundation rules, permission tiers, agent map, and web dashboard | **Completed** |
| **1** | **Memory System & Runtime** | Checkpoints, JSONL runtime logs, and approved facts engine | **Completed** |
| **2** | **ELIE Prototype** | Active assistant coordination layer and approval gates | **Completed** |
| **3** | **Playground Review System** | Action reports, validation, and multi-agent intent routing | **Completed** |
| **4** | **NEXUS Routing Layer** | Inter-agent event bus and external provider vault routing | **Completed** |
| **5** | **SABLE Safety Enforcer** | Read-only file tools, path validation, and boundary auditing | **Completed** |
| **6** | **ORBIT System Monitor** | Continuity pulses, rolling backups, and session reviews | **Completed** |
| **7** | **HAVEN Health Diagnostics** | 53 automated health checks, routine alignment, and daily briefs | **Completed** |
| **8** | **LEDGER Resource Tracker** | Project task tracking and resource auditing | **Completed** |
| **9** | **Lucy Integration** | Lesson absorption, self-model, and overnight checkpoint engine | **Completed** |

---

### Part 0 — Spine Config & Living API

The living spine config (`data/spine.json`) serves as Lucy's single source of truth for rules, boundaries, permissions, and agent stages.

#### Design Decisions
- **Why JSON, not a database?** At the foundation phase, configurations must be human-readable, directly editable, and git-versionable without migrations or ORM overhead.
- **Why Flask?** Lightweight, simple, transparent, and easy to extend without unnecessary boilerplate.
- **Why a Web Dashboard?** Provides an instant visual interface to inspect permissions, agent stages, and safety rules without requiring complex terminal setups.

#### Core REST Endpoints (`backend/server.py`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status` | Quick system overview, stage counts, and phase status |
| `GET` | `/api/spine` | Full `data/spine.json` living configuration |
| `GET` | `/api/lucy` | Core Lucy metadata and security locks |
| `GET` | `/api/agents` | All 14 planned agents and their metadata |
| `GET` | `/api/agents/<id>` | Detail for a specific agent |
| `PATCH` | `/api/agents/<id>/stage` | Update an agent's stage (requires `{"confirmed": true}`) |
| `GET` | `/api/safety` | Active safety rules (`absolute_never`, `always_safe`) |
| `GET` | `/api/permissions` | Permission Levels 0–4 specifications |
| `POST` | `/api/chat` | Send a command or prompt to `CommandRouter` |

To update an agent's stage when a milestone is genuinely reached:
```bash
curl -X PATCH http://localhost:7700/api/agents/ELIE/stage \
  -H "Content-Type: application/json" \
  -d '{"stage": "prototype", "confirmed": true, "reason": "First prototype working, logging actions"}'
```
*Note: The server automatically creates a timestamped backup of `spine.json` before any write.*

---

### Part 1 — LUCY Core Runtime Prototype

Part 1 introduces the **Core Runtime Prototype & Inactive Agent Foundation**:
- Loads the living spine config from Part 0
- Registers all 14 specialist agents safely as `inactive`
- Evaluates whether actions are safe, blocked, or require approval
- Records approval requests, local checkpoints, and JSONL runtime logs
- Validates system integrity via comprehensive health checks

#### Quick Start Commands:
```bash
python run_lucy_core.py status
python run_lucy_core.py spine
python run_lucy_core.py agents
python run_lucy_core.py agent ELIE
python run_lucy_core.py check "delete my files"
python run_lucy_core.py check "what is your status"
python run_lucy_core.py checkpoint "Foundation checkpoint"
python run_lucy_core.py health
```

---

### Checkpoint 1 — Local Operating Assistant Foundation

Extends the Part 1 runtime into a reliable, everyday local assistant:
- Interactive terminal chat (`python run_lucy.py` or `python run_lucy_core.py`)
- Web chat at `http://localhost:7700`
- Approved local memory store (`remember`, `recall`, `forget`, `memory audit`)
- Project and task tracking (`list projects`, `add task`, `show tasks`)
- Daily context and routine briefs (`daily brief`, `daily checkin`)
- Working thoughts and transparent cognition (`vision`, `think`, `thoughts`)

#### Useful Commands:
```bash
python run_lucy_core.py remember "Lucy operates local-first with deterministic safety"
python run_lucy_core.py recall "local-first"
python run_lucy_core.py forget "outdated note"
python run_lucy_core.py memory audit
python run_lucy_core.py list projects
python run_lucy_core.py add task "Review stage 34 health checks"
python run_lucy_core.py show tasks
python run_lucy_core.py daily checkin energy=8 sleep=good notes="stabilized guardian classifier"
python run_lucy_core.py daily brief
python run_lucy_core.py continuity status
python run_lucy_core.py backup memory
python run_lucy_core.py vision
python run_lucy_core.py think "What should Lucy focus on next?"
python run_lucy_core.py thoughts
```

---

### Checkpoint 2 — Safe Local Operator Tools (JARVIS-Style)

Brings safe local operator tooling closer to a desktop assistant while strictly gating dangerous operations:
- **Workspace Awareness:** Inspect, search, and summarize local project code within user-approved folders.
- **Knowledge Ingestion:** Build redacted local knowledge indexes from documents (metadata-only for secret/key files).
- **Cognition State:** Transparent local state tracking drives, vision, working thoughts, and focus without claiming artificial consciousness.
- **Safety Boundary:** Refuses outside-project file reads, sensitive filenames, and unapproved command execution.

#### Useful Commands:
```bash
python run_lucy_core.py dashboard
python run_lucy_core.py workspace
python run_lucy_core.py find file router
python run_lucy_core.py search text Guardian
python run_lucy_core.py read file README.md
python run_lucy_core.py system status
python run_lucy_core.py logs 5
python run_lucy_core.py approvals
python run_lucy_core.py approve <id-prefix>
python run_lucy_core.py reject <id-prefix>
python run_lucy_core.py add reminder "Update integration tests"
python run_lucy_core.py reminders
python run_lucy_core.py plan "Refactor command router helpers"
python run_lucy_core.py eat ai collections
python run_lucy_core.py ai collections status
python run_lucy_core.py search ai collections "provider vault"
```

---

### Recovered Lucy V0.1 Checkpoint 023 Architecture

Reconstructs Lucy's original checkpoint history map as an architectural reference:
- Preserves the recovered checkpoint lineage in `data/lucy/recovered_architecture.json`
- Establishes clear boundaries: Sub-agents (like ELIE) serve as modular assistants, not as Lucy's identity

#### Commands:
```bash
python run_lucy_core.py recovered
python run_lucy_core.py recovered checkpoints
python run_lucy_core.py brain status
python run_lucy_core.py ask "what is the current phase"
python run_lucy_core.py scan project
python run_lucy_core.py backup project
```

---

### External LLM Tools, Permanent Memory & Talking Style

Lucy can securely connect to external language providers (**NVIDIA NIM**, **Groq**, **OpenRouter**, **Google Gemini**, **SambaNova**) without leaking keys or letting an LLM hijack Lucy's identity:
- **Key Safety:** Keys are loaded via environment variables, session storage, or encrypted local storage.
- **Permanent Memory:** Saved in `data/lucy/memory/memory.json`.
- **Custom Style:** Talking style preferences live in `data/lucy/learning/talking_style.json`.
- **Fallback Proposals:** LLM suggestions are treated as candidate proposals, not authoritative truth.

#### Commands:
```bash
python run_lucy_core.py
# Inside Lucy REPL:
api tools
brain status
ask what can you help me with now?
learning status
permanent memory
learn style talk to me casually, clearly, and like an expert software engineer
style status
memory fallback what should Lucy remember about this repository
```

---

### Desktop UI & Overnight Checkpoint Builder

Lucy includes both a native desktop interface and an overnight checkpoint batch engine:

#### Start Native Desktop GUI:
```bash
python run_lucy_desktop.py
```

#### Run Overnight Checkpoints (up to 500 batches):
```bash
python run_lucy_core.py overnight checkpoints 100
python run_lucy_core.py learning status
python run_lucy_core.py health
```
*What the Overnight Builder does:*
- Builds incremental verified checkpoint records with local learning traces
- Runs health checks before and after every batch
- Keeps all protected actions strictly blocked
- Operates entirely offline without making unapproved API calls

---

## Permission Model (Levels 0–4)

Every action executed by LUCY or its sub-agents is governed by `data/spine.json`:

| Level | Name | Scope & Allowed Actions | Restrictions & Approval |
| :--- | :--- | :--- | :--- |
| **Level 0** | **Read-Only** | View status, read reports, logs, and checkpoints | Cannot write or execute anything |
| **Level 1** | **Log & Report** | Write logs, markdown notes, reports, and templates | Cannot delete files, edit configs, or run commands |
| **Level 2** | **Safe User Commands** | Run sandboxed scripts, create folders, manage project files | Cannot touch OS files, install global packages, or read secrets |
| **Level 3** | **Approved Project Edits** | Edit project configs, apply approved patches, update agent stages | Requires **explicit approval per action** |
| **Level 4** | **Root / Privileged** | System-level commands, OS config changes | Disabled by default; requires **explicit typed confirmation every time** |

---

## Planned 14-Agent Ecosystem

LUCY's spine orchestrates 4 core internal sub-agents (`Safety`, `Memory`, `Reasoning`, `Learning`) and defines the roadmap for 14 specialized domain agents:

| Order | ID | Full Name | Role |
| :---: | :--- | :--- | :--- |
| 1 | **ELIE** | Executive Liaison Intelligence Engine | Primary executive synthesis & task coordination |
| 2 | **RAY** | Reactive Automation Yield | Local workflow & task automation |
| 3 | **ARES** | Autonomous Research & Extraction System | Deep research, synthesis, and knowledge extraction |
| 4 | **VANTA** | Volatility Analysis & Tactical Allocation Agent | Risk modeling and analytical simulation |
| 5 | **HAVEN** | Health, Alignment, Vitality & Emotional Navigation | Daily energy, sleep, and routine alignment |
| 6 | **NEXUS** | Networked Exchange & Cross-agent Understanding | Inter-agent bus and context routing |
| 7 | **ECHO** | Experience Capture & Human Observation | Session reflection and communication adaptation |
| 8 | **LEDGER** | Life Economics, Debt & Growth Expense Recorder | Resource and budget tracking |
| 9 | **SABLE** | Security Analysis & Boundary Logic Engine | Threat modeling and boundary auditing |
| 10 | **ORBIT** | Operational Relay & Background Intelligence Tracker | Continuity pulses and scheduled reminders |
| 11 | **NOVA** | Navigation, Opportunity & Vision Assistant | Long-term strategy and project milestones |
| 12 | **MINT** | Managed Investment & Net-worth Tracker | Portfolio and asset analytics |
| 13 | **ATLAS** | Adaptive Transformation & Life Architecture System | Systems organization and structural planning |
| 14 | **JESTER** | Judgment, Error-Spotting & Tactical Evaluation | Red-teaming, shadow testing, and assumption checking |

---

## Directory Structure

```text
lucy/
├── backend/
│   ├── server.py                  # Flask REST API & Spine Config Server (Port 7700)
│   └── lucy_core/                 # Core Runtime Modules (Stages 1–34)
│       ├── lucy_runtime.py        # Main lifecycle & subsystem orchestrator
│       ├── router.py              # Command normalization & intent dispatcher
│       ├── guardian.py            # Deterministic safety classifier & audit logger
│       ├── memory.py              # Approved local facts store & recall engine
│       ├── cognition.py           # Transparent local cognition state
│       ├── daily_context.py       # Daily check-ins, energy/sleep tracking & briefs
│       ├── safe_tools.py          # Read-only approved folder & file toolbox
│       ├── secrets.py             # Session & encrypted secret manager
│       ├── api_tools.py           # External LLM clients (Groq, Gemini, NVIDIA, etc.)
│       └── sub_agents/            # Core safety, memory, reasoning & learning agents
├── config/
│   ├── lucy_runtime_config.json   # Runtime feature flags & mode locks
│   └── lucy_protected_actions.json# Hard-blocked & approval-gated action definitions
├── data/
│   ├── spine.json                 # Master Living Spine configuration
│   └── lucy/                      # Local JSON state stores (memory, daily, checkpoints)
├── docs/                          # Architecture guides, roadmaps & manual test plans
├── frontend/
│   └── index.html                 # Single-page Cyber/Mono Cognitive Web Dashboard
├── tests/                         # 70+ unittest suites (923 tests covering Stages 1–34)
├── run.sh                         # Quick-start launcher for the Web Server
├── run_lucy.py                    # Interactive CLI chat REPL
├── run_lucy_core.py               # CLI command dispatcher & Part 1 runner
└── run_lucy_desktop.py            # Native Tkinter desktop interface
```

---

## Quick Start & Installation

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/seninalikp/lucy.git
cd lucy

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
LUCY runs 100% offline out of the box. To enable external LLM providers, copy `.env.example` to `.env` and add your keys:
```bash
cp .env.example .env
```
Supported environment variables in `.env`:
- `LUCY_PORT=7700`
- `LUCY_API_ORDER=groq,gemini,nvidia,openrouter,sambanova`
- `GROQ_API_KEY`, `GEMINI_API_KEY`, `NVIDIA_API_KEY`, `OPENROUTER_API_KEY`, `SAMBANOVA_API_KEY`

---

## Running LUCY

### Option A: Web Dashboard & REST API (Port 7700)
```bash
./run.sh
# Or directly:
python3 backend/server.py
```
Open **`http://localhost:7700`** in your browser to inspect the Spine configuration, view agent stages, review safety rules, and chat with LUCY.

### Option B: Interactive CLI REPL
```bash
python3 run_lucy.py
```
Example commands inside the REPL:
- `status` — View full runtime, memory, and safety status
- `remember <fact>` — Store an approved fact in local memory
- `recall <keyword>` — Search local memory
- `daily brief` — View latest energy, sleep, and routine check-in
- `help` — List all available runtime commands
- `exit` — Trigger graceful shutdown

### Option C: Single-Command CLI Execution
```bash
python3 run_lucy_core.py status
```

### Option D: Native Desktop Window (Tkinter)
```bash
python3 run_lucy_desktop.py
```

---

## Running the Test Suite

LUCY includes a comprehensive standard-library `unittest` suite covering all 34 developmental stages:

```bash
python3 -m unittest discover -s tests -v
```

---

## License

This project is licensed under the [MIT License](LICENSE).