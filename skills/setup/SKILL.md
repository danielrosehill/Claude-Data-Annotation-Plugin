---
name: setup
description: Set up or refresh the user's data-annotation overlay (Label Studio URL, Hugging Face org, default hotkeys and audio settings, ASR endpoint for spoken annotation, own templates). Use on "set up data annotation", "configure annotation backends", "my Label Studio is at ...", "change my annotation defaults", or when another data-annotation skill finds no overlay.
---

# Set up the data-annotation overlay

The plugin is generic. Everything particular to the user lives in a private data folder outside the plugin, and every
skill reads it first.

## 1. Find the folder

`uv run ${CLAUDE_PLUGIN_ROOT}/scripts/overlay.py show` prints the resolved folder, `profile.env` values and the files
present. Resolution order: `$DATA_ANNOTATION_DIR`, `$CLAUDE_USER_DATA/data-annotation`,
`~/.claude-user-data/data-annotation` (if `~/.claude-user-data` exists), then
`${XDG_DATA_HOME:-~/.local/share}/claude-plugins/data-annotation`. `overlay.py init` creates it.

## 2. Ask only for what cannot be detected

Propose a value for each and accept corrections. Skip anything the user does not use.

| Key in `profile.env` | Meaning |
|---|---|
| `LABEL_STUDIO_URL` | the URL people open in a browser |
| `LABEL_STUDIO_API_URL` | direct API address when the public URL sits behind an access gateway (default: same as URL) |
| `LABEL_STUDIO_TOKEN_ENV` | the NAME of the environment variable holding the API token (default `LABEL_STUDIO_TOKEN`) |
| `LABEL_STUDIO_FILES_ROOT` | local-files root inside the Label Studio container (default `/label-studio/files`) |
| `HF_ORG` | Hugging Face user or org that owns Spaces and datasets |
| `HF_TOKEN_ENV` | NAME of the variable holding the Hugging Face token (default `HF_TOKEN`) |
| `DEFAULT_VISIBILITY` | `private` (default) or `public` for new datasets and Spaces |
| `ASR_ENDPOINT_URL`, `ASR_MODEL`, `ASR_TOKEN_ENV` | an OpenAI-compatible `/v1/audio/transcriptions` endpoint for spoken annotations (optional) |
| `SPOKEN_ANNOTATION_MODEL` | audio-capable OpenRouter model id used when no ASR endpoint is set |
| `OPENROUTER_TOKEN_ENV` | NAME of the variable holding the OpenRouter key (default `OPENROUTER_API_KEY`) |

Verify what can be verified instead of trusting the answer: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/labelstudio.py whoami`
(needs the token variable in the environment) and `hf auth whoami`.

## 3. Write the files

- `profile.env`: `KEY=value` lines, comments allowed. **Never a token value**, only variable names.
- `preferences.md`: free text the skills read as defaults. Suggested headings: *Labelling UI* (hotkey conventions, verdict
  colours, audio player defaults such as `speed`, `zoom`, `defaultspeed`, `height`), *Annotators* (who labels, how many
  annotations per item), *Spoken annotations* (language, structure of a note), *House rules*.
- `templates/label-studio/<id>/` and `templates/hf-space/<name>/`: the user's own templates. A folder with the same name as a
  built-in wins over it.
- `schemas/<name>.json`: reusable annotation schemas (optional).
- `<skill-name>.md`: private notes for one skill. They win over that skill's defaults.
- `label-studio-projects.md`: the user's own register of projects (id, title, source, write-back). Optional, but update it
  whenever a project is created.

## 4. Report

Show the folder path and the written files (values, not secrets). Say which backends are now usable.

## Load step for every other skill

> Find the data folder (`overlay.py path`). Read `profile.env`, `preferences.md` and `<this-skill-name>.md` if present; they win over defaults. If there is no overlay, use defaults and offer `setup` at the end.
