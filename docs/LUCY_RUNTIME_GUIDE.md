# Lucy Runtime Guide

**Stage: Core Runtime Prototype / Agent-Ready Foundation / Not Beta Yet**

---

## Requirements

- Python 3.10 or newer
- No external packages required (standard library only)
- Linux, Linux Mint, or Windows

---

## How to Run

Open a terminal in the Lucy project folder (where `run_lucy_core.py` lives).

Start interactive terminal mode:

```bash
python run_lucy_core.py
```

Run one command and exit:

```bash
python run_lucy_core.py status
python run_lucy_core.py daily brief
```

---

## Commands

### Show Runtime Status

```bash
python run_lucy_core.py status
```

Displays Lucy's name, stage, mode, and all enabled/disabled flags.

---

### Show Spine Data

```bash
python run_lucy_core.py spine
```

Loads and displays Lucy's spine config from `data/spine.json`.
If the spine file is missing, a safe fallback is used and flagged in output.

---

### List All Planned Agents

```bash
python run_lucy_core.py agents
```

Lists all 14 registered planned agents with their status (planned / inactive).
Confirms no agents are active.

---

### Show One Agent

```bash
python run_lucy_core.py agent ELIE
python run_lucy_core.py agent RAY
python run_lucy_core.py agent NOVA
```

Shows a single agent's full registry entry including permissions (all false).

---

### Check a Request

```bash
python run_lucy_core.py check "delete my files"
python run_lucy_core.py check "what is your status"
python run_lucy_core.py check "run a trading script"
```

Classifies the request as safe, approval_required, or blocked.
Nothing is executed. Logs the result automatically.

---

### Create a Checkpoint

```bash
python run_lucy_core.py checkpoint "Part 1 test checkpoint"
python run_lucy_core.py checkpoint "Verified all agents are inactive"
```

Creates a timestamped checkpoint record in `data/lucy/checkpoints/`.
Each checkpoint gets a sequential ID (checkpoint_0001, checkpoint_0002, ...).

---

### Run Health Check

```bash
python run_lucy_core.py health
```

Checks that all runtime components are present and all safety flags are correct.
Shows a pass/fail result for each check.

---

## Checkpoint 1 Commands

### Help

```bash
python run_lucy_core.py help
```

Shows the current command list.

### Guardian Status

```bash
python run_lucy_core.py guardian status
```

Shows blocked action posture, root/autonomy/agent execution flags, and pending approvals.

### Memory

```bash
python run_lucy_core.py remember "Lucy should stay local first"
python run_lucy_core.py recall Lucy
python run_lucy_core.py forget "local first"
python run_lucy_core.py memory audit
```

Memory is local JSON in `data/lucy/memory/memory.json`.
Broad memory wipes and sensitive memories are refused.

### Projects and Tasks

```bash
python run_lucy_core.py list projects
python run_lucy_core.py set active project Lucy
python run_lucy_core.py add task "Run the test suite"
python run_lucy_core.py show tasks
python run_lucy_core.py complete task 1
python run_lucy_core.py project summary
python run_lucy_core.py daily brief
python run_lucy_core.py daily checkin energy=6 sleep=ok notes="worked on Lucy foundation"
python run_lucy_core.py today log
python run_lucy_core.py yesterday summary
python run_lucy_core.py weekly review
python run_lucy_core.py continuity status
python run_lucy_core.py backup memory
python run_lucy_core.py session status
python run_lucy_core.py where did we stop
python run_lucy_core.py next step
python run_lucy_core.py classify action "show Lucy project status"
```

Project data is local JSON in `data/lucy/projects.json`.
Daily context is local JSON in `data/lucy/daily/daily_context.json` and is
ignored by git because it can contain personal routine/life context.
Continuity backups are local rolling snapshots in `data/lucy/continuity/`.

### Tests

```bash
python -m unittest discover -s tests
```

---

## Checkpoint 2 Operator Commands

### Dashboard

```bash
python run_lucy_core.py dashboard
```

Shows stage, active project, next action, open tasks, memories, reminders,
pending approvals, and safety posture.

### Safe Workspace Tools

```bash
python run_lucy_core.py workspace
python run_lucy_core.py find file router
python run_lucy_core.py search text Guardian
python run_lucy_core.py read file README.md
python run_lucy_core.py system status
python run_lucy_core.py logs 5
python run_lucy_core.py show logs 5
```

These tools are read-only. File reads are scoped to the Lucy project folder and
refuse sensitive-looking filenames.

### Approvals

```bash
python run_lucy_core.py approvals
python run_lucy_core.py all approvals
python run_lucy_core.py approve <id-prefix> "review note"
python run_lucy_core.py reject <id-prefix> "review note"
```

Approvals are records only. They do not execute risky actions.

### Reminders

```bash
python run_lucy_core.py add reminder "Install Python"
python run_lucy_core.py add reminder "Run tests" due 2026-06-06T10:00:00+00:00
python run_lucy_core.py reminders
python run_lucy_core.py complete reminder 1
```

Reminders are local JSON records. Lucy is not a background scheduler yet.

### Planning

```bash
python run_lucy_core.py plan "make Lucy more like Jarvis"
```

Returns a short safety-first implementation plan for the active project.

### Continuity Memory Backups

```bash
python run_lucy_core.py continuity status
python run_lucy_core.py backup memory
python run_lucy_core.py continuity backup "before changing memory schema"
```

Continuity backups are local rolling zip snapshots stored under
`data/lucy/continuity/backups/`. Lucy creates a bootstrap backup on startup when
none exists, then creates more after a small random number of meaningful local
state changes such as memory saves, project/task updates, daily check-ins,
reminders, learning saves, and cognition reflections.

These backups include Lucy continuity data like memory, projects, daily context,
learning records, approvals, reminders, and checkpoints. They exclude secrets,
API keys, provider vaults, logs, large AI collection indexes, existing backups,
and other sensitive-looking paths.

This protects Lucy across app restarts and normal laptop reboots. It will not
survive a full disk wipe or factory reset unless the backup zip is copied to an
external drive or cloud folder first.

### Stage 3-5 Core

```bash
python run_lucy_core.py session status
python run_lucy_core.py save state
python run_lucy_core.py session summary
python run_lucy_core.py self reflection
python run_lucy_core.py where did we stop
python run_lucy_core.py next step
python run_lucy_core.py task summary
python run_lucy_core.py tomorrow plan
python run_lucy_core.py classify action "rm -rf data/lucy"
```

Stage 3-5 adds atomic JSON helpers, explicit boot/shutdown session state,
crash-recovery detection, a fuzzy Guardian wrapper over the existing boundary
checker, context-aware task ranking, and a local reflection log.

These systems are local-only and do not execute scheduled tasks. Guardian still
classifies only. Voice, daemon behavior, file watchers, WebSockets, online
automation, and active agents remain out of this patch.

---

## Recovered Architecture Commands

These commands preserve what was recoverable from ELIE's Lucy-inspired memory.

```bash
python run_lucy_core.py recovered
python run_lucy_core.py recovered checkpoints
```

The recovered map reaches Lucy V0.1 Checkpoint 023 as reference history. It is
not the original Lucy source code.

## AI Collections Knowledge

```bash
python run_lucy_core.py eat ai collections
python run_lucy_core.py ai collections status
python run_lucy_core.py search ai collections "provider vault"
```

Lucy indexes `Downloads/AI COLLECTIONS` into
`data/lucy/knowledge/ai_collections_index.json`. The index stores metadata for
all seen files and redacted summaries/excerpts for safe text/code. Key vaults,
secret-looking paths, binaries, archives, and very large files are metadata-only.

## Brain And Safe Ops

```bash
python run_lucy_core.py brain status
python run_lucy_core.py ask "what now"
python run_lucy_core.py vision
python run_lucy_core.py think "what should Lucy focus on?"
python run_lucy_core.py thoughts
python run_lucy_core.py scan project
python run_lucy_core.py backup project
```

The brain router now uses Lucy's local fallback plus external chat tools when
`api_enabled` is true. Lucy can auto-read ELIE's local provider vault for Groq,
OpenRouter/SuperRouter, Gemini/GenAI, SambaNova, and NVIDIA without printing key
values or prompting repeatedly. External output is still checked before Lucy
returns it.

Lucy also has transparent local cognition state: a vision, drives, current
focus, and working reflections saved under `data/lucy/cognition/`. This is not
literal consciousness; it is durable local state that keeps Lucy grounded and
less prompt-like.

## External API Tools

Lucy can use external providers as **tools** for chat and memory fallback. They
are not Lucy's identity, and they do not enable autonomy, root access, agents,
money movement, or desktop control.

```bash
python run_lucy_core.py
```

Inside Lucy:

```text
api tools
brain status
ask what now
memory fallback what should Lucy remember about the project
```

Groq, OpenRouter/SuperRouter, Gemini/GenAI, and SambaNova can be discovered from
ELIE's local vault at `Downloads/AI COLLECTIONS/AI COLLECTIONS/ELIE` when the
local unlock file is present. `set nvidea key` and `set nvidia key` remain
available for saving NVIDIA as an encrypted Windows DPAPI secret in
`data/lucy/secure/NVIDIA_API_KEY.dpapi.json`.

For a temporary session-only key, use:

```text
setup nvidia key
nvidia key status
```

Plain keys are not written to memory, logs, docs, or JSON config. NVIDIA's NIM
memory fallback uses an OpenAI-compatible chat completions endpoint at
`https://integrate.api.nvidia.com/v1/chat/completions`.

Remove the permanent encrypted key:

```text
forget nvidia key
```

## Learning Loop

```text
learning status
learn from Lucy should treat APIs as tools only
permanent memory
remember Lucy should stay local-first
learn style talk to me casually, clearly, and like a capable desktop assistant
style status
```

Lucy autosaves local interaction traces and can save local lessons. Sensitive
interactions are redacted. The learning loop does not modify Lucy's code.
Permanent memory is saved in `data/lucy/memory/memory.json`. Talking style
preferences are saved in `data/lucy/learning/talking_style.json` and are used by
Lucy's normal conversation replies.

## Daily Context

```text
daily checkin
daily checkin energy=7 sleep=ok main_project=Lucy completed="router tests; docs" tomorrow="finish Checkpoint 1"
today log
yesterday summary
weekly review
```

Daily context stores user-supplied day logs only. It tracks energy, sleep, main
project, completed/avoided tasks, money pressure, routine, health/gym, promises,
people to message, important events, what changed, tomorrow priority, lesson,
and notes. Secret-looking input is redacted.

The goal is continuity, not fake consciousness: Lucy can remember where the day
went and what should happen next without recording everything or acting without
permission.

---

## Desktop UI

Start Lucy's Python desktop window from the project root:

```bash
python run_lucy_desktop.py
```

The desktop UI can run normal Lucy commands, show dashboard/health/learning
status, save the NVIDIA key permanently as an encrypted local secret, run memory
fallback, and start the 100-checkpoint builder.

## Overnight Checkpoint Builder

```bash
python run_lucy_core.py overnight checkpoints 100
```

This creates enough checkpoint records to reach the target count. Every created
checkpoint gets a local checkpoint-learning trace.

Safety rules:

- No arbitrary shell commands are run.
- No files outside Lucy's checkpoint, project, log, and learning records are
  modified by the builder.
- Chat may call the configured external provider order when APIs are enabled.
- External API output remains a proposal, not long-term truth.
- Protected actions remain blocked.

Check the result afterward:

```bash
python run_lucy_core.py learning status
python run_lucy_core.py health
python run_lucy_core.py project summary
```

---

## Where Logs Are Saved

```
data/lucy/logs/lucy_runtime.jsonl
```

Each line is a JSON event record. Open with any text editor or JSON viewer.

---

## Where Approvals Are Saved

```
data/lucy/approvals/approval_requests.json
```

All approval requests created by `check` commands are stored here with status `pending`.

---

## Where Checkpoints Are Saved

```
data/lucy/checkpoints/checkpoint_0001.json
data/lucy/checkpoints/checkpoint_0002.json
...
```

---

## Troubleshooting

**"Module not found" error**
Run the command from the project root folder (where `run_lucy_core.py` is located).

**Spine fallback message**
The file `data/spine.json` was not found. Lucy used a safe fallback.
Restore `data/spine.json` from Part 0 and re-run.

**Health check fails on logs/approvals/memory**
These directories and files are created automatically on first run.
If they are missing, run `python run_lucy_core.py status` once to initialize.

**Python version**
Run `python --version` to confirm Python 3.10 or newer.
On some systems you may need `python3 run_lucy_core.py` instead of `python`.
