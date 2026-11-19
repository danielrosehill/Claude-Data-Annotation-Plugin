# Hugging Face round trip (Label Studio)

Many jobs start and end in a private Hugging Face dataset. Label Studio Community has no Hugging Face storage
connector, so the round trip is scripted. Settings come from the overlay (`HF_ORG`, `LABEL_STUDIO_*`).

## In: dataset to tasks

1. Read the pool (`pool.jsonl`, `data/*.jsonl`, ...). Small text pools can be read locally
   (`hf download <repo> <file> --repo-type dataset`). A private dataset needs the token on every read: the anonymous
   default 404s, which looks like a missing file.
2. Map each row to `{"data": {...}, "predictions": [...]}`. Keep the dataset's own `id` in `data.id`: it is the join key on
   the way back. Keep every field the write-back needs, displayed or not.
3. Media (audio, images): download it onto the Label Studio host under its local-files root
   (`LABEL_STUDIO_FILES_ROOT`, default `/label-studio/files/<slug>/`), add a local-files storage
   (`labelstudio.py add-localfiles <pid> <slug> --confirm`), and set the task field to
   `/data/local-files/?d=<slug>/<relative path>`. Public URLs can be used as they are. A browser cannot fetch private
   Hugging Face media from inside the labelling screen, so private media is staged.
4. Dry-run, then import: `labelstudio.py import <pid> tasks.json` prints counts and keys; then add `--confirm`.
5. Items that already have annotations in the dataset: import them as predictions with `model_version: "hf-import"`, or
   leave them out. Decide per project and say which in the project description.

## Out: annotations to dataset

1. `labelstudio.py export <pid> -o export.json` (JSON export: every task with `annotations[]`, `completed_by` = user id).
2. Map user ids to annotator names (`GET /api/users`).
3. Write the dataset's **existing** write-back format so downstream training scripts don't change. If there is none yet,
   write one row per task: `id`, the verdict fields, annotator, `updated_at`, and the raw result under `raw`.
4. Commit with `huggingface_hub` (`HfApi.upload_folder` or `create_commit`), one commit per sync, message
   `label-studio export <project> <ISO time>`.
5. Verify the thing, not the exit code: re-download the target with `force_download=True` and compare row counts.

## Keeping it running

A one-off import/export is a script in the project's own repository. When it should run on a timer, make it a sidecar
next to Label Studio (a container running the same script hourly, with the API token and a Hugging Face token
injected), mirroring: dataset to tasks, tasks to predictions, annotations back to the dataset. Only changed projects
should commit. An on-demand variant is the same script run once. Record the sidecar wherever the deployment is
documented, and never run it ad hoc against production data.
