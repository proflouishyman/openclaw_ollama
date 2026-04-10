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

## Upgrade notes

After OpenClaw updates, rerun:

```bash
python3 scripts/generate_bundled_shim.py
```

That refreshes the absolute bundled import target used by the plugin.
