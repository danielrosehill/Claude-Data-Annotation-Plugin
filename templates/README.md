# Built-in templates

- `label-studio/<id>/`: tested Label Studio setups. Each folder has `config.xml`, `template.json`
  (what it is for, data fields, controls and verdict meanings, project settings, pre-fill, read-back),
  `instructions.md` and `example-tasks.json`. Build one with
  `uv run scripts/labelstudio.py create-from-template <id> --title "<title>" --confirm`.
- A file with the same folder name in the user's overlay (`<data folder>/templates/label-studio/<id>/`) wins over the built-in.
- Hugging Face Space templates live in `skills/hf-annotation-space/templates/`; overlay copies go in `<data folder>/templates/hf-space/<name>/`.

| Template | For | Status |
|---|---|---|
| `label-studio/audio-clip-review` | Per-clip audio QA: Fine / Flag / Imperfect, fault regions on the waveform, one-click Fine | tested on Label Studio 1.23 |
