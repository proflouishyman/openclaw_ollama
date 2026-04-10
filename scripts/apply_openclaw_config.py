#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply shadow ollama plugin config.")
    parser.add_argument(
        "--config",
        default=str(Path.home() / ".openclaw/openclaw.json"),
        help="Path to openclaw.json",
    )
    parser.add_argument(
        "--plugin-path",
        default=str(Path(__file__).resolve().parent.parent),
        help="Path to plugin root to add under plugins.load.paths",
    )
    parser.add_argument(
        "--model-key",
        default="ollama/gemma4:26b",
        help="Model key under agents.defaults.models",
    )
    parser.add_argument("--keep-alive", default="45m", help="params.ollama.keepAlive value")
    parser.add_argument(
        "--num-batch",
        type=int,
        default=16,
        help="params.ollama.options.num_batch value",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    cfg = json.loads(config_path.read_text())
    changed = False

    plugins = cfg.setdefault("plugins", {})
    load = plugins.setdefault("load", {})
    paths = load.get("paths")
    if not isinstance(paths, list):
        paths = []
    if args.plugin_path not in paths:
        paths.insert(0, args.plugin_path)
        changed = True
    load["paths"] = paths

    agents = cfg.setdefault("agents", {})
    defaults = agents.setdefault("defaults", {})
    models = defaults.setdefault("models", {})
    model_cfg = models.setdefault(args.model_key, {})
    params = model_cfg.setdefault("params", {})
    ollama = params.setdefault("ollama", {})
    if ollama.get("keepAlive") != args.keep_alive:
        ollama["keepAlive"] = args.keep_alive
        changed = True
    options = ollama.get("options")
    if not isinstance(options, dict):
        options = {}
    if options.get("num_batch") != args.num_batch:
        options["num_batch"] = args.num_batch
        changed = True
    ollama["options"] = options

    if changed:
        config_path.write_text(json.dumps(cfg, indent=2) + "\n")
        print(f"Updated {config_path}")
    else:
        print(f"No changes needed: {config_path}")


if __name__ == "__main__":
    main()
