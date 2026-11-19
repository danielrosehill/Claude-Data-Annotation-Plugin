#!/usr/bin/env python3
"""Turn a run's outputs into blinded items for human rating, and back again.

  rate         --responses F --out items.jsonl --key key.json
  pairs        --responses F --out items.jsonl --key key.json [--per-output N]
  unblind      --reviews F --key key.json --out F
  preferences  --reviews F --items items.jsonl --key key.json --out F

Responses are JSONL with `model`, plus `prompt_id` and `prompt`, plus the output in
`response`, `output`, `text` or `image`. The key maps opaque ids to models: it must stay
out of the Space and out of the rating dataset, or the rating isn't blind.
Reviews are JSONL with `id`, `verdict` (a, b, tie, both_bad for pairs) and `reviewer`.
Standard library only. Output is JSON on stdout.
"""
import argparse
import json
import random
import secrets
import sys

FIELDS = ("response", "output", "text", "image")


def read(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def write(path, rows):
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def content(row):
    for field in FIELDS:
        if row.get(field):
            return field, row[field]
    return None, None


def usable(path):
    rows, skipped = [], 0
    for row in read(path):
        field, value = content(row)
        if value is None or "model" not in row:
            skipped += 1
            continue
        rows.append({"model": row["model"], "prompt_id": str(row.get("prompt_id", "default")),
                     "prompt": row.get("prompt", ""), "field": field, "value": value})
    if not rows:
        sys.exit(f"no usable rows in {path}: need `model` and one of {FIELDS}")
    return rows, skipped


def opaque():
    return secrets.token_hex(6)


def cmd_rate(a):
    rows, skipped = usable(a.responses)
    random.shuffle(rows)
    items, key = [], {}
    for r in rows:
        item_id = opaque()
        key[item_id] = {"model": r["model"]}
        items.append({"id": item_id, "prompt_id": r["prompt_id"], "prompt": r["prompt"], r["field"]: r["value"]})
    write(a.out, items)
    with open(a.key, "w") as f:
        json.dump(key, f, indent=1)
    print(json.dumps({"items": len(items), "skipped": skipped, "out": a.out, "key": a.key}, indent=1))


def cmd_pairs(a):
    rows, skipped = usable(a.responses)
    by_prompt = {}
    for r in rows:
        by_prompt.setdefault(r["prompt_id"], []).append(r)
    items, key, seen = [], {}, set()
    for prompt_id, group in by_prompt.items():
        for _ in range(a.per_output):
            random.shuffle(group)
            for left, right in zip(group[0::2], group[1::2]):
                if left["model"] == right["model"]:
                    continue
                marker = frozenset((id(left), id(right)))
                if marker in seen:
                    continue
                seen.add(marker)
                item_id = opaque()
                key[item_id] = {"a": left["model"], "b": right["model"]}
                items.append({"id": item_id, "prompt_id": prompt_id, "prompt": left["prompt"],
                              "a": left["value"], "b": right["value"], "kind": left["field"]})
    random.shuffle(items)
    write(a.out, items)
    with open(a.key, "w") as f:
        json.dump(key, f, indent=1)
    print(json.dumps({"pairs": len(items), "prompts": len(by_prompt), "skipped": skipped, "out": a.out, "key": a.key}, indent=1))


def cmd_unblind(a):
    key = json.load(open(a.key))
    rows, unknown = [], 0
    for r in read(a.reviews):
        if r.get("id") in key:
            rows.append({**r, **key[r["id"]]})
        else:
            unknown += 1
    write(a.out, rows)
    print(json.dumps({"unblinded": len(rows), "unknown_ids": unknown, "out": a.out}, indent=1))


def cmd_preferences(a):
    key = json.load(open(a.key))
    items = {i["id"]: i for i in read(a.items)}
    rows, dropped = [], {}
    for r in read(a.reviews):
        verdict, item = r.get("verdict"), items.get(r.get("id"))
        if item is None or verdict not in ("a", "b"):
            reason = "unknown_id" if item is None else str(verdict)
            dropped[reason] = dropped.get(reason, 0) + 1
            continue
        loser = "b" if verdict == "a" else "a"
        models = key.get(r["id"], {})
        rows.append({"prompt": item["prompt"], "chosen": item[verdict], "rejected": item[loser],
                     "chosen_model": models.get(verdict), "rejected_model": models.get(loser),
                     "reviewer": r.get("reviewer"), "note": r.get("note")})
    write(a.out, rows)
    print(json.dumps({"preferences": len(rows), "dropped": dropped, "out": a.out}, indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("rate", cmd_rate), ("pairs", cmd_pairs)):
        s = sub.add_parser(name)
        s.add_argument("--responses", required=True); s.add_argument("--out", required=True); s.add_argument("--key", required=True)
        if name == "pairs":
            s.add_argument("--per-output", type=int, default=2)
        s.set_defaults(fn=fn)
    s = sub.add_parser("unblind"); s.add_argument("--reviews", required=True); s.add_argument("--key", required=True); s.add_argument("--out", required=True); s.set_defaults(fn=cmd_unblind)
    s = sub.add_parser("preferences"); s.add_argument("--reviews", required=True); s.add_argument("--items", required=True); s.add_argument("--key", required=True); s.add_argument("--out", required=True); s.set_defaults(fn=cmd_preferences)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
