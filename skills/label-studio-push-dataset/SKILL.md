---
name: label-studio-push-dataset
description: Push a Label Studio project's annotations into a Hugging Face dataset in that dataset's native format by running the project's export script, or trigger the user's sync. Use on "push the labels to Hugging Face", "sync project X up", "update the dataset with my labels", "publish annotations from Label Studio", "is it synced".
---

# Push a project's annotations to its dataset

Load settings first: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/overlay.py show` (see `setup`). Commands below use `lsctl` for `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/labelstudio.py`; it needs the token in the variable named by `LABEL_STUDIO_TOKEN_ENV` (inject it with the user's secrets tool; never write it to a file). Writes are dry runs until `--confirm`. `references/label-studio/hf-round-trip.md` has the format rules.

## Steps

1. **Which project.** Match the name the user gave to a project id (`lsctl projects`, or the overlay's `label-studio-projects.md`).
2. **Which exporter.** The register names each project's export script and target. If the user runs a timed sync sidecar,
   its on-demand trigger is in the overlay's `label-studio-push-dataset.md`; use it. No exporter: say so, and offer to
   write `ls_export.py` (`label-studio-import-hf-space` step 4) from `lsctl export <pid>`.
3. **Run it** from the project repository after `git pull`. Read `--help` first for the push flag and any dry-run switch.
   Usual form: `<secrets tool> uv run --with huggingface_hub python scripts/<export>.py <args> --push`.
4. **Verify the file on Hugging Face, not the script's exit.** Re-download the target with `force_download=True`, compare
   with the local output (row count, the new rows), and read the latest commit title on the dataset.
5. **Report** in one or two lines: project, dataset and file, row counts by label, the commit. If the push revealed a step
   the script doesn't document, fix the script's docs in the same commit.

## Data storage

Reads the overlay; the script's output goes to the project repository.
