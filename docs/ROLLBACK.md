# Rollback

## Runtime rollback

1. Edit `~/.openclaw/openclaw.json`.
2. Remove this plugin path from `plugins.load.paths`.
3. Restart gateway:

```bash
openclaw gateway restart
```

## launchd rollback (macOS)

If you applied `scripts/setup_launchagent.py`, restore backup plist:

```bash
cp ~/Library/LaunchAgents/ai.openclaw.gateway.plist.bak.kvstartup \
   ~/Library/LaunchAgents/ai.openclaw.gateway.plist
openclaw gateway restart
```

If your backup has a different suffix, use that filename.

## Validation

```bash
openclaw plugins inspect ollama --json
```

Bundled source should be:

`/opt/homebrew/lib/node_modules/openclaw/dist/extensions/ollama/index.js`

or your platform's equivalent OpenClaw install path.
