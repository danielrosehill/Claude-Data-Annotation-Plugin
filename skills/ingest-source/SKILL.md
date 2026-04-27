---
name: ingest-source
description: Stage raw data from a GitHub repo, local path, or remote URL into a working directory so downstream prep skills can operate on it. Use when the user provides a data source and wants it pulled in, or when `shape-dataset` needs to ingest before profiling.
---

# Ingest Source

Unified entry point for getting raw data onto disk in a known location. Does not transform the data — just stages it and reports what was staged.

## Inputs

- A source: GitHub URL (repo or file blob), a local path, or a remote URL (single file or archive).
- Optional: a destination workspace. Default:

```bash
DATA_ROOT="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/data-annotation"
WORKSPACE="$DATA_ROOT/workspaces/<dataset-name>/raw"
```

If the user prefers a path they own (e.g. `~/repos/...` or `~/Documents/`), use that and store the pointer in `$DATA_ROOT/config.json`.

## Behavior by source type

### GitHub repo (`github.com/<owner>/<repo>` or `<owner>/<repo>`)

Clone shallow:

```bash
git clone --depth 1 https://github.com/<owner>/<repo>.git "$WORKSPACE"
```

Then scan the working tree for data files (`.csv`, `.tsv`, `.json`, `.jsonl`, `.parquet`, `.arrow`, `.txt`, `.md`, `.yaml`, `.xml`, `.xlsx`, image/audio dirs). Report a tree of candidates by extension with byte sizes. Do not assume the whole repo is data — README and source code are common.

### GitHub file blob (`github.com/<owner>/<repo>/blob/<ref>/<path>`)

Convert to raw URL and download:

```bash
curl -L https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path> -o "$WORKSPACE/<basename>"
```

### Local path

Copy (don't move) the contents into `$WORKSPACE/`. Preserve directory structure.

### Remote URL — single file

`curl -L -o "$WORKSPACE/<basename>" <url>`. Verify content-length and content-type after download.

### Remote URL — archive (`.zip`, `.tar.gz`, `.tar.bz2`, `.7z`)

Download, then extract into `$WORKSPACE/`. After extraction, delete the archive unless the user wants to keep it.

## Output

Write `$WORKSPACE/_ingest.json` with:

- `source` — original source string
- `source_type` — one of `github-repo`, `github-blob`, `local`, `url-file`, `url-archive`
- `staged_at` — ISO timestamp
- `tree` — list of files with sizes
- `notes` — anything the user should be aware of (binary blobs, unusual extensions, archive layout)

Then briefly summarize for the user: "Staged N files, total X MB, candidates appear to be ..." and hand off to `shape-dataset` (or whatever the user wants next).

## Operating principles

- **Never modify the staged copy.** Downstream stages live elsewhere.
- **Be transparent about size.** Warn before downloading >1 GB.
- **Respect private repos.** If a `git clone` fails, suggest `gh repo clone` (which uses the user's gh auth) instead of asking for credentials.
