# Lucy Test Log

## 2026-06-05 - Checkpoint 1 Local Foundation

Planned verification:

- `python run_lucy_core.py status`
- `python run_lucy_core.py health`
- `python run_lucy_core.py guardian status`
- `python run_lucy_core.py remember "Lucy should stay local first"`
- `python run_lucy_core.py recall Lucy`
- `python run_lucy_core.py list projects`
- `python run_lucy_core.py daily brief`
- `python -m unittest discover -s tests`

Result: blocked by missing Python runtime.

Observed locally:

- `python --version` opens the Microsoft Store alias instead of a real interpreter.
- `python3 --version` opens the Microsoft Store alias instead of a real interpreter.
- `py --version` did not return an installed launcher.
- No Python install was found in common local `Programs/Python` paths.
- `uv`, `conda`, `mamba`, and `pip` were not available.

Static checks completed:

- Confirmed restored file tree with `rg --files`.
- Confirmed no git repository is present in this project folder.
- Confirmed the new source/test files are present.

Next verification step:

Install Python 3.10+ and run:

```bash
python run_lucy_core.py status
python run_lucy_core.py health
python -m unittest discover -s tests
```

## 2026-06-06 - NVIDIA Tool And Local Learning Loop

Additional tests added:

- `tests/test_secrets.py`
- `tests/test_learning.py`
- `tests/test_api_tools.py`
- Expanded `tests/test_router.py`

Result: still blocked by missing working Python runtime. Run after installing Python 3.10+:

```bash
python run_lucy_core.py learning status
python run_lucy_core.py api tools
python run_lucy_core.py nvidia key status
python -m unittest discover -s tests
```

## 2026-06-05 - Checkpoint 2 Local Operator Tools

Additional tests added:

- `tests/test_tools.py`
- `tests/test_reminders.py`
- `tests/test_approvals.py`
- Expanded `tests/test_router.py`

Result: still blocked by missing Python runtime. Run after installing Python 3.10+:

```bash
python run_lucy_core.py dashboard
python run_lucy_core.py workspace
python run_lucy_core.py health
python -m unittest discover -s tests
```

Static verification completed:

- JSON validation passed for runtime config, protected actions, memory, projects, reminders, checkpoint 0003, approvals, and agent registry.
- Static searches found no non-ASCII characters in the newly touched Python/test/log/data files.
- Static searches found no stale imports of `MemoryPlaceholder` in active backend/test code.
- A Python executable was found inside the ARES virtual environment, but it is broken because it points to a missing base Python install.

## 2026-06-05 - Recovered Lucy V0.1 Checkpoint 023 Architecture

Additional tests added:

- `tests/test_brain.py`
- `tests/test_recovery.py`
- `tests/test_ops.py`
- Expanded `tests/test_router.py`

Result: still blocked by missing Python runtime. Run after installing Python 3.10+:

```bash
python run_lucy_core.py recovered
python run_lucy_core.py recovered checkpoints
python run_lucy_core.py brain status
python run_lucy_core.py scan project
python run_lucy_core.py backup project
python -m unittest discover -s tests
```

## 2026-06-06 - Desktop UI And Overnight Checkpoint Builder

Additional tests added:

- `tests/test_checkpoint_builder.py`
- Expanded `tests/test_learning.py`
- Expanded `tests/test_router.py`

Verification run:

```bash
python -m unittest discover -s tests
```

Result:

```text
Ran 49 tests in 11.359s
OK
```

Runtime verification:

```bash
python run_lucy_core.py overnight checkpoints 100
python run_lucy_core.py overnight checkpoints 101
python run_lucy_core.py learning status
python run_lucy_core.py health
python -m py_compile run_lucy_desktop.py backend/lucy_core/desktop_ui.py backend/lucy_core/checkpoint_builder.py
python -c "import tkinter; print('tkinter ok')"
```

Observed:

- Checkpoint files: 101
- Project-linked checkpoints: 100
- Checkpoint learning traces: 96
- Health: 33 passed / 0 failed
- Tkinter import: ok

## 2026-06-06 - Permanent NVIDIA Key And Talking Style Memory

Additional tests added:

- Expanded `tests/test_secrets.py` for Windows DPAPI persistent secret save/restore.
- Expanded `tests/test_learning.py` for talking style preferences and style application.
- Expanded `tests/test_router.py` for style and permanent memory commands.

Verification run:

```bash
python -m unittest discover -s tests
```

Result:

```text
Ran 54 tests in 4.146s
OK
```

Runtime verification:

```bash
python run_lucy_core.py health
python run_lucy_core.py nvidia key status
python run_lucy_core.py style status
python run_lucy_core.py permanent memory
python run_lucy_core.py "who are you"
```

Observed:

- Health: 38 passed / 0 failed
- NVIDIA permanent file path is ready under `data/lucy/secure/`
- Talking style file exists with 1 default preference
- Permanent memory reports 4 active facts
- Conversation reply applied local talking style
