#!/usr/bin/env python3
"""Reconcile stale OpenClaw runtime state before gateway startup.

Purpose:
- mark stale `running` CLI/subagent tasks as `lost` when no gateway/agent
  processes are active (safe startup window)
- remove orphaned session lock files whose PIDs no longer exist
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


RUNTIMES_TO_RECONCILE = ("cli", "subagent")


@dataclass
class ReconcileSummary:
    db_exists: bool
    db_backed_up_to: str | None
    running_candidates: int
    tasks_marked_lost: int
    lock_files_seen: int
    lock_files_removed: int
    skipped_due_to_active_runtime: bool
    active_runtime_pids: List[str]


def _pid_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _pgrep_exact(name: str) -> List[str]:
    try:
        proc = subprocess.run(
            ["pgrep", "-x", name],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _active_runtime_pids() -> List[str]:
    pids = set()
    for exe in ("openclaw-gateway", "openclaw-agent"):
        pids.update(_pgrep_exact(exe))
    return sorted(pids)


def _cleanup_orphan_locks(openclaw_home: Path, dry_run: bool) -> tuple[int, int]:
    pattern = str(openclaw_home / "agents" / "*" / "sessions" / "*.jsonl.lock")
    lock_paths = sorted(glob.glob(pattern))
    removed = 0
    for lock_path in lock_paths:
        try:
            payload = json.loads(Path(lock_path).read_text(encoding="utf-8"))
            pid = int(payload.get("pid", 0))
        except Exception:
            pid = 0
        if _pid_exists(pid):
            continue
        if not dry_run:
            try:
                Path(lock_path).unlink(missing_ok=True)
            except Exception:
                continue
        removed += 1
    return len(lock_paths), removed


def _backup_db(db_path: Path, dry_run: bool) -> str | None:
    if dry_run or not db_path.exists():
        return None
    ts = time.strftime("%Y%m%dT%H%M%S")
    backup_path = db_path.with_name(f"{db_path.name}.bak-startup-reconcile-{ts}")
    shutil.copy2(db_path, backup_path)
    return str(backup_path)


def _reconcile_running_tasks(db_path: Path, grace_seconds: int, dry_run: bool) -> tuple[int, int]:
    if not db_path.exists():
        return 0, 0
    now_ms = int(time.time() * 1000)
    cutoff_ms = now_ms - max(0, grace_seconds) * 1000
    placeholders = ",".join("?" for _ in RUNTIMES_TO_RECONCILE)
    where_clause = (
        "status='running' "
        f"AND runtime IN ({placeholders}) "
        "AND COALESCE(last_event_at, started_at, created_at, 0) <= ?"
    )
    params: Iterable[object] = tuple(RUNTIMES_TO_RECONCILE) + (cutoff_ms,)

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT COUNT(*) FROM task_runs WHERE {where_clause}",
            params,
        )
        candidates = int(cur.fetchone()[0] or 0)
        if dry_run or candidates == 0:
            return candidates, 0
        cur.execute(
            (
                "UPDATE task_runs "
                "SET status='lost', "
                "error='startup stale task reconciliation', "
                "terminal_outcome='error', "
                "ended_at=?, "
                "last_event_at=?, "
                "cleanup_after=? "
                f"WHERE {where_clause}"
            ),
            (now_ms, now_ms, now_ms + 86400000, *params),
        )
        conn.commit()
        return candidates, int(cur.rowcount or 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--openclaw-home",
        default=os.environ.get("OPENCLAW_HOME", str(Path.home() / ".openclaw")),
        help="OpenClaw home directory (default: ~/.openclaw)",
    )
    parser.add_argument(
        "--grace-seconds",
        type=int,
        default=90,
        help="Only reconcile running tasks older than this threshold.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run reconciliation even when gateway/agent processes are active.",
    )
    args = parser.parse_args()

    openclaw_home = Path(args.openclaw_home).expanduser()
    db_path = openclaw_home / "tasks" / "runs.sqlite"
    active_pids = _active_runtime_pids()
    skip = bool(active_pids) and not args.force

    db_backup = None
    candidates = 0
    marked = 0
    if not skip:
        db_backup = _backup_db(db_path, args.dry_run)
        candidates, marked = _reconcile_running_tasks(
            db_path=db_path,
            grace_seconds=args.grace_seconds,
            dry_run=args.dry_run,
        )

    locks_seen, locks_removed = _cleanup_orphan_locks(
        openclaw_home=openclaw_home,
        dry_run=args.dry_run,
    )

    summary = ReconcileSummary(
        db_exists=db_path.exists(),
        db_backed_up_to=db_backup,
        running_candidates=candidates,
        tasks_marked_lost=marked,
        lock_files_seen=locks_seen,
        lock_files_removed=locks_removed,
        skipped_due_to_active_runtime=skip,
        active_runtime_pids=active_pids,
    )
    print(json.dumps(summary.__dict__, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
