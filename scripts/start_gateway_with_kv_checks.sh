#!/usr/bin/env bash
set -euo pipefail

# Function purpose: Start OpenClaw gateway with an Ollama shadow-plugin preflight.
# This script is intended to be used as the launchd ProgramArguments entrypoint.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PLUGIN_PATH="${OPENCLAW_OLLAMA_PLUGIN_PATH:-${REPO_ROOT}}"
MODEL_KEY="${OPENCLAW_OLLAMA_MODEL_KEY:-ollama/gemma4:26b}"
KEEP_ALIVE="${OPENCLAW_OLLAMA_KEEPALIVE:-45m}"
NUM_BATCH="${OPENCLAW_OLLAMA_NUM_BATCH:-16}"
REQUEST_TIMEOUT_MS="${OPENCLAW_OLLAMA_REQUEST_TIMEOUT_MS:-90000}"
MAX_RETRIES="${OPENCLAW_OLLAMA_MAX_RETRIES:-1}"
RETRY_BACKOFF_MS="${OPENCLAW_OLLAMA_RETRY_BACKOFF_MS:-250}"

# Reconcile stale runtime state before gateway boot to avoid lock resurrection.
python3 "${SCRIPT_DIR}/reconcile_runtime_state.py" \
  --grace-seconds 0 >/dev/null || true

python3 "${SCRIPT_DIR}/apply_openclaw_config.py" \
  --plugin-path "${PLUGIN_PATH}" \
  --model-key "${MODEL_KEY}" \
  --keep-alive "${KEEP_ALIVE}" \
  --num-batch "${NUM_BATCH}" \
  --request-timeout-ms "${REQUEST_TIMEOUT_MS}" \
  --max-retries "${MAX_RETRIES}" \
  --retry-backoff-ms "${RETRY_BACKOFF_MS}" >/dev/null || true

if inspect_json="$(openclaw plugins inspect ollama --json 2>/dev/null)"; then
  source_path="$(python3 - "${inspect_json}" <<'PY'
import json
import sys
raw = sys.argv[1]
start = raw.find("{")
end = raw.rfind("}")
if start < 0 or end < 0 or end <= start:
    print("")
    raise SystemExit(0)
snippet = raw[start : end + 1]
try:
    payload = json.loads(snippet)
except Exception:
    print("")
    raise SystemExit(0)
print(payload.get("plugin", {}).get("source", ""))
PY
)"
  if [[ "${source_path}" == "${PLUGIN_PATH}/index.js" ]]; then
    echo "[kv-startup] ollama shadow plugin active: ${source_path}"
  else
    echo "[kv-startup] warning: unexpected ollama plugin source: ${source_path}" >&2
  fi
fi

exec openclaw gateway run "$@"
