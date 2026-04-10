#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def summary_block(payload: dict) -> dict:
    m = payload["measured"]["summary"]
    return {
        "ok": m["ok"],
        "failed": m["failed"],
        "timeouts": m["timeouts"],
        "timeout_rate": m["timeout_rate"],
        "p50": m["latency"]["p50"],
        "p95": m["latency"]["p95"],
        "mean": m["latency"]["mean"],
        "turns": payload["measured"]["turns"],
    }


def fmt_float(value) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def turns_line(turns: list[dict]) -> str:
    parts = []
    for t in turns:
        parts.append(
            f"t{t['turn']}={t['latency_s']:.3f}s"
            + (" timeout" if t.get("timeout") else "")
            + (" ok" if t.get("ok") else " fail")
        )
    return ", ".join(parts)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    source_root = Path("/Users/louishyman/openclaw/runtime_metrics")
    out_md = repo_root / "docs/METRICS_COMPARISON_2026-04-10.md"
    out_json = repo_root / "docs/metrics-comparison-2026-04-10.json"

    files = {
        "bundled_baseline": source_root / "ollama-kv-ab-bundled.json",
        "shadow_first_pass": source_root / "ollama-kv-ab-shadow.json",
        "shadow_warm_rerun": source_root / "ollama-kv-ab-shadow-rerun.json",
    }

    loaded = {name: summary_block(load(path)) for name, path in files.items()}

    out_json.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "sources": {k: str(v) for k, v in files.items()},
                "results": loaded,
            },
            indent=2,
        )
    )

    md = []
    md.append("# Ollama KV Cache Comparison (2026-04-10)")
    md.append("")
    md.append("## Summary Table")
    md.append("")
    md.append("| Scenario | OK/Total | Timeouts | Timeout Rate | p50 (s) | p95 (s) | Mean (s) |")
    md.append("| --- | --- | --- | --- | --- | --- | --- |")
    for scenario in ["bundled_baseline", "shadow_first_pass", "shadow_warm_rerun"]:
        row = loaded[scenario]
        total = row["ok"] + row["failed"]
        md.append(
            "| "
            + f"{scenario} | {row['ok']}/{total} | {row['timeouts']} | {row['timeout_rate']:.3f} | "
            + f"{fmt_float(row['p50'])} | {fmt_float(row['p95'])} | {fmt_float(row['mean'])} |"
        )
    md.append("")
    md.append("## Raw Turn Latencies")
    md.append("")
    for scenario in ["bundled_baseline", "shadow_first_pass", "shadow_warm_rerun"]:
        md.append(f"- `{scenario}`: {turns_line(loaded[scenario]['turns'])}")
    md.append("")
    md.append("## Interpretation")
    md.append("")
    md.append("- Warm rerun with shadow plugin is materially faster than bundled baseline.")
    md.append("- First shadow pass showed severe variance/timeouts, so stability is environment-dependent.")
    md.append("- Recommended publication framing: speedup is achievable, but operators should benchmark on their own host and run multiple passes.")
    md.append("")
    md.append("## Source Files")
    md.append("")
    for name, path in files.items():
        md.append(f"- `{name}`: `{path}`")

    out_md.write_text("\n".join(md) + "\n")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()
