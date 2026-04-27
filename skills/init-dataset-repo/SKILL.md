---
name: init-dataset-repo
description: Initialize a local git repository for a dataset, with the conventional Hugging Face layout, LFS configuration, license, and a stub dataset card. Use when the user wants to start a new dataset repo, or as a step inside `hf-setup`.
---

# Init Dataset Repo

Creates a clean local git repository structured for Hugging Face hosting. Does not push anywhere — `hf-setup` handles remote creation and push.

## Inputs

- **Dataset name** (kebab-case for the directory and HF repo name).
- **Path** for the repo. Default: `<workspace>/dataset-repo/` if a `shape-dataset` workspace exists, otherwise ask.
- **License** (defaults to `mit` if the user hasn't decided; flag this in the card as a TODO).

## Layout produced

```
<dataset-name>/
├── .gitattributes          # LFS rules
├── .gitignore              # excludes scratch/, .env, __pycache__/
├── LICENSE                 # full license text
├── README.md               # dataset card stub
└── data/                   # empty; prepared splits go here later
```

## .gitattributes contents

```
*.parquet filter=lfs diff=lfs merge=lfs -text
*.arrow   filter=lfs diff=lfs merge=lfs -text
*.bin     filter=lfs diff=lfs merge=lfs -text
*.h5      filter=lfs diff=lfs merge=lfs -text
*.zip     filter=lfs diff=lfs merge=lfs -text
*.tar.gz  filter=lfs diff=lfs merge=lfs -text
*.jsonl   filter=lfs diff=lfs merge=lfs -text
*.csv     filter=lfs diff=lfs merge=lfs -text
*.png     filter=lfs diff=lfs merge=lfs -text
*.jpg     filter=lfs diff=lfs merge=lfs -text
*.wav     filter=lfs diff=lfs merge=lfs -text
*.mp3     filter=lfs diff=lfs merge=lfs -text
```

If certain formats are known to be small in this dataset, the user can prune later — better to over-include LFS rules at init time.

## README.md stub

Minimal HF dataset card with YAML frontmatter and section headers. Every value is `<!-- TODO -->` until prep produces real metadata. The full population happens in `hf-setup`.

## Steps

1. `mkdir -p <path>/data`
2. Write `.gitattributes`, `.gitignore`, `LICENSE`, `README.md`.
3. `git init` and `git lfs install` inside the repo.
4. Initial commit: `git add -A && git commit -m "Initialize dataset repo skeleton"`.
5. Report the path back to the user.

Do not add any HF remote here. `hf-setup` does that after asking public/private.
