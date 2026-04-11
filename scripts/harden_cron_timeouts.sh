#!/usr/bin/env bash
set -euo pipefail

# Function purpose: Tune known long-running ingestion jobs to reduce timeout flapping.
# Assumption: these job IDs are from the current local OpenClaw deployment.

echo "[cron-hardening] applying timeout/profile updates"

# maxwell gmail-backfill-12m-20m
openclaw cron edit 292d2a4f-fd28-4b06-bd94-29283a902753 \
  --timeout-seconds 420 \
  --thinking off \
  --tools exec,read,write

# polly ingestion-watch-15m
openclaw cron edit 3ccc95b8-5528-4b13-997f-cdbe344024e8 \
  --timeout-seconds 420 \
  --thinking off \
  --tools read,write

# maxwell gmail-sweep-5m
openclaw cron edit 37234939-3257-41a4-9d09-8c5a0ab14050 \
  --timeout-seconds 420 \
  --thinking off \
  --tools exec,read,write

# rex contacts-sync-6h
openclaw cron edit e9f2a862-d75d-4dfb-a2a3-db4841a4f152 \
  --timeout-seconds 600 \
  --thinking off \
  --tools exec,read,write

# otto outlook-sweep
openclaw cron edit d82aef74-97a5-4bc6-bd83-11847b21a58f \
  --timeout-seconds 900 \
  --thinking off

echo "[cron-hardening] done"
