#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def summary_block(payload: dict) -> dict:
    m = payload["measured"]["summary"]
    w = payload.get("warmup", {}).get("summary", {}).get("latency", {}) or {}
    return {
        "ok": m["ok"],
        "failed": m["failed"],
        "timeouts": m["timeouts"],
        "timeout_rate": m["timeout_rate"],
        "p50": m["latency"]["p50"],
        "p95": m["latency"]["p95"],
        "mean": m["latency"]["mean"],
        "warmup_p50": w.get("p50"),
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
        "bundled_baseline": source_root / "ollama-kv-ab10-bundled.json",
        "shadow_first_pass": source_root / "ollama-kv-ab10-shadow.json",
        "shadow_warm_rerun": source_root / "ollama-kv-ab10-shadow-rerun.json",
    }

    loaded = {name: summary_block(load(path)) for name, path in files.items()}
    baseline = loaded["bundled_baseline"]
    shadow = loaded["shadow_first_pass"]
    rerun = loaded["shadow_warm_rerun"]

    p50_speedup_shadow = (baseline["p50"] / shadow["p50"]) if baseline["p50"] and shadow["p50"] else None
    p95_speedup_shadow = (baseline["p95"] / shadow["p95"]) if baseline["p95"] and shadow["p95"] else None
    p50_speedup_rerun = (baseline["p50"] / rerun["p50"]) if baseline["p50"] and rerun["p50"] else None
    p95_speedup_rerun = (baseline["p95"] / rerun["p95"]) if baseline["p95"] and rerun["p95"] else None

    out_json.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "sources": {k: str(v) for k, v in files.items()},
                "results": loaded,
                "derived": {
                    "p50_speedup_vs_baseline": {
                        "shadow_first_pass": p50_speedup_shadow,
                        "shadow_warm_rerun": p50_speedup_rerun,
                    },
                    "p95_speedup_vs_baseline": {
                        "shadow_first_pass": p95_speedup_shadow,
                        "shadow_warm_rerun": p95_speedup_rerun,
                    },
                },
            },
            indent=2,
        )
    )

    md = []
    md.append("# Ollama KV Cache Comparison (2026-04-10, 10 Turns)")
    md.append("")
    md.append("Test setup: `Reply with exactly OK`, same agent/model/session strategy as prior runs, 10 measured turns per scenario.")
    md.append("")
    md.append("## Summary Table")
    md.append("")
    md.append("| Scenario | OK/Total | Timeouts | Timeout Rate | Warmup p50 (s) | p50 (s) | p95 (s) | Mean (s) |")
    md.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for scenario in ["bundled_baseline", "shadow_first_pass", "shadow_warm_rerun"]:
        row = loaded[scenario]
        total = row["ok"] + row["failed"]
        md.append(
            "| "
            + f"{scenario} | {row['ok']}/{total} | {row['timeouts']} | {row['timeout_rate']:.3f} | "
            + f"{fmt_float(row['warmup_p50'])} | {fmt_float(row['p50'])} | {fmt_float(row['p95'])} | {fmt_float(row['mean'])} |"
        )
    md.append("")
    md.append("## Speedup vs Bundled Baseline")
    md.append("")
    md.append("| Scenario | p50 Speedup | p95 Speedup |")
    md.append("| --- | --- | --- |")
    md.append(f"| shadow_first_pass | {fmt_float(p50_speedup_shadow)}x | {fmt_float(p95_speedup_shadow)}x |")
    md.append(f"| shadow_warm_rerun | {fmt_float(p50_speedup_rerun)}x | {fmt_float(p95_speedup_rerun)}x |")
    md.append("")
    md.append("## Raw Turn Latencies")
    md.append("")
    for scenario in ["bundled_baseline", "shadow_first_pass", "shadow_warm_rerun"]:
        md.append(f"- `{scenario}`: {turns_line(loaded[scenario]['turns'])}")
    md.append("")
    md.append("## Interpretation")
    md.append("")
    md.append("- Steady-state shadow performance is substantially faster than bundled baseline (~14x by p50).")
    md.append("- Shadow first pass pays a large cold-start cost (warmup ~118.7s), then stabilizes near ~4s in measured turns.")
    md.append("- Warm rerun shows tail-risk variance (1 timeout and one very slow turn), so p95 can regress despite strong p50.")
    md.append("- Recommended framing: large steady-state win is achievable, but production rollout should monitor long-tail latency and timeout rate.")
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
