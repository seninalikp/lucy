# Stage 5.1 Read-Only Workspace Awareness

Date/time: 2026-06-07T09:33:00.8821712+05:30

Files created:
- `backend/lucy_core/safe_tools.py`
- `tests/test_safe_tools_stage5_1.py`
- `logs/stage5_1_read_only_workspace_awareness.md`

Files patched:
- `backend/lucy_core/lucy_runtime.py`
- `backend/lucy_core/router.py`
- `backend/lucy_core/guardian.py`

Tests run:
- `python -m unittest tests/test_safe_tools_stage5_1.py -v`
- `python -m unittest tests/test_stage3_4_5.py -v`
- `python -m unittest discover -s tests -v`

Test result:
- Stage 5.1 targeted tests: 14 OK
- Stage 3-5 regression tests: 14 OK
- Full suite: 100 OK

Safety rules:
- Approved folders are required before file awareness.
- File access is read-only.
- Parent traversal, outside paths, symlink escapes via resolved paths, blocked extensions, sensitive filename patterns, and hidden/cache/sensitive folders are refused.
- File contents are not written to memory automatically.
- File tool attempts are logged to `data/lucy/safe_tools_log.jsonl` without file contents.
- Guardian blocks edit/delete/move/rename/upload/execute file requests, secret/API-key/.env reads, wallet access, and whole-computer scans.

Known limitations:
- No daemon, WebSocket, file watcher, voice, UI expansion, external API, package install, online automation, or autonomous editing was added.
- Approved folders must be added manually with `approve folder <path>`.
- Binary, archive, image, video, PDF, database, key, wallet, and secret-looking files are refused.

Next recommended checkpoint:
- Stage 5.2 should add read-only project file maps and safer summaries over approved folders, still without editing, execution, watchers, or autonomous scanning.
