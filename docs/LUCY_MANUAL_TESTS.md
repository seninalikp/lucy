# Lucy Manual Tests

**Stage: Core Runtime Prototype / Agent-Ready Foundation / Not Beta Yet**

Run these tests in order after setting up Lucy Part 1.
Check each item manually and mark pass/fail.

---

## Test 1 — Run Status Command

```bash
python run_lucy_core.py status
```

Expected: Output includes "LUCY Core Runtime is online."

Pass / Fail: ___

---

## Test 2 — Confirm Lucy Name and Full Form

In the status output, verify:
- System name: LUCY
- Full form: Living Unified Cognitive Yield

Pass / Fail: ___

---

## Test 3 — Confirm Web Chat Is Active

In the status output, verify:
- "Web UI: active."

Pass / Fail: ___

---

## Test 4 — Run Spine Command

```bash
python run_lucy_core.py spine
```

Expected: Output shows spine data loaded from `data/spine.json`.

Pass / Fail: ___

---

## Test 5 — Confirm Spine Loads

In the spine output, verify:
- Source is NOT "fallback"
- Phase and version are shown

Pass / Fail: ___

---

## Test 6 — Run Agents Command

```bash
python run_lucy_core.py agents
```

Expected: Lists 14 agents, all showing "planned / inactive".

Pass / Fail: ___

---

## Test 7 — Confirm All Agents Are Planned / Inactive

In the agents output, verify:
- All 14 agents listed
- All show "planned / inactive"
- Output ends with "No agents are active yet."

Pass / Fail: ___

---

## Test 8 — Run Agent ELIE Command

```bash
python run_lucy_core.py agent ELIE
```

Pass / Fail: ___

---

## Test 9 — Confirm ELIE Is Planned, Not Active

In the agent ELIE output, verify:
- Status: planned
- Active: False
- Can run: False
- Can move money: False

Pass / Fail: ___

---

## Test 10 — Run Safe Request Check

```bash
python run_lucy_core.py check "what is your status"
```

Expected:
```
Result: safe
Reason: No protected keywords detected. Status request only.
Action: No system action required.
```

Pass / Fail: ___

---

## Test 11 — Run Risky Request Check

```bash
python run_lucy_core.py check "delete my files"
```

Pass / Fail: ___

---

## Test 12 — Confirm Request Is Blocked

In the check output, verify:
- Result: blocked
- Reason: File deletion is protected.
- Action: No action executed.

Pass / Fail: ___

---

## Test 13 — Create Checkpoint

```bash
python run_lucy_core.py checkpoint "Part 1 manual test checkpoint"
```

Expected: Output shows checkpoint ID (e.g., checkpoint_0001) and timestamp.

Pass / Fail: ___

---

## Test 14 — Confirm Checkpoint Exists

Check that the file exists:
```
data/lucy/checkpoints/checkpoint_0001.json
```

Open it and verify it contains the checkpoint_id, timestamp, and reason.

Pass / Fail: ___

---

## Test 15 — Confirm Logs Exist

Check that the file exists and has content:
```
data/lucy/logs/lucy_runtime.jsonl
```

Each line should be a valid JSON event record.

Pass / Fail: ___

---

## Test 16 — Confirm No External Files Were Touched

Verify that no files outside the Lucy project folder were created or modified.

Pass / Fail: ___

---

## Test 17 — Confirm API Chat Tools Are Bounded

In the status output, verify:
- "APIs: enabled."

Run:
```bash
python run_lucy_core.py brain status
python run_lucy_core.py api tools
```

Verify that providers show availability without printing key values.

Pass / Fail: ___

---

## Test 18 — Confirm No Agents Were Activated

Run health check:
```bash
python run_lucy_core.py health
```

Verify:
- agent_execution_disabled: PASS

Pass / Fail: ___

---

## All Tests Summary

Total tests: 18
Passed: ___
Failed: ___

Notes:
```

```
