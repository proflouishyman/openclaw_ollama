#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class TurnResult:
    turn: int
    ok: bool
    latency_s: float
    timeout: bool
    rc: int
    stderr_excerpt: str
    stdout_excerpt: str


def run_turn(agent: str, session_id: str, message: str, timeout_seconds: int) -> TurnResult:
    cmd = [
        "openclaw",
        "agent",
        "--agent",
        agent,
        "--session-id",
        session_id,
        "--message",
        message,
        "--json",
        "--thinking",
        "off",
    ]
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        latency = time.perf_counter() - start
        return TurnResult(
            turn=-1,
            ok=completed.returncode == 0,
            latency_s=latency,
            timeout=False,
            rc=completed.returncode,
            stderr_excerpt=(completed.stderr or "")[:1200],
            stdout_excerpt=(completed.stdout or "")[:1200],
        )
    except subprocess.TimeoutExpired as exc:
        latency = time.perf_counter() - start
        out = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return TurnResult(
            turn=-1,
            ok=False,
            latency_s=latency,
            timeout=True,
            rc=124,
            stderr_excerpt=err[:1200],
            stdout_excerpt=out[:1200],
        )


def percentile(values: list[float], p: int) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[p - 1]


def summarize(results: list[TurnResult]) -> dict[str, Any]:
    ok_latencies = [r.latency_s for r in results if r.ok]
    total = len(results)
    failed = sum(1 for r in results if not r.ok)
    timeouts = sum(1 for r in results if r.timeout)
    return {
        "count": total,
        "ok": total - failed,
        "failed": failed,
        "timeouts": timeouts,
        "timeout_rate": (timeouts / total) if total else 0.0,
        "latency": {
            "p50": percentile(ok_latencies, 50),
            "p95": percentile(ok_latencies, 95),
            "mean": statistics.mean(ok_latencies) if ok_latencies else None,
            "min": min(ok_latencies) if ok_latencies else None,
            "max": max(ok_latencies) if ok_latencies else None,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default="main")
    parser.add_argument("--session-id", default="kv-benchmark")
    parser.add_argument("--message", required=True)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--turns", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--out", default="benchmark-result.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    warmup: list[TurnResult] = []
    measured: list[TurnResult] = []

    for idx in range(args.warmup):
        res = run_turn(args.agent, args.session_id, args.message, args.timeout_seconds)
        res.turn = idx + 1
        warmup.append(res)
        print(f"warmup {res.turn}/{args.warmup}: ok={res.ok} latency={res.latency_s:.3f}s")

    for idx in range(args.turns):
        res = run_turn(args.agent, args.session_id, args.message, args.timeout_seconds)
        res.turn = idx + 1
        measured.append(res)
        print(f"turn {res.turn}/{args.turns}: ok={res.ok} latency={res.latency_s:.3f}s")

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "agent": args.agent,
        "session_id": args.session_id,
        "message": args.message,
        "timeout_seconds": args.timeout_seconds,
        "warmup": {"count": args.warmup, "summary": summarize(warmup), "turns": [asdict(x) for x in warmup]},
        "measured": {"count": args.turns, "summary": summarize(measured), "turns": [asdict(x) for x in measured]},
    }

    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    print(f"saved: {out}")


if __name__ == "__main__":
    main()
