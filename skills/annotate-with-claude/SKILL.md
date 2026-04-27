---
name: annotate-with-claude
description: Annotate a small dataset directly inside the Claude Code session — Claude reads each record, applies the locked schema, and writes structured annotations to disk. For datasets where standing up Label Studio or a Gemini batch job would be overkill (typically tens to low hundreds of records). Use when the user says "annotate this dataset", "label these records with Claude", "do the annotations yourself", or "small-scale annotation".
---

# Annotate With Claude (Interactive, In-Session)

For small annotation jobs where the right tool is just Claude, a schema, and a JSONL file. No batch infra, no UI, no API key — Claude reads each record in turn, applies the schema, writes the output, and moves on. The user supervises (skim, spot-check, course-correct mid-run).

This skill complements `scaffold-annotation-env` (which sets up Gemini batch inference for larger runs). Choose based on scale and feedback loop:

| Situation | Use |
|---|---|
| ≤ ~200 records, schema may still need refinement, want tight feedback | `annotate-with-claude` (this skill) |
| Hundreds to thousands of records, schema is locked | `scaffold-annotation-env` |
| Mixed: a small calibration set first, then scale | This skill for the calibration set, then scaffold |

## Inputs to gather

1. **Input file** — a JSONL where each line is one record. If the source is CSV/Parquet, ask the orchestrator (`shape-dataset`) to reshape first. Each record must have a stable `id`.
2. **Schema** — `schema.json` produced by the `schema-designer` subagent. If absent, run `schema-designer` first; do not invent a schema mid-run.
3. **Annotation guidelines** — short markdown describing edge cases, decision rules, and "when in doubt" defaults. Usually a sibling of `schema.json`.
4. **Output file** — JSONL of annotations. Default: `<workspace>/annotation/claude-annotations.jsonl`.
5. **Confidence/abstain policy** — should Claude flag uncertain cases for human review rather than guess? Default yes.

## Workflow

### 1. Preflight

- Load `schema.json` and the guidelines into context.
- Read the input file, count records.
- Read the output file if it exists; collect already-annotated `id`s so the run is resumable.
- Show the user: N total, M already done, K remaining. Confirm before starting.

### 2. Calibration pass

For the first 5–10 records, annotate slowly and visibly:

- Show each record in the chat.
- Apply the schema and explain the reasoning in 1–2 sentences.
- Write the annotation to the output file.
- Ask the user to confirm or correct before moving on.

Calibration surfaces schema gaps fast — it's far cheaper to fix the schema after 5 mislabels than after 200. If the user corrects an annotation, also ask whether the schema or guidelines should be updated; if yes, update them and restart calibration on the corrected set.

### 3. Bulk pass

After calibration is approved, switch to bulk mode:

- Annotate records in chunks (default 20 per chunk) without per-record commentary.
- After each chunk, show a concise summary: counts per label, any abstentions, any records that hit unusual cases.
- Write each chunk's annotations to the output file as you go (append-only, never rewrite earlier lines).
- Pause between chunks so the user can interrupt, spot-check, or stop.

### 4. Output format

Each line of the output JSONL:

```json
{"id": "<record id>", "annotations": { ... matches schema ... }, "confidence": "high|medium|low", "rationale": "<one short line, optional>", "abstained": false, "annotator": "claude-<model>", "annotated_at": "<iso8601>"}
```

If `abstained: true`, the `annotations` field may be partial or null and the record is queued for human review.

### 5. Validation and handoff

When the run finishes (or the user stops):

- Validate every line against `schema.json` using the `validate_outputs.py` helper from `scaffold-annotation-env` (or inline jsonschema).
- Report: total annotated, abstentions, validation failures, label distribution.
- Suggest next steps: review abstentions, run `review-annotations` for a sample audit, or move to `hf-setup` to publish.

## Operating principles

- **Schema first, always.** Never start annotating without a locked schema. If the schema needs to change mid-run, stop, update it, and decide whether to re-annotate prior records.
- **Resumable.** The run can be paused and resumed; never re-annotate a record whose `id` is already in the output file unless the user explicitly asks for re-annotation.
- **Abstain rather than guess.** When a record genuinely doesn't fit the schema, set `abstained: true` and explain why. Inflated confidence is worse than honest gaps.
- **Visibility scales inversely with volume.** First 10 records: full reasoning. Bulk: summaries only. End: aggregate report.
- **You are the annotator, but the user is the editor.** Encourage the user to spot-check and correct. Treat their corrections as ground truth and learn from them in-session.
- **Don't fabricate metadata.** If you don't have a confident answer for an optional schema field, leave it null rather than inventing one.
