---
name: label-studio-import-hf-space
description: Rebuild a one-off Hugging Face annotation Space as an equivalent Label Studio project that reads the same dataset and writes labels back in the same format. Use on "move this Space to Label Studio", "replace the annotation Space", "import my Space", "rebuild this review UI in Label Studio".
---

# Import an HF annotation Space into Label Studio

Turn a one-off Space into a Label Studio project that does the same job, reads the same dataset, and writes labels back in
the **same format** the Space wrote, so nothing downstream changes. Load settings first: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/overlay.py show` (see `setup`). Commands below use `lsctl` for `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/labelstudio.py`; it needs the token in the variable named by `LABEL_STUDIO_TOKEN_ENV` (inject it with the user's secrets tool; never write it to a file). Writes are dry runs until `--confirm`.

## Inputs

A Space id (`owner/name`) or URL.

## Steps

1. **Read the Space source** (`hf download <space> --repo-type space --include "*.py" "*.md" "*.json" "*.html" --local-dir /tmp/space-<name>`;
   read it, don't run it). Note its fields, label set, data source, queue logic and the exact write-back format
   (`reviews/<id>.json` and so on).
2. **Map the UI honestly.** List what the Space did that Label Studio can't (adaptive sampling, blind reveal, copy-to-clipboard,
   live diffs) and the replacement for each (precomputed order, hidden data fields, HyperText diffs). Tell the user the gaps before building.
3. **Build** with `label-studio-new-project` steps 3-9: config, validate, approval, create, media, 10-20 task pilot.
   Items already labelled in the dataset: import as predictions (`model_version: "hf-import"`) or skip them; say which.
4. **Export script:** write `ls_export.py` in the dataset's project repository, mapping the Label Studio export to the Space's
   write-back format (`references/label-studio/hf-round-trip.md`, "Out"). Run it once on the pilot and diff a written record
   against an old one from the Space.
5. **Retire the Space only on the user's word.** Until then it stays up; note in its README that annotation moved. Pause
   (don't delete) once they confirm.
6. **Record** the move in the overlay's `label-studio-projects.md` (Space, project id, export script, status: created, in progress, done).

## Notes

- Private media can't be fetched by the browser from Label Studio: stage it (local-files).
- One Space may become several projects (one per task kind).
