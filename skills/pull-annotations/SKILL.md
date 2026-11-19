---
name: pull-annotations
description: Bring finished annotations back from wherever they were made - a Hugging Face annotation Space, Label Studio, a model batch run, spoken notes - into one JSONL joined to the source items, with a quality check. Use on "pull the reviews", "get the annotations back", "export my labels", "merge the annotations into the dataset", "how is annotation going".
---

# Pull annotations back

Load settings first (`setup`, load step).

## Steps

1. **Identify the source** from the job: a Space's dataset (`reviews/<id>.json`), a Label Studio project id, a model batch
   output folder, a `voice-annotations.jsonl`.
2. **Pull**
   - Hugging Face Space: `uv run ${CLAUDE_PLUGIN_ROOT}/skills/hf-annotation-space/scripts/pull_reviews.py <owner>/<dataset> data/reviews.jsonl`
     (token in the variable named by `HF_TOKEN_ENV`).
   - Label Studio: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/labelstudio.py export <pid> -o export.json`, then flatten each task's
     `annotations[].result` to the schema's fields; map `completed_by` ids to annotator names (`GET /api/users`). Latest
     annotation per annotator wins; cancelled (skipped) annotations are not labels.
   - Model batch: the run's output JSONL (see `scaffold-annotation-env`); in-session: `annotate-in-session` output file.
   - Spoken: `spoken-annotations` output; hand-made annotations win over voice-derived ones.
3. **Join to the items** on the stable `id`. Report: items total, annotated, skipped, with conflicts (two annotators disagree),
   and unknown ids. Keep the raw files; write the merged JSONL beside them.
4. **Audit** with the `review-annotations` agent: schema validation, label distribution, spot-checks, agreement
   (kappa or percent agreement) when there is more than one annotator.
5. **Hand off:** blind grading results are un-blinded only now, with the key kept locally (`hf-annotation-space`, blind
   grading). Publish with `hf-setup`, or `label-studio-push-dataset` for a Label Studio project's own dataset.

Verify the thing: count the rows you pulled against what the backend reports, and read two records end to end.
