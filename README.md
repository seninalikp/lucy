# LUCY — Living Unified Cognitive Yield

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Operational](https://img.shields.io/badge/Status-Recovered%20V0.1%20Checkpoint%20023-cyan.svg)]()
[![Tests: 922 Passing](https://img.shields.io/badge/Tests-922%20Passing-success.svg)]()

> **A safe, local-first cognitive assistant and modular multi-stage autonomous agent runtime.**

---

## Overview

**LUCY** (**L**iving **U**nified **C**ognitive **Y**ield) is a local cognitive operating assistant engineered with safety, transparency, and explicit permission boundaries at its core.

Rather than relying on unconstrained autonomous loops, Lucy operates on a deterministic foundation:
* **The Living Spine** (`data/spine.json`): The single source of truth defining permissions, boundaries, memory rules, and agent definitions.
* **The Guardian Safety Enforcer** (`backend/lucy_core/guardian.py`): A hard filter that intercepts all user requests and tool executions, ensuring actions fall strictly within approved permission levels (Levels 0–4: Read-Only to Root).
* **Transparent Cognition**: Tracks internal vision, working thoughts, daily context, and session continuity in local JSON/JSONL state—without ungrounded anthropomorphism.
* **Isolated Provider Layer**: Connects to LLM providers (NVIDIA NIM, Groq, OpenRouter, Google Gemini, SambaNova) as external conversational tools without allowing external models to hijack system identity or permissions.

---

## Core Architecture & Features

```
┌─────────────────────────────────────────────────────────────┐
│                       USER INTERFACES                       │
│     Web UI (Port 7700)   │   CLI Chat   │   Desktop UI      │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                    COMMAND ROUTER & BUS                     │
│               Command Normalization & Routing               │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                  GUARDIAN SAFETY ENFORCER                   │
│   Permission Levels 0-4  │  Protected Files  │  Audit Log   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                     LUCY CORE RUNTIME                       │
│  • Memory & Deep Recall       • Daily Context & Briefs      │
│  • Self-Model & Reflection    • Projects & Task Tracker     │
│  • Safe Local File Tools      • Health & Continuity Pulse   │
│  • Shadow Testing & Lab       • Safe Provider Vault Tools   │
└─────────────────────────────────────────────────────────────┘
```

* **Permission Hierarchy (Levels 0–4)**:
  * **Level 0 (Read-Only)**: Status, logs, checkpoints.
  * **Level 1 (Log & Report)**: Notes, daily briefs, summaries.
  * **Level 2 (Safe Commands)**: Sandboxed project actions, local memory.
  * **Level 3 (Approved Edits)**: Project configuration modifications (requires confirmation).
  * **Level 4 (Root / Privileged)**: System-level operations (strictly blocked by default).
* **14 Registered Specialist Agents**: Defined in the spine (ELIE, RAY, ARES, VANTA, HAVEN, NEXUS, ECHO, LEDGER, SABLE, ORBIT, NOVA, MINT, ATLAS, JESTER), kept safely inactive until individual verification.
* **34 Developmental Stages**: Full feature progression including memory filters, recovery, adaptive communication, human-state awareness, autonomy boundaries, and provider health verification.

---

## Tech Stack

* **Backend Runtime**: Python 3.10+
* **Web Server**: Flask, Werkzeug
* **Frontend**: Vanilla HTML5, CSS3 (IBM Plex Mono + Syne typography), Modern ES6+ JavaScript
* **Desktop Client**: Python Tkinter
* **Data Storage**: Human-readable JSON configurations and append-only JSONL event/reflection logs
* **Testing**: Python standard `unittest` (920+ unit tests)

---

## Directory Structure

```
lucy/
├── backend/
│   ├── server.py              # Flask API & static frontend server (port 7700)
│   └── lucy_core/             # Core cognitive runtime & stage modules
│       ├── guardian.py        # Safety classification and boundary enforcement
│       ├── router.py          # Command normalizer and intent router
│       ├── lucy_runtime.py    # Main lifecycle, state, and coordination engine
│       ├── safe_tools.py      # Read-only workspace inspection tools
│       ├── memory.py          # Local approved memory store & recall
│       ├── api_tools.py       # External LLM provider client integrations
│       ├── secrets.py         # Key management and secret isolation
│       └── ...                # Cognitive stage modules (Stages 1–34)
├── config/
│   ├── lucy_protected_actions.json
│   └── lucy_runtime_config.json
├── data/
│   ├── spine.json             # Living spine: identity, rules, agent registry
│   └── lucy/                  # Local runtime data, state, memory, and checkpoints
│       ├── memory/            # Approved facts and memory rules
│       ├── daily/             # Daily contexts and routine logs
│       └── secure/            # Isolated key vault directory
├── docs/                      # Architectural contracts and integration roadmaps
├── frontend/
│   └── index.html             # Single-page cyberpunk dashboard & web chat UI
├── logs/                      # Audit trails, build logs, and test documentation
├── tests/                     # Comprehensive test suite (920+ test cases)
├── .env.example               # Template environment configuration
├── .gitignore                 # Tech-stack specific ignore rules
├── requirements.txt           # Python package dependencies
├── run.sh                     # Shell script launcher for Web UI
├── run_lucy.py                # Interactive CLI REPL chat launcher
├── run_lucy_core.py           # CLI command dispatcher
└── run_lucy_desktop.py        # Native desktop GUI client
```

---

## Local Setup & Installation

### 1. Prerequisites
* Python 3.10 or higher
* Git

### 2. Clone Repository
```bash
git clone git@github.com:seninalikp/lucy.git
cd lucy
```

### 3. Create a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment
```bash
cp .env.example .env
# Edit .env with your optional provider API keys (NVIDIA, Groq, OpenRouter, Gemini, etc.)
```

---

## Usage Guide

### 1. Web Dashboard & Chat (Recommended)
Start the local server:
```bash
bash run.sh
# or directly:
python3 backend/server.py
```
Open **[http://localhost:7700](http://localhost:7700)** in your browser to view the living spine, inspect agent statuses, review permission boundaries, and interact via web chat.

### 2. Interactive CLI Chat
To chat directly with Lucy in the terminal:
```bash
python3 run_lucy.py
```
Type `help` for available commands, or `exit` / `quit` to leave.

### 3. Native Desktop UI
Launch the desktop client window:
```bash
python3 run_lucy_desktop.py
```

### 4. CLI Command Dispatcher
Execute individual commands directly:
```bash
# Check runtime status & health
python3 run_lucy_core.py status
python3 run_lucy_core.py health

# Memory operations
python3 run_lucy_core.py remember "Always operate local-first"
python3 run_lucy_core.py recall "local-first"

# Projects & tasks
python3 run_lucy_core.py list projects
python3 run_lucy_core.py add task "Review stage 34 health checks"
python3 run_lucy_core.py show tasks

# Daily brief & continuity
python3 run_lucy_core.py daily brief
python3 run_lucy_core.py continuity status
```

---

## Verification & Testing

Lucy includes a comprehensive unit test suite covering Guardian safety rules, tool execution boundaries, memory stores, and stage-by-stage pipelines:

```bash
# Run the entire test suite
python3 -m unittest discover -s tests

# Run system health diagnostics (53 checks)
python3 run_lucy_core.py health
```

---

## License

This project is open-source under the [MIT License](LICENSE).