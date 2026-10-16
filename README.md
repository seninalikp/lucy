# LUCY — Living Unified Cognitive Yield

> **Offline-first, deterministic, safety-gated cognitive operating assistant and modular multi-agent runtime foundation.**

![Python](https://img.shields.io/badge/Python-3.10%2B-00c8ff?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-00e5a0?style=flat-square&logo=flask&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-922%20Passing-00e5a0?style=flat-square)
![Mode](https://img.shields.io/badge/Runtime-Safe%20Local%20First-f5c842?style=flat-square)
![License](https://img.shields.io/badge/Status-Core%20Prototype%20v0.1.0-purple?style=flat-square)

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
├── tests/                         # 70+ unittest suites (922 tests covering Stages 1–34)
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

## REST API Endpoints (`backend/server.py`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status` | High-level runtime status, version, and agent stage counts |
| `GET` | `/api/spine` | Full `data/spine.json` configuration |
| `GET` | `/api/lucy` | Core LUCY metadata and capability locks |
| `GET` | `/api/agents` | List all 14 planned agents and their metadata |
| `GET` | `/api/agents/<id>` | Detailed configuration for a specific agent |
| `PATCH` | `/api/agents/<id>/stage` | Update an agent's stage (requires `{"confirmed": true}`) |
| `GET` | `/api/safety` | Active safety rules (`absolute_never`, `always_safe`, `protected_files`) |
| `GET` | `/api/permissions` | Permission Levels 0–4 specification |
| `POST` | `/api/chat` | Send a command or chat message (`{"message": "..."}`) to `CommandRouter` |