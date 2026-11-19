#!/usr/bin/env python3
"""Resolve and read the data-annotation user overlay (standard library only).

Usage:
    uv run overlay.py path            print the data folder (does not create it)
    uv run overlay.py show            print path, profile.env values and the overlay files present
    uv run overlay.py get KEY [DEF]   print one profile.env value (environment variable of the same name wins)
    uv run overlay.py init            create the folder with empty profile.env / preferences.md if missing

Resolution order (first match wins):
    $DATA_ANNOTATION_DIR
    $CLAUDE_USER_DATA/data-annotation
    ~/.claude-user-data/data-annotation        if ~/.claude-user-data exists
    ${XDG_DATA_HOME:-~/.local/share}/claude-plugins/data-annotation

Secrets never live in the overlay: profile.env holds URLs, names and the NAMES of environment
variables that carry tokens.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

NAME = "data-annotation"


def data_dir() -> Path:
    if os.environ.get("DATA_ANNOTATION_DIR"):
        return Path(os.environ["DATA_ANNOTATION_DIR"]).expanduser()
    if os.environ.get("CLAUDE_USER_DATA"):
        return Path(os.environ["CLAUDE_USER_DATA"]).expanduser() / NAME
    home = Path.home()
    if (home / ".claude-user-data").is_dir():
        return home / ".claude-user-data" / NAME
    xdg = Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share")
    return xdg / "claude-plugins" / NAME


def profile(d: Path | None = None) -> dict[str, str]:
    f = (d or data_dir()) / "profile.env"
    vals: dict[str, str] = {}
    if f.is_file():
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def get(key: str, default: str = "") -> str:
    return os.environ.get(key) or profile().get(key, default)


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "show"
    d = data_dir()
    if cmd == "path":
        print(d)
    elif cmd == "get":
        print(get(argv[1], argv[2] if len(argv) > 2 else ""))
    elif cmd == "init":
        d.mkdir(parents=True, exist_ok=True)
        for n in ("profile.env", "preferences.md"):
            (d / n).touch(exist_ok=True)
        print(d)
    else:
        files = sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()) if d.is_dir() else []
        print(json.dumps({"data_dir": str(d), "exists": d.is_dir(), "profile": profile(d), "files": files},
                         indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
