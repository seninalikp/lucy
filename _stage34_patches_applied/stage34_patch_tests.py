"""
stage34_patch_tests.py
Advance the active-stage reflection assertions in existing tests from Stage 33
to Stage 34 (the same sweep every prior stage transition performed).
Idempotent. Run from the project root:  python stage34_patch_tests.py
"""

from pathlib import Path

TESTS_DIR = Path("tests")

# Ordered: longer patterns before the shorter ones they contain.
REPLACEMENTS = [
    (
        "Active stage: 33 provider registry",
        "Active stage: 34 provider health-check dry-run",
    ),
    (
        "Current active stage: 33 provider registry",
        "Current active stage: 34 provider health-check dry-run",
    ),
    (
        "create/check provider registry metadata, keep providers disabled unless approved, dry-run only",
        "describe what a provider health check would do, dry-run only, no network",
    ),
    (
        "create/check provider registry metadata",
        "describe what a provider health check would do",
    ),
    ("Stage 34 gate:", "Stage 35 gate:"),
    ("Stage 34:", "Stage 35:"),
    (
        "keep providers disabled unless approved",
        "no provider calls, no keys read",
    ),
    (
        "Provider health-check dry-run stage blocked",
        "First manual model call stage blocked",
    ),
    # Constant identifiers imported by name (only test_command_aliases.py uses these).
    ("STAGE33_OPERATIONAL_NEXT_ACTION", "STAGE34_OPERATIONAL_NEXT_ACTION"),
    ("STAGE33_SAFE_NEXT_ACTION", "STAGE34_SAFE_NEXT_ACTION"),
]


def main() -> None:
    if not TESTS_DIR.is_dir():
        print("[FAIL] tests/ not found. Run from the project root.")
        raise SystemExit(1)

    total_files = 0
    total_subs = 0
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        original = text
        file_subs = 0
        for old, new in REPLACEMENTS:
            n = text.count(old)
            if n:
                text = text.replace(old, new)
                file_subs += n
        if text != original:
            path.write_text(text, encoding="utf-8")
            total_files += 1
            total_subs += file_subs
            print(f"  [ok] {path.name}: {file_subs} replacement(s)")

    print(f"[done] {total_subs} replacement(s) across {total_files} file(s).")


if __name__ == "__main__":
    main()
