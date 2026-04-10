#!/usr/bin/env python3
from __future__ import annotations

import argparse
import plistlib
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch OpenClaw launchd service to use kv startup wrapper.")
    parser.add_argument(
        "--plist",
        default=str(Path.home() / "Library/LaunchAgents/ai.openclaw.gateway.plist"),
        help="LaunchAgent plist path",
    )
    parser.add_argument(
        "--wrapper",
        default=str(Path(__file__).resolve().parent / "start_gateway_with_kv_checks.sh"),
        help="Wrapper script path",
    )
    parser.add_argument("--backup-suffix", default="bak.kvstartup", help="Backup filename suffix")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plist_path = Path(args.plist).expanduser().resolve()
    wrapper_path = Path(args.wrapper).expanduser().resolve()
    backup_path = plist_path.with_name(plist_path.name + "." + args.backup_suffix)

    if not plist_path.exists():
        raise SystemExit(f"LaunchAgent plist not found: {plist_path}")
    if not wrapper_path.exists():
        raise SystemExit(f"Wrapper script not found: {wrapper_path}")

    shutil.copy2(plist_path, backup_path)

    with plist_path.open("rb") as fh:
        data = plistlib.load(fh)

    args_list = data.get("ProgramArguments", [])
    port = "18789"
    if isinstance(args_list, list) and "--port" in args_list:
        idx = args_list.index("--port")
        if idx + 1 < len(args_list):
            port = str(args_list[idx + 1])

    data["ProgramArguments"] = [str(wrapper_path), "--port", port]

    with plist_path.open("wb") as fh:
        plistlib.dump(data, fh, sort_keys=False)

    print(f"Updated LaunchAgent: {plist_path}")
    print(f"Backup: {backup_path}")
    print("Apply with: openclaw gateway restart")


if __name__ == "__main__":
    main()
