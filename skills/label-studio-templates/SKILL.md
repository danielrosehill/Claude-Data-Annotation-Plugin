---
name: label-studio-templates
description: Use or capture reusable Label Studio project templates (config, instructions, settings, pre-fill, read-back) - built-ins plus the user's own in the overlay. Use on "start from a template", "save this as a template", "make a template from project X", "which templates are there".
---

# Label Studio templates

Load settings first: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/overlay.py show` (see `setup`). Commands below use `lsctl` for `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/labelstudio.py`; it needs the token in the variable named by `LABEL_STUDIO_TOKEN_ENV` (inject it with the user's secrets tool; never write it to a file). Writes are dry runs until `--confirm`. Built-ins live in `${CLAUDE_PLUGIN_ROOT}/templates/label-studio/<id>/`; the user's own in
`<data folder>/templates/label-studio/<id>/`, and a same-named folder in the overlay wins. Each has `config.xml`,
`template.json`, `instructions.md`, `example-tasks.json` (all four, always).

## Using one

`lsctl templates` lists them. `lsctl create-from-template <id> --title "<Title>" [--description ...]` (dry run, then `--confirm`)
creates the project with the config, `expert_instruction` and `project_settings`. Shape the import like `example-tasks.json`
(including the pre-fill prediction if the template has one). Several projects of one kind: `label-studio-project-groups`.
Adapt per job rather than forcing the fit: `template.json` `variants` lists the usual changes.

## Saving one

Only from a setup that has been **used**: a project with annotations in progress or done (`lsctl projects`, `annotated` > 0).
A config nobody has labelled with is a `draft`; say so.

1. List `templates/label-studio/` in the overlay and the built-ins: update an existing template (or add a variant)
   instead of a near-duplicate.
2. **Pull the setup:** `lsctl get-config <pid> -o <dir>/config.xml`, `lsctl project <pid>`, `GET /api/projects/<pid>` for
   `expert_instruction` and settings, `lsctl sample-tasks <pid> -n 2` for the data fields. If a script generates the project, read it too: pre-fill and read-back logic live there.
3. **Generalise:** id = the kind of job (`audio-clip-review`, `pairwise-ab-audio`), not the project. Keep control names and
   verdict values (read-back scripts key on them). Rewrite `instructions.md` without project specifics.
   `example-tasks.json`: 1-2 made-up tasks with every field, plus the pre-fill prediction. **No real task data, names or private text.**
4. **`template.json`:** `id`, `title`, `summary`, `use_for`, `status` (`in use` or `draft`), `derived_from`, `data_fields`,
   `controls` (verdict meanings, hotkeys), `project_settings`, `one_click`, `look`, `readback`, `variants`. Copy the shape of
   the built-in `audio-clip-review`.
5. **Check it builds:** `lsctl validate <dir>/config.xml`.
6. Save to the **overlay** by default. If it is generic, offer it as a built-in contribution to the plugin repository
   (no personal data) instead.

## Data storage

Reads and writes `templates/label-studio/` in the overlay.
