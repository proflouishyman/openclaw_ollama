#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path


USAGE_RE = re.compile(
    r'"usage"\s*:\s*\{\s*"input"\s*:\s*(\d+)\s*,\s*"output"\s*:\s*(\d+)\s*,\s*"total"\s*:\s*(\d+)',
    re.S,
)
LAST_CALL_RE = re.compile(
    r'"lastCallUsage"\s*:\s*\{[^}]*?"cacheRead"\s*:\s*(\d+)\s*,\s*"cacheWrite"\s*:\s*(\d+)',
    re.S,
)


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lower = math.floor(pos)
    upper = math.ceil(pos)
    if lower == upper:
        return float(ordered[lower])
    low_v = ordered[lower]
    up_v = ordered[upper]
    return float(low_v + (up_v - low_v) * (pos - lower))


def fmt_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


def parse_turn_usage(turn: dict) -> dict | None:
    blob = (turn.get("stdout_excerpt") or "") + "\n" + (turn.get("stderr_excerpt") or "")
    usage_match = USAGE_RE.search(blob)
    if not usage_match:
        return None
    input_tokens, output_tokens, total_tokens = map(int, usage_match.groups())
    parsed = {
        "input": input_tokens,
        "output": output_tokens,
        "total": total_tokens,
    }
    last_call_match = LAST_CALL_RE.search(blob)
    if last_call_match:
        cache_read, cache_write = map(int, last_call_match.groups())
        parsed["cacheRead"] = cache_read
        parsed["cacheWrite"] = cache_write
    return parsed


def summarize(payload: dict) -> dict:
    summary = payload["measured"]["summary"]
    turns = payload["measured"]["turns"]
    enriched_turns = []
    token_turns = []

    for turn in turns:
        usage = parse_turn_usage(turn)
        row = {
            "turn": turn["turn"],
            "ok": turn["ok"],
            "timeout": turn["timeout"],
            "latency_s": turn["latency_s"],
            "usage": usage,
        }
        enriched_turns.append(row)
        if turn["ok"] and usage:
            token_turns.append(row)

    totals = {
        "input": sum(t["usage"]["input"] for t in token_turns),
        "output": sum(t["usage"]["output"] for t in token_turns),
        "total": sum(t["usage"]["total"] for t in token_turns),
        "cacheRead": sum(t["usage"].get("cacheRead", 0) for t in token_turns),
        "cacheWrite": sum(t["usage"].get("cacheWrite", 0) for t in token_turns),
    }
    count = len(token_turns)
    total_per_turn = [t["usage"]["total"] for t in token_turns]
    tokens_per_second = [t["usage"]["total"] / max(t["latency_s"], 1e-9) for t in token_turns]

    return {
        "ok": summary["ok"],
        "failed": summary["failed"],
        "timeouts": summary["timeouts"],
        "timeout_rate": summary["timeout_rate"],
        "turns_with_usage": sum(1 for t in enriched_turns if t["usage"] is not None),
        "turns": enriched_turns,
        "token_metrics": {
            "count": count,
            "sum": totals,
            "avg_per_ok_turn": {
                "input": (totals["input"] / count) if count else None,
                "output": (totals["output"] / count) if count else None,
                "total": (totals["total"] / count) if count else None,
            },
            "p50_total_per_ok_turn": percentile(total_per_turn, 0.5),
            "p95_total_per_ok_turn": percentile(total_per_turn, 0.95),
            "mean_tokens_per_second": (sum(tokens_per_second) / count) if count else None,
            "p50_tokens_per_second": percentile(tokens_per_second, 0.5),
            "p95_tokens_per_second": percentile(tokens_per_second, 0.95),
        },
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    source_root = Path("/Users/louishyman/openclaw/runtime_metrics")
    out_md = repo_root / "docs/TOKEN_USAGE_COMPARISON_2026-04-10.md"
    out_json = repo_root / "docs/token-usage-comparison-2026-04-10.json"

    files = {
        "bundled_baseline": source_root / "ollama-kv-ab10-bundled.json",
        "shadow_first_pass": source_root / "ollama-kv-ab10-shadow.json",
        "shadow_warm_rerun": source_root / "ollama-kv-ab10-shadow-rerun.json",
    }

    results = {name: summarize(load(path)) for name, path in files.items()}
    baseline = results["bundled_baseline"]["token_metrics"]
    shadow = results["shadow_first_pass"]["token_metrics"]
    rerun = results["shadow_warm_rerun"]["token_metrics"]

    derived = {
        "mean_tps_speedup_vs_baseline": {
            "shadow_first_pass": (
                shadow["mean_tokens_per_second"] / baseline["mean_tokens_per_second"]
                if shadow["mean_tokens_per_second"] and baseline["mean_tokens_per_second"]
                else None
            ),
            "shadow_warm_rerun": (
                rerun["mean_tokens_per_second"] / baseline["mean_tokens_per_second"]
                if rerun["mean_tokens_per_second"] and baseline["mean_tokens_per_second"]
                else None
            ),
        },
        "p50_tps_speedup_vs_baseline": {
            "shadow_first_pass": (
                shadow["p50_tokens_per_second"] / baseline["p50_tokens_per_second"]
                if shadow["p50_tokens_per_second"] and baseline["p50_tokens_per_second"]
                else None
            ),
            "shadow_warm_rerun": (
                rerun["p50_tokens_per_second"] / baseline["p50_tokens_per_second"]
                if rerun["p50_tokens_per_second"] and baseline["p50_tokens_per_second"]
                else None
            ),
        },
    }

    out_json.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "sources": {k: str(v) for k, v in files.items()},
                "results": results,
                "derived": derived,
                "notes": [
                    "Token values are parsed from OpenClaw benchmark stdout/stderr excerpts.",
                    "Timeout turns generally do not include usage payloads and are excluded from per-ok-turn aggregates.",
                ],
            },
            indent=2,
        )
    )

    rows = ["bundled_baseline", "shadow_first_pass", "shadow_warm_rerun"]
    md = []
    md.append("# Ollama KV Cache Token Usage Comparison (2026-04-10, 10 Turns)")
    md.append("")
    md.append("Token counts are derived from the same 10-turn latency experiment artifacts.")
    md.append("")
    md.append("## Summary Table")
    md.append("")
    md.append(
        "| Scenario | OK/Total | Usage Parsed | Input Sum | Output Sum | Total Sum | Avg Total/OK Turn | Mean Tokens/s |"
    )
    md.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for scenario in rows:
        r = results[scenario]
        t = r["token_metrics"]
        total_turns = r["ok"] + r["failed"]
        md.append(
            "| "
            + f"{scenario} | {r['ok']}/{total_turns} | {r['turns_with_usage']}/{total_turns} | "
            + f"{t['sum']['input']} | {t['sum']['output']} | {t['sum']['total']} | "
            + f"{fmt_float(t['avg_per_ok_turn']['total'])} | {fmt_float(t['mean_tokens_per_second'])} |"
        )

    md.append("")
    md.append("## Distribution (Total Tokens Per Successful Turn)")
    md.append("")
    md.append("| Scenario | p50 Total | p95 Total | p50 Tokens/s | p95 Tokens/s |")
    md.append("| --- | --- | --- | --- | --- |")
    for scenario in rows:
        t = results[scenario]["token_metrics"]
        md.append(
            "| "
            + f"{scenario} | {fmt_float(t['p50_total_per_ok_turn'])} | {fmt_float(t['p95_total_per_ok_turn'])} | "
            + f"{fmt_float(t['p50_tokens_per_second'])} | {fmt_float(t['p95_tokens_per_second'])} |"
        )

    md.append("")
    md.append("## Throughput Speedup vs Bundled Baseline")
    md.append("")
    md.append("| Scenario | Mean Tokens/s Speedup | p50 Tokens/s Speedup |")
    md.append("| --- | --- | --- |")
    md.append(
        "| shadow_first_pass | "
        + f"{fmt_float(derived['mean_tps_speedup_vs_baseline']['shadow_first_pass'])}x | "
        + f"{fmt_float(derived['p50_tps_speedup_vs_baseline']['shadow_first_pass'])}x |"
    )
    md.append(
        "| shadow_warm_rerun | "
        + f"{fmt_float(derived['mean_tps_speedup_vs_baseline']['shadow_warm_rerun'])}x | "
        + f"{fmt_float(derived['p50_tps_speedup_vs_baseline']['shadow_warm_rerun'])}x |"
    )
    md.append("")
    md.append("## Per-turn Parsed Usage")
    md.append("")
    for scenario in rows:
        md.append(f"### {scenario}")
        for turn in results[scenario]["turns"]:
            usage = turn["usage"]
            if usage is None:
                md.append(
                    f"- t{turn['turn']}: ok={turn['ok']} timeout={turn['timeout']} usage=missing latency={turn['latency_s']:.3f}s"
                )
            else:
                md.append(
                    f"- t{turn['turn']}: ok={turn['ok']} timeout={turn['timeout']} "
                    + f"input={usage['input']} output={usage['output']} total={usage['total']} "
                    + f"cacheRead={usage.get('cacheRead', 0)} cacheWrite={usage.get('cacheWrite', 0)} "
                    + f"latency={turn['latency_s']:.3f}s"
                )
        md.append("")

    md.append("## Notes")
    md.append("")
    md.append("- Token counts are similar across bundled and shadow warm scenarios.")
    md.append("- Latency improvements therefore come from faster execution path, not fewer prompt tokens.")
    md.append("- `cacheRead/cacheWrite` are reported as zero in these artifacts.")
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
