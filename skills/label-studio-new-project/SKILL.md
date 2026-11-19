---
name: label-studio-new-project
description: Create a Label Studio annotation project from a brief and a dataset - config, instructions, settings, pilot import - against any Label Studio URL. Use on "set up a Label Studio project", "new labelling project", "make a project to label X", "annotate this in Label Studio".
---

# New Label Studio project

Load settings first: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/overlay.py show` (see `setup`). Commands below use `lsctl` for `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/labelstudio.py`; it needs the token in the variable named by `LABEL_STUDIO_TOKEN_ENV` (inject it with the user's secrets tool; never write it to a file). Writes are dry runs until `--confirm`. API map: `${CLAUDE_PLUGIN_ROOT}/references/label-studio/api.md`. Config rules:
`references/label-studio/config-patterns.md`. HF in/out: `references/label-studio/hf-round-trip.md`.

## Inputs

The objective (training set, eval, review queue) and the task; the data (links, folder, HF dataset, which fields matter);
who annotates, and whether a model draft should pre-fill. Look at 3-5 real rows yourself before asking anything.

## Steps

1. **Templates first.** `lsctl templates` lists the user's own and the built-in ones; a match gives config, instructions,
   settings and pre-fill (`label-studio-templates`). Rebuilding an old Space: `label-studio-import-hf-space`.
   A schema from `design-schema` becomes the config.
2. **Read the data.** Note the id field, the media fields, anything that should become a prediction.
3. **Draft the config** in `/tmp/ls-<slug>.xml` from the closest template, snippet or existing project
   (`lsctl get-config <pid>`). Control names are permanent keys: choose them now. Apply the user's hotkey and audio
   defaults from `preferences.md`.
4. **Validate:** `lsctl validate /tmp/ls-<slug>.xml` (local checks, plus a throwaway project on the server). Fix until `ok: true`.
5. **Show the user** the config, a sample task and your assumptions (field names, label set, hotkeys) in one message. Wait
   for a yes, or iterate.
6. **Create:** `lsctl create-project /tmp/ls-<slug>.xml --title "<Title>" --description "<objective, source, write-back>" --confirm`.
7. **Settings** (`lsctl patch-project <id> --json '{...}' --confirm`): `expert_instruction` (the labelling guide, HTML),
   `show_instruction`, `show_skip_button`, `maximum_annotations` (2 or more for agreement), `sampling`.
8. **Media:** stage on the Label Studio host and `lsctl add-localfiles <pid> <slug> --confirm` (hf-round-trip step 3).
9. **Pilot:** build 10-20 tasks, `lsctl import <pid> tasks.json` (dry run), then `--confirm`. Look at one task
   (`lsctl sample-tasks <pid>`) and give the user the project link. Import the rest only once they have labelled a few
   and the config holds.
10. **Write-back:** if the labels must land in a dataset, agree the format and where the export script lives. Don't leave it implied.
11. **Record** the project in the overlay's `label-studio-projects.md` (id, title, source, write-back).

## Notes

- `create-project` and `import` change a live instance. Community edition: everyone on the instance sees every project, so
  client data does not belong on a shared one.
- Large media or long audio (over ~10 minutes): split before import.

## Data storage

Reads the overlay (`profile.env`, `preferences.md`, `templates/label-studio/`); appends to `label-studio-projects.md`.
