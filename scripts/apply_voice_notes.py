#!/usr/bin/env python3
"""Turn spoken annotation notes into structured annotations (standard library plus ffmpeg).

A note is an audio file recorded next to one item. This script transcribes it and asks a model to
fill the annotation structure from what was said, using the item's context. It writes one JSON line
per note with the verbatim transcript, the structured annotation, a confidence and provenance.

Usage (dry run by default: prints each reading and writes nothing):
    uv run apply_voice_notes.py --notes notes.jsonl --schema schema.json --out voice-annotations.jsonl [--apply]
        [--audio-dir DIR] [--model MODEL] [--limit N]

notes.jsonl, one object per line:
    {"id": "n1", "item_id": "i42", "audio": "n1.webm", "context": {...text, reference, allowed categories...}}
schema.json: a JSON object describing the fields to fill, with the allowed values, for example
    {"verdict": ["pass","fail"], "reason": ["wrong word","noise"], "words": [{"index": "int", "issue": "string"}]}

Routes (settings from the overlay profile.env or the environment):
    ASR_ENDPOINT_URL set    -> transcribe there (OpenAI-compatible /v1/audio/transcriptions), then a text model fills the structure
    otherwise               -> one call to an audio-capable OpenRouter model (SPOKEN_ANNOTATION_MODEL) returns transcript + structure
Token values come only from the environment, in the variables named by OPENROUTER_TOKEN_ENV (default OPENROUTER_API_KEY)
and ASR_TOKEN_ENV.

Rules baked in: the model must return null for anything not said or clearly implied; existing hand-made annotations are
never overwritten (this script only appends rows with source "voice:<id>").
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import uuid
from pathlib import Path


def overlay():
    spec = importlib.util.spec_from_file_location("da_overlay", Path(__file__).with_name("overlay.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


OV = overlay()
PROMPT = """You turn a spoken annotation note into a structured annotation.
Item context (JSON): {context}
Annotation structure and allowed values (JSON): {schema}
Rules: record only what the annotator said or clearly implied; use null for anything not said; use only allowed values;
resolve references such as "the third word" using the context. Reply with ONE JSON object:
{{"transcript": "<verbatim words spoken>", "annotation": {{...}}, "confidence": "high|medium|low"}}"""


def to_mp3(src: Path) -> Path:
    out = Path(tempfile.mkdtemp()) / (src.stem + ".mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", "16000", str(out)], check=True)
    return out


def post_json(url: str, body: dict, token: str) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def transcribe(mp3: Path, endpoint: str, model: str, token: str) -> str:
    b = uuid.uuid4().hex
    parts = [f'--{b}\r\nContent-Disposition: form-data; name="model"\r\n\r\n{model}\r\n'.encode(),
             f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{mp3.name}"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode(),
             mp3.read_bytes(), f"\r\n--{b}--\r\n".encode()]
    req = urllib.request.Request(endpoint.rstrip("/") + "/v1/audio/transcriptions", data=b"".join(parts), method="POST",
                                 headers={"Authorization": f"Bearer {token}" if token else "", "Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read()).get("text", "")


def parse(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--notes", required=True); ap.add_argument("--schema", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--audio-dir"); ap.add_argument("--model"); ap.add_argument("--limit", type=int)
    ap.add_argument("--apply", action="store_true", help="write rows (default: dry run)")
    a = ap.parse_args(argv)

    schema = json.loads(Path(a.schema).read_text())
    notes = [json.loads(l) for l in Path(a.notes).read_text().splitlines() if l.strip()]
    done = set()
    if Path(a.out).exists():
        done = {json.loads(l).get("note_id") for l in Path(a.out).read_text().splitlines() if l.strip()}
    audio_dir = Path(a.audio_dir) if a.audio_dir else Path(a.notes).parent
    model = a.model or OV.get("SPOKEN_ANNOTATION_MODEL")
    asr = OV.get("ASR_ENDPOINT_URL")
    or_key = os.environ.get(OV.get("OPENROUTER_TOKEN_ENV", "OPENROUTER_API_KEY"), "")
    asr_key = os.environ.get(OV.get("ASR_TOKEN_ENV", "ASR_TOKEN"), "")
    if not model:
        sys.exit("no model: pass --model or set SPOKEN_ANNOTATION_MODEL in the overlay")
    if not or_key:
        sys.exit("OpenRouter token variable is empty (OPENROUTER_TOKEN_ENV names it)")
    rows = []
    for n in [n for n in notes if n["id"] not in done][: a.limit]:
        src = audio_dir / n["audio"]
        mp3 = to_mp3(src)
        prompt = PROMPT.format(context=json.dumps(n.get("context", {}), ensure_ascii=False), schema=json.dumps(schema, ensure_ascii=False))
        content = [{"type": "text", "text": prompt}]
        if asr:
            content.append({"type": "text", "text": "Transcript: " + transcribe(mp3, asr, OV.get("ASR_MODEL", "whisper-1"), asr_key)})
        else:
            content.append({"type": "input_audio", "input_audio": {"data": base64.b64encode(mp3.read_bytes()).decode(), "format": "mp3"}})
        r = post_json("https://openrouter.ai/api/v1/chat/completions",
                      {"model": model, "temperature": 0, "messages": [{"role": "user", "content": content}],
                       "response_format": {"type": "json_object"}}, or_key)
        got = parse(r["choices"][0]["message"]["content"])
        row = {"note_id": n["id"], "item_id": n.get("item_id"), "source": f"voice:{n['id']}", "model": model,
               "route": "asr+text" if asr else "audio-model", **got, "usage": r.get("usage")}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False, indent=2))
    if a.apply and rows:
        with open(a.out, "a") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"appended {len(rows)} rows to {a.out}", file=sys.stderr)
    else:
        print(f"dry run: {len(rows)} notes read, nothing written (use --apply)", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
