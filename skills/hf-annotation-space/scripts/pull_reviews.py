"""Merge decisions from the review Space into a local reviews.jsonl (append-only, last wins).

    python3 pull_reviews.py <owner>/<dataset> data/reviews.jsonl

Needs the `hf` CLI and HF_TOKEN (or HUGGINGFACE_TOKEN) with read access to the dataset.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main(dataset: str, out: Path, reviews_dir: str = "reviews"):
    env = {**os.environ, "HF_TOKEN": os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN", "")}
    hf = shutil.which("hf") or os.path.expanduser("~/.local/bin/hf")
    have = {(r["id"], r.get("ts")) for r in map(json.loads, open(out))} if out.exists() else set()
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([hf, "download", dataset, "--repo-type", "dataset", "--include", f"{reviews_dir}/*",
                        "--local-dir", d, "--quiet"], check=True, env=env, stdout=subprocess.DEVNULL)
        recs = [json.loads(p.read_text()) for p in sorted(Path(d, reviews_dir).glob("*.json"))]
    new = sorted((r for r in recs if (r["id"], r.get("ts")) not in have), key=lambda r: r.get("ts") or "")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a") as f:
        for r in new:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(recs)} reviews on the Hub, {len(new)} new appended to {out}")


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]))
