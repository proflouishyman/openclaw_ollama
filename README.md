# OpenClaw Ollama KV Cache Plugin

Shadow `ollama` provider plugin for OpenClaw that injects Ollama cache controls
for static prompt reuse (for example large `SOUL.md` prefixes).

## What it does

- Overrides bundled `ollama` provider via plugin id `ollama`.
- Preserves bundled provider behavior.
- Injects request fields from model params:
  - `params.ollama.keepAlive` -> top-level `keep_alive` (if absent)
  - `params.ollama.options` -> merged into payload `options`
- Keeps OpenClaw core-managed options authoritative when already set:
  - `num_ctx`
  - `temperature`
  - `num_predict`

## Why this exists

As of 2026-04-10, bundled OpenClaw Ollama request building does not expose
request-level `keep_alive` and custom Ollama options in a controlled way.

This plugin is a maintainable bridge until/if upstream exposes first-class
params for these fields.

## Quickstart

1. Generate the bundled-entry shim (machine-specific path resolution):

```bash
python3 scripts/generate_bundled_shim.py
```

2. Apply OpenClaw config changes:

```bash
python3 scripts/apply_openclaw_config.py
```

3. Verify active plugin source:

```bash
openclaw plugins inspect ollama --json
```

Expected source:

`<this-repo>/index.js`

4. Optional: make this persistent at gateway startup (launchd on macOS):

```bash
python3 scripts/setup_launchagent.py
openclaw gateway restart
```

## Config contract

Example in `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "models": {
        "ollama/gemma4:26b": {
          "params": {
            "ollama": {
              "keepAlive": "45m",
              "options": {
                "num_batch": 16
              }
            }
          }
        }
      }
    }
  }
}
```

## Rollback

1. Remove this plugin path from `plugins.load.paths`.
2. Restart gateway.
3. If launchd startup hook was installed, restore your LaunchAgent backup.

Details: [docs/ROLLBACK.md](docs/ROLLBACK.md)

## Tests

```bash
node --test test/cache-controls.test.mjs
```

## Measured results (2026-04-10)

Test setup: fixed SOUL-heavy prompt, `ollama/gemma4:26b`, same agent/session,
4 turns per scenario.

| Scenario | OK/Total | Timeout Rate | p50 (s) | p95 (s) |
| --- | --- | --- | --- | --- |
| Bundled OpenClaw Ollama provider | 4/4 | 0% | 52.20 | 58.11 |
| Shadow provider (first pass) | 1/4 | 75% | 130.93 | 130.93 |
| Shadow provider (warm rerun) | 4/4 | 0% | 3.97 | 4.03 |

Warm rerun speedup vs bundled baseline:

- p50: 13.14x faster
- p95: 14.44x faster
- timeout rate: 0% vs 0% (no regression)

Interpretation:

- Warm-path speedups can be large when static-prefix reuse is effective.
- First-pass behavior may still be noisy depending on host load/model state.
- Run multiple local passes before drawing conclusions.

Details and shareable artifacts:

- `docs/METRICS_COMPARISON_2026-04-10.md`
- `docs/metrics-comparison-2026-04-10.json`
- `docs/TOKEN_USAGE_COMPARISON_2026-04-10.md`
- `docs/token-usage-comparison-2026-04-10.json`

## Token usage comparison (2026-04-10)

From the same A/B benchmark runs:

| Scenario | OK/Total | Input Sum | Output Sum | Total Sum | Avg Total/OK Turn | Mean Tokens/s |
| --- | --- | --- | --- | --- | --- | --- |
| Bundled OpenClaw Ollama provider | 4/4 | 67620 | 24 | 67644 | 16911.00 | 1321.99 |
| Shadow provider (first pass) | 1/4 | 17259 | 6 | 17265 | 17265.00 | 131.86 |
| Shadow provider (warm rerun) | 4/4 | 68978 | 26 | 69004 | 17251.00 | 4340.97 |

Takeaways:

- Token volume per successful turn is similar between bundled and shadow warm runs.
- Latency gains are driven by execution speed, not fewer prompt tokens.
- In these artifacts, `cacheRead/cacheWrite` remained `0`.

Regenerate reports:

```bash
python3 scripts/build_metrics_comparison.py
python3 scripts/build_token_usage_comparison.py
```

## Upgrade notes

After OpenClaw updates, rerun:

```bash
python3 scripts/generate_bundled_shim.py
```

That refreshes the absolute bundled import target used by the plugin.
# openclaw_ollama
