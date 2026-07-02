# LUCY — Part 0: Spine Config

**10-part build series · Part 0 of 10**

---

## What This Is

The living spine config — Lucy's rules, boundaries, agent map, permission model, and memory filter served as a real API with a web UI to read it live.

This is not a chatbot. Not an AI yet. This is the **foundation layer** — the single source of truth that everything else in Lucy will be built on top of.

---

## What's Inside

```
lucy_part0/
├── data/
│   └── spine.json          ← The spine config. Edit this directly.
├── backend/
│   └── server.py           ← Flask API serving spine.json
├── frontend/
│   └── index.html          ← Web UI reading from the API
├── requirements.txt
├── run.sh
└── README.md
```

---

## How to Run

```bash
# Install dependencies (first time only)
pip3 install -r requirements.txt

# Start the server
bash run.sh
# or directly:
python3 backend/server.py

# Then open:
http://localhost:7700
```

---

## API Endpoints

| Method | Endpoint | Returns |
|--------|----------|---------|
| GET | `/api/spine` | Full spine.json |
| GET | `/api/lucy` | Lucy core identity & status |
| GET | `/api/agents` | All 14 agents |
| GET | `/api/agents/{ID}` | Single agent |
| PATCH | `/api/agents/{ID}/stage` | Update agent stage (requires confirmation) |
| GET | `/api/safety` | Safety rules |
| GET | `/api/permissions` | Permission level model |
| GET | `/api/build-order` | Build order sorted list |
| GET | `/api/memory-filter` | Three-layer memory filter |
| GET | `/api/playground` | Playground config |
| GET | `/api/status` | Quick system overview |
| POST | `/api/chat` | Send a message to Lucy's local chat/router |

---

## How to Update Stage

When an agent genuinely reaches a new stage, PATCH the endpoint:

```bash
curl -X PATCH http://localhost:7700/api/agents/ELIE/stage \
  -H "Content-Type: application/json" \
  -d '{"stage": "prototype", "confirmed": true, "reason": "First prototype working, logging actions"}'
```

The server creates a backup of spine.json before any write.

---

## What Comes Next

| Part | What Gets Built |
|------|----------------|
| 0 | ✓ Spine config — this |
| 1 | Memory system — checkpoints, logs, approved lessons as real data |
| 2 | ELIE prototype — the active assistant layer |
| 3 | Playground review system — reports, approvals, routing |
| 4 | NEXUS routing layer |
| 5 | SABLE safety enforcer |
| 6 | ORBIT system monitor |
| 7 | HAVEN health logs + pattern detection |
| 8 | LEDGER money tracker |
| 9 | Lucy integration — lesson absorption + checkpoint engine |

---

## Design Decisions

**Why JSON, not a database?**
At Foundation Phase, the config needs to be human-readable, directly editable, and version-controllable. A database would add complexity before there's anything complex to store. When Part 1 (memory system) is built, proper storage gets introduced there.

**Why Flask and not something heavier?**
Same reason. Lightweight, readable, easy to extend. No ORM, no migrations, no boilerplate. Just a server that reads a file and returns it.

**Why a web UI and not just terminal?**
You said terminal gives you headaches. The UI is the interface. The terminal is just how you start it.


---

## Part 1 — LUCY Core Runtime Prototype

Part 1 adds the **LUCY Core Runtime Prototype / Agent-Ready Foundation**.

Lucy can now:
- Load her living spine config from Part 0
- Register 14 planned inactive agents
- Check whether requests are safe, blocked, or approval-required
- Create approval request records
- Create checkpoint records
- Write JSONL runtime logs
- Report runtime health

**Web chat is active. No agents are active. Lucy is not Beta yet.**

### Quick Start (Part 1)

```bash
python run_lucy_core.py status
python run_lucy_core.py spine
python run_lucy_core.py agents
python run_lucy_core.py agent ELIE
python run_lucy_core.py check "delete my files"
python run_lucy_core.py check "what is your status"
python run_lucy_core.py checkpoint "My first checkpoint"
python run_lucy_core.py health
```

See `docs/LUCY_RUNTIME_GUIDE.md` for full documentation.

---

## Checkpoint 1 - Local Operating Assistant Foundation

The restored Part 1 runtime has been extended into a beginner-friendly local
assistant foundation.

Lucy can now:
- Start an interactive terminal chat with `python run_lucy_core.py`
- Chat in the browser at `http://localhost:7700`
- Route commands through a dedicated command router
- Save approved local memories with `remember <fact>`
- Recall memories with `recall [keyword]`
- Soft-delete specific memories with `forget <specific memory>`
- Audit memory with `memory audit`
- Track projects and active tasks
- Produce a simple `daily brief`
- Keep Guardian safety checks in front of risky actions

Useful commands:

```bash
python run_lucy_core.py
python run_lucy_core.py help
python run_lucy_core.py guardian status
python run_lucy_core.py remember "Lucy should stay local first"
python run_lucy_core.py recall Lucy
python run_lucy_core.py list projects
python run_lucy_core.py add task "Run the test suite"
python run_lucy_core.py show tasks
python run_lucy_core.py daily brief
python run_lucy_core.py daily checkin energy=6 sleep=ok notes="worked on Lucy foundation"
python run_lucy_core.py today log
python run_lucy_core.py weekly review
python run_lucy_core.py continuity status
python run_lucy_core.py backup memory
python run_lucy_core.py vision
python run_lucy_core.py think "what should Lucy focus on?"
python run_lucy_core.py thoughts
python -m unittest discover -s tests
```

Lucy still does not have desktop automation, voice, autonomous actions, or active agents.
Those layers should wait until the local foundation is stable.

---

## Checkpoint 2 - Local Operator Tools

Lucy now has safe local operator tools that make her closer to a JARVIS-style
assistant while keeping dangerous actions gated.

New commands:

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
python run_lucy_core.py add reminder "Install Python"
python run_lucy_core.py reminders
python run_lucy_core.py plan "make Lucy more like Jarvis"
python run_lucy_core.py eat ai collections
python run_lucy_core.py ai collections status
python run_lucy_core.py search ai collections "provider vault"
```

Safety line:
- Lucy can inspect and summarize local project files.
- Lucy can build a redacted local knowledge index from `Downloads/AI COLLECTIONS`.
- Lucy can keep transparent local cognition state: vision, drives, working thoughts, and current focus.
- Lucy can keep user-supplied daily context logs for routine/project continuity.
- Lucy can create rolling local continuity backups for memory, projects, daily context, learning, and checkpoints.
- Lucy refuses outside-project file reads and sensitive-looking filenames.
- Lucy still does not run arbitrary shell commands.
- Approval review records your decision; it does not execute risky actions.

AI Collections ingestion stores metadata for every seen file and redacted
summaries/excerpts for safe text/code. Key vaults, binary files, and
secret-looking paths are metadata-only.

Local cognition is not consciousness. It is a persistent state file that helps
Lucy remember her vision, reflect on project context, and avoid drifting.

---

## Recovered Lucy V0.1 Checkpoint 023 Architecture

ELIE's memory files say ELIE was a tiny skeleton built from **Lucy V0.1
Checkpoint 023 architecture style**. Lucy's original code is still lost, but
the checkpoint map was recovered as reference history.

New reconstruction commands:

```bash
python run_lucy_core.py recovered
python run_lucy_core.py recovered checkpoints
python run_lucy_core.py brain status
python run_lucy_core.py ask "what now"
python run_lucy_core.py scan project
python run_lucy_core.py backup project
```

Important boundary: ELIE is not Lucy. ELIE is used only as a smaller reference
for safe architecture patterns.

---

## External API Tools, Permanent Memory, And Talking Style

Lucy can use ELIE's local provider vault as an external chat tool source. Groq,
OpenRouter/SuperRouter, Gemini/GenAI, SambaNova, and NVIDIA are discovered
without printing key values or repeatedly asking for them.

```bash
python run_lucy_core.py
```

Then inside Lucy:

```text
api tools
brain status
ask what can you help me with now?
learning status
permanent memory
learn style talk to me casually, clearly, and like a capable desktop assistant
style status
memory fallback what should Lucy remember about the project
```

Rules:
- External providers are tools for Lucy's safe language layer, not Lucy's identity.
- Lucy can auto-read ELIE's local vault when `local_unlock.py` is present.
- Lucy does not write plain provider keys to memory, logs, docs, or runtime config.
- `setup nvidia key` remains available for session-only NVIDIA setup.
- `set nvidia key` / `set nvidea key` saves an encrypted permanent NVIDIA key file.
- Permanent memory lives in `data/lucy/memory/memory.json`.
- Talking style preferences live in `data/lucy/learning/talking_style.json`.
- External NVIDIA memory fallback suggestions are saved as proposals, not truth.

---

## Desktop UI And Overnight Checkpoints

Lucy now has a Python desktop UI and a safe overnight checkpoint builder.

Start the desktop window:

```bash
python run_lucy_desktop.py
```

Or run from the terminal:

```bash
python run_lucy_core.py overnight checkpoints 100
python run_lucy_core.py learning status
python run_lucy_core.py health
```

What the overnight checkpoint builder does:

- Creates enough checkpoint records to reach the requested target, up to 500.
- Saves a local checkpoint-learning trace for every created checkpoint.
- Runs health before and after the checkpoint batch.
- Keeps protected actions blocked.
- Does not run autonomous API work or treat an API as Lucy's identity.
#   l u c y  
 