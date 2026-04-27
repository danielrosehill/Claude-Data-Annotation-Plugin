---
name: hf-setup
description: Set up a Hugging Face dataset repository — create the remote repo (asking public/private), copy prepared data over, generate a dataset card, and push. Uses the huggingface-cli, not an MCP. Use when the user says "set up a HF dataset", "publish to Hugging Face", "create the HF dataset repo", or after annotation/prep is complete.
---

# Hugging Face Dataset Setup

End-to-end setup of an HF dataset repository from a prepared local dataset. Encompasses creation, data copy, dataset card, and push.

## Prerequisites

- `huggingface-cli` installed and logged in. Check with `huggingface-cli whoami`. If not logged in, instruct the user to run `huggingface-cli login` (don't try to do it programmatically).
- A prepared local dataset directory — typically `<workspace>/final/` from `shape-dataset`, optionally enriched with annotation outputs from `scaffold-annotation-env`.
- Knowledge of the target task and license (ask if not already in the workspace).

## Inputs to gather

1. **Dataset name on HF** — defaults to the workspace dataset name. Confirm.
2. **Visibility** — public or private. **Always ask.** Don't assume.
3. **License** — common defaults: `mit`, `apache-2.0`, `cc-by-4.0`, `cc-by-sa-4.0`, `cc0-1.0`, or `other`. Ask if unclear.
4. **Owner** — user account or an organization. Default to the logged-in user.

## Workflow

### 1. Create the remote repo

```bash
huggingface-cli repo create <name> --type dataset [--private] [--organization <org>]
```

Use `--private` if the user chose private. Capture the resulting repo URL (`https://huggingface.co/datasets/<owner>/<name>`).

### 2. Initialize a local dataset repo

If the workspace doesn't already have a git repo for the dataset, run `init-dataset-repo` first. Otherwise reuse it.

```bash
cd <dataset-repo>
git lfs install
huggingface-cli lfs-enable-largefiles .
git remote add origin https://huggingface.co/datasets/<owner>/<name>
```

Configure `.gitattributes` for LFS on `*.parquet`, `*.arrow`, `*.json`, `*.jsonl` over a size threshold, and any media files.

### 3. Copy prepared data into the repo

Lay out the dataset on disk in the conventional HF structure:

```
<dataset-repo>/
├── README.md          # the dataset card (next step)
├── data/
│   ├── train.parquet  # or .jsonl
│   ├── validation.parquet
│   └── test.parquet
└── LICENSE
```

If the prepared data is in a different format/layout, convert it. Prefer Parquet for tabular, JSONL for variable-shape records.

### 4. Generate the dataset card

Write `README.md` with the YAML frontmatter HF expects:

```yaml
---
license: <license>
task_categories:
  - <task>
language:
  - en
size_categories:
  - <auto>
pretty_name: <Pretty Name>
tags:
  - <tag>
---
```

Below the frontmatter, generate sections from the workspace artifacts:

- **Dataset Summary** — derived from the target task and prep plan.
- **Supported Tasks** — from the task description.
- **Languages** — detected during prep if applicable.
- **Dataset Structure** — schema from `schema.json`, columns, splits, sizes (read from the actual files).
- **Data Fields** — per-column descriptions.
- **Data Splits** — row counts per split.
- **Source Data** — origin (GitHub repo, etc.) from prep metadata.
- **Annotations** — if applicable: who annotated (Gemini model + version, with date), schema link, review process.
- **Personal and Sensitive Information** — PII handling summary from the `pii-scanner` run, if any.
- **Considerations** — biases, limitations, intended use.
- **Licensing Information**.
- **Citation** — bibtex stub for the user to fill in.

Anything the workspace doesn't have an answer for should be a clearly-marked `<!-- TODO -->` rather than a fabricated detail.

### 5. Push

```bash
git add -A
git commit -m "Initial dataset upload"
git push origin main
```

Report back the dataset URL and remind the user that the card preview may take a minute to render on the Hub.

## Operating principles

- **Always ask public vs private.** Even if the user's tone implied one. Datasets get embarrassing once they leak.
- **Don't fabricate the card.** TODO markers beat invented metadata.
- **LFS before large pushes.** Catching a missed LFS configuration after a 2GB push is painful.
- **Reproducibility.** Save the prep plan and any annotation run metadata into the dataset repo so the published artifact is auditable.
