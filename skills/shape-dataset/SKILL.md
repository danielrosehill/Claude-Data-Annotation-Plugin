---
name: shape-dataset
description: Main entry point for turning raw data into a dataset. Examines a source (GitHub repo, local path, URL), works with the user to define the target task, then plans and executes a prep pipeline — profiling, PII handling, column curation, format normalization, splits, and annotation schema design. Delegates specialized work to subagents. Use when the user says "prep this data", "turn this into a dataset", "get this ready for annotation", or "build a dataset from X".
---

# Prep Dataset (Orchestrator)

This is the top-level workflow for taking raw data and getting it into shape for a dataset — typically one destined for annotation and publication on Hugging Face. It does **not** try to enumerate every possible operation as a separate skill. Instead, it inspects the data, understands the user's goal, and decides which preparatory steps to run, delegating each to a specialized subagent.

## Inputs to gather

1. **Source** — a GitHub repo URL, a local path, or a remote URL. If unclear, invoke the `ingest-source` skill to stage the data first.
2. **Target task** — what is the dataset *for*? (e.g. classification, instruction tuning, NER, RAG eval, preference pairs). This drives every downstream decision.
3. **Sensitivity expectation** — does the data potentially contain PII? Is the published dataset intended to be public?
4. **Working directory** — where prepared artifacts are written. Default: `$CLAUDE_USER_DATA/data-annotation/workspaces/<dataset-name>/` resolved as:

```bash
DATA_ROOT="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/data-annotation"
```

If the user wants the workspace under a path *they* own (e.g. `~/repos/...`), store only the pointer to that path in `$DATA_ROOT/config.json` and write artifacts there.

## Workflow

### 1. Stage the source

If not already on disk, invoke the `ingest-source` skill. End state: a single directory with the raw data files visible.

### 2. Profile

Delegate to the `data-profiler` subagent. Expect back: file inventory, format(s), row/record counts, schema (column names + inferred types), null/dup rates, encoding issues, and a small sample.

### 3. Surface concerns and propose a plan

Based on the profile and the target task, write a short prep plan to the workspace as `prep-plan.md`. Typical line items:

- **PII**: if the profiler flagged free-text columns or obvious identifier columns, queue the `pii-scanner` subagent.
- **Column curation**: if there are columns the target task won't use, queue the `column-curator` subagent.
- **Format issues**: nested JSON to flatten, encoding to fix, format conversion (e.g. CSV → JSONL/Parquet) — queue the `format-normalizer` subagent.
- **Reshaping**: if the target is annotation, the data needs to become one row per annotation task with a stable `id` — queue `format-normalizer` for this too.
- **Splits**: train/val/test if appropriate — queue `format-normalizer`.
- **Annotation schema**: if the goal includes annotation, queue the `schema-designer` subagent after reshape.
- **Other**: deduplication, language detection, length filtering, toxicity screening — call out only if relevant signals appeared in the profile.

Show the plan to the user. **Do not execute steps the user hasn't approved.** Let them strike, reorder, or add items.

### 4. Execute approved steps

Run each approved step by invoking the corresponding subagent with a precise brief: input path, output path, the relevant slice of the profile, and the target task. After each step, re-profile briefly so the next step works on current data.

Persistent intermediate artifacts go in `<workspace>/stages/<NN>-<step>/`. The final cleaned dataset lands in `<workspace>/final/`.

### 5. Hand off

When prep is done, suggest the next skill based on scale and feedback needs:
- **Small annotation (≤ ~200 records, schema may still need tuning)**: `annotate-with-claude` — Claude annotates each record interactively in-session, with the user supervising.
- **Larger annotation (hundreds to thousands, schema locked)**: `scaffold-annotation-env` — sets up Gemini batch inference over the prepared data.
- **For publication**: `hf-setup` — creates the HF dataset repo, copies data over, generates the card.
- **End-to-end**: annotate (either skill), then `hf-setup` once labels are populated.

## Operating principles

- **Diagnose, don't dictate.** Look at the data and the task before recommending operations. Don't run PII redaction on a synthetic benchmark; don't strip columns from an already-clean dataset.
- **Confirm before destructive steps.** Column drops, redaction, and reshaping change the data. Always show the user what will be removed/transformed before doing it.
- **Keep stages.** Never modify the raw input in place. Each step produces a new stage directory so the user can audit or roll back.
- **Single source of truth for the schema.** Once a schema is locked (post-reshape), write it to `<workspace>/schema.json` and refer back to it from every later stage.
