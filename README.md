# Claude Data Annotation Plugin

End-to-end toolkit for turning raw data into an annotated dataset and publishing it to Hugging Face. Covers the full lifecycle: ingest, profile, clean (PII, columns, format), design an annotation schema, annotate (interactively with Claude or via Gemini batch inference), review, and publish.

The plugin is built around a small set of orchestrator skills delegating to specialized subagents — instead of one micro-skill per micro-operation, the orchestrator looks at the data, talks to the user, and figures out which steps are needed.

## Skills

- **`shape-dataset`** — top-level prep workflow. Ingests a source, profiles it, proposes a prep plan (PII, columns, format, splits, schema), executes approved steps. Hands off to annotation or publication.
- **`annotate-with-claude`** — Claude annotates a small dataset interactively in-session against a locked schema. For runs where Label Studio or batch inference would be overkill (typically tens to low hundreds of records).
- **`scaffold-annotation-env`** — generates a workspace for large-scale annotation via the Gemini batch inference API, with Python boilerplate (run, poll, validate).
- **`hf-setup`** — creates a Hugging Face dataset repo (asks public/private), copies the prepared data over, generates the dataset card, pushes via `huggingface-cli`.
- **`ingest-source`** — stages raw data from GitHub, a local path, or a remote URL into a known working directory.
- **`init-dataset-repo`** — initializes a local git repo with the conventional HF dataset layout, LFS rules, license, and card stub.

## Subagents

The orchestrator skills delegate to these — they are not invoked directly by the user.

- **`data-profiler`** — schema inference, stats, encoding, samples; flags concerns.
- **`pii-scanner`** — detects PII (direct and quasi), proposes redaction strategy per column; can apply on approval.
- **`column-curator`** — recommends keep/drop/rename/recast/derive per column for the target task.
- **`schema-designer`** — proposes annotation schema and guidelines from data + task; iterates with the user before locking.
- **`format-normalizer`** — executes format conversions, encoding fixes, JSON flattening, reshape-for-annotation, and splits.
- **`review-annotations`** — audits finished annotations: schema validation, label distribution, sampled spot-checks, agreement analysis.

## Typical workflow

```
ingest-source
   ↓
shape-dataset  ──→  data-profiler, pii-scanner, column-curator, format-normalizer, schema-designer
   ↓
annotate-with-claude   (small)        OR        scaffold-annotation-env   (large)
   ↓                                                ↓
review-annotations                               review-annotations
   ↓                                                ↓
hf-setup                                         hf-setup
```

## Installation

```bash
claude plugins marketplace update danielrosehill
claude plugins install data-annotation@danielrosehill
```

After installing, restart Claude Code.

## Requirements

- `huggingface-cli` (logged in) for `hf-setup`.
- `GEMINI_API_KEY` in the annotation workspace `.env` for `scaffold-annotation-env`.
- Python with `pandas`, `pyarrow`, `presidio-analyzer`, `jsonschema` (skill scripts install via `uv` on first run).

## Data storage

- Plugin-managed working state: `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/data-annotation/`.
- User-owned dataset repos: a path the user picks during onboarding (typically under `~/repos/` or `~/Documents/`); only a pointer is stored under `$CLAUDE_USER_DATA`.

## License

MIT.
