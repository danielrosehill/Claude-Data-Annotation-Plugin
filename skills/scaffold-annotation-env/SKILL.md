---
name: scaffold-annotation-env
description: Create a self-contained annotation workspace for a prepared dataset, including a locked annotation schema and ready-to-run boilerplate for batch inference via the Gemini API. Use when the user says "set up annotation", "create annotation environment", "scaffold annotation", or after `shape-dataset` has produced a clean reshaped dataset.
---

# Scaffold Annotation Environment

Produces a workspace where annotation runs can be executed, reviewed, and iterated. The annotation engine is **Gemini batch inference** (cost/throughput driven choice), with Python boilerplate using the official `google-genai` SDK.

## Prerequisites

- A prepared dataset with one record per annotation task and a stable `id` field (typically the output of `shape-dataset`).
- An annotation schema. If one isn't already locked, invoke the `schema-designer` subagent to produce `schema.json` before scaffolding.
- A Gemini API key. Check for `GEMINI_API_KEY` in env. If missing, tell the user where to set it; don't proceed silently.

## What gets scaffolded

Inside the user's annotation workspace (default: `<dataset-workspace>/annotation/`):

```
annotation/
├── README.md              # how to run, edit prompts, review outputs
├── schema.json            # the locked annotation schema (copied from prep)
├── prompts/
│   └── annotator.md       # system + user prompt templates referencing schema.json
├── input/
│   └── tasks.jsonl        # one task per line, {id, ...fields}
├── output/                # batch results written here
├── reviewed/              # post-review outputs
├── scripts/
│   ├── run_batch.py       # Gemini batch inference runner
│   ├── poll_batch.py      # poll job status, download results
│   └── validate_outputs.py# schema-validate every annotation
├── .env.example           # GEMINI_API_KEY=...
├── pyproject.toml         # uv-managed deps: google-genai, pydantic, jsonschema
└── .gitignore             # output/, reviewed/, .env
```

## Boilerplate to write

### `scripts/run_batch.py`

A runnable script that:

1. Loads `schema.json` and `prompts/annotator.md`.
2. Reads `input/tasks.jsonl`.
3. Builds a JSONL batch request file in Gemini's batch format — one request per task, with the system prompt, the rendered user prompt (task fields substituted), and a JSON-mode / responseSchema config so output conforms to the schema.
4. Submits the batch via `client.batches.create(...)` using the `google-genai` SDK.
5. Writes the returned batch job ID to `output/batch-<timestamp>.json`.

Use Gemini's structured-output / response-schema feature to constrain outputs to the annotation schema — don't rely on prompt-only JSON contracts.

Keep the script readable. The user will tweak prompts and re-run; clarity beats cleverness.

### `scripts/poll_batch.py`

Polls the most recent batch job, downloads results when complete, and writes per-task outputs to `output/<id>.json`. Reports progress on each poll.

### `scripts/validate_outputs.py`

Walks `output/`, validates each JSON against `schema.json` using `jsonschema`, and reports failures. This catches cases where the model returned malformed output despite the response schema.

### `prompts/annotator.md`

Two sections — system prompt and user prompt template. The system prompt summarizes the task, the label set from `schema.json`, and the guidelines (including any edge cases captured by `schema-designer`). The user prompt is a template referencing the task fields.

### `README.md`

Tells the user how to: install deps (`uv sync`), set the API key, run a small smoke batch (e.g. 5 tasks) before the full run, poll, validate, and hand off to `review-annotations` (the subagent) for human/LLM-in-the-loop review.

## Operating principles

- **Smoke before scale.** Always make it easy to run on a small slice first. Mass annotation runs are expensive and a bad prompt should be caught at 10 tasks, not 10,000.
- **Schema is law.** Use Gemini's response schema feature, validate after, and surface any drift.
- **Idempotent.** Re-running the script on the same input shouldn't duplicate work — skip tasks whose `id` already has an output.
- **Don't bake the API key into anything.** `.env` only, `.env.example` checked in, real `.env` ignored.
