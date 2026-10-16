#!/usr/bin/env python3
"""
Deterministic Pre-Implementation & Post-Implementation Verification Gate
for the `telegram-copilot-bot` OpenSpec change.

Usage:
    python scripts/verify_telegram_copilot_gate.py

What this gate checks automatically:
1. Workspace Hygiene (`scripts/check_workspace_hygiene.py`).
2. Required Target Files & Module Compilation (`backend/app/telegram/*`, `backend/app/api/v1/telegram.py`).
3. OpenAPI Contract Routes (`/api/v1/telegram/webhook`, admin enrollment & revocation routes).
4. Full Automated Pytest Suite (`backend/tests/test_telegram_copilot.py`) with FakeTelegramAPIServer
   verifying AC-1 through AC-8 (inbound webhook auth, single-use enrollment, role anti-spoofing,
   idempotency, read-only barrier, and outbound `api.telegram.org` HTTP payload verification).
5. Regression Check on Existing Web Copilot (`backend/tests/test_copilot_api.py`).

Exit code:
    0 -> ALL GATES PASSED (Implementation is verified)
    1 -> GATE FAILED (Missing files, broken contract, or failing tests)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "backend/app/telegram/__init__.py",
    "backend/app/telegram/schemas.py",
    "backend/app/telegram/security.py",
    "backend/app/telegram/store.py",
    "backend/app/telegram/transport.py",
    "backend/app/api/v1/telegram.py",
    "backend/tests/test_telegram_copilot.py",
]

REQUIRED_OPENAPI_PATHS = [
    "/api/v1/telegram/webhook",
    "/api/v1/telegram/admin/enrollment-codes",
    "/api/v1/telegram/admin/bindings/{telegram_chat_id}/revoke",
    "/api/v1/copilot/chat",
]


def run_step(title: str, cmd: list[str]) -> bool:
    print(f"\n[GATE] {title}")
    print(f"  $ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=REPO_ROOT)
    if proc.returncode != 0:
        print(f"  -> [FAIL] {title} (exit code {proc.returncode})")
        return False
    print(f"  -> [PASS] {title}")
    return True


def main() -> int:
    print("=" * 76)
    print("TELEGRAM COPILOT BOT — AUTOMATED VERIFICATION GATE")
    print("=" * 76)

    all_passed = True

    # 1. Workspace hygiene
    if not run_step(
        "Step 1/5: Workspace Hygiene Check",
        [sys.executable, "scripts/check_workspace_hygiene.py"],
    ):
        all_passed = False

    # 2. Target file existence & syntax compilation
    print("\n[GATE] Step 2/5: Target Files & Python Compilation")
    missing_files = [rel for rel in REQUIRED_FILES if not (REPO_ROOT / rel).is_file()]
    if missing_files:
        for m in missing_files:
            print(f"  -> [MISSING] {m}")
        print("  -> [FAIL] Target Files Check")
        all_passed = False
    else:
        if not run_step(
            "Step 2b/5: Bytecode Compilation Check",
            [
                sys.executable,
                "-m",
                "compileall",
                "-q",
                "backend/app/telegram",
                "backend/app/api/v1/telegram.py",
                "backend/app/api/v1/copilot.py",
            ],
        ):
            all_passed = False

    # 3. OpenAPI route registration check
    openapi_check_code = (
        "from backend.app.main import app; "
        "paths = app.openapi().get('paths', {}); "
        f"missing = [p for p in {REQUIRED_OPENAPI_PATHS!r} if p not in paths]; "
        "assert not missing, f'Missing OpenAPI paths: {missing}'; "
        "print('  -> Verified OpenAPI paths:', list(paths.keys()))"
    )
    if not run_step(
        "Step 3/5: OpenAPI Route Contract Verification",
        [sys.executable, "-c", openapi_check_code],
    ):
        all_passed = False

    # 4. Telegram Copilot Bot AC-1..AC-8 Test Suite
    if not run_step(
        "Step 4/5: Telegram Copilot Bot Automated Test Suite (AC-1..AC-8)",
        [sys.executable, "-m", "pytest", "-q", "backend/tests/test_telegram_copilot.py"],
    ):
        all_passed = False

    # 5. Existing Web Copilot Regression Suite
    if not run_step(
        "Step 5/5: Existing Copilot API Regression Suite",
        [sys.executable, "-m", "pytest", "-q", "backend/tests/test_copilot_api.py"],
    ):
        all_passed = False

    print("\n" + "=" * 76)
    if all_passed:
        print("VERDICT: PASS — All Telegram Copilot Bot verification gates succeeded.")
        print("=" * 76)
        return 0
    else:
        print("VERDICT: FAIL — One or more verification gates failed (see details above).")
        print("=" * 76)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
