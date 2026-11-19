# Data-Annotation-Plugin

Public Claude Code plugin `data-annotation` (v2.0.0): schema design, annotation UIs (Label Studio, Hugging Face Spaces),
annotation jobs (human, model, voice), pulling results back.

- **Public and generic.** No personal names, hostnames, private domains, tokens or project names in anything committed.
  Say "the user". Particulars go in the overlay (README, "Overlay"): `scripts/overlay.py` resolves it; skills read
  `profile.env`, `preferences.md`, `<skill>.md` first. Secrets: the overlay holds only variable NAMES.
- Skill names: no "claude" or "anthropic"; one-line descriptions with trigger phrases; under 500 lines per SKILL.md.
- Label Studio backend: `scripts/labelstudio.py` + `references/label-studio/`. Built-in templates in `templates/label-studio/`
  must be tested and contain no real data. Writes are dry runs until `--confirm`.
- Python via `uv` only.
- Before committing: grep the tree for the user's private terms (instance hostnames, private domains, LAN addresses, project and organisation names): nothing may match; the author's handle appears only in repository URLs.
- Bump `.claude-plugin/plugin.json` version with each change; add a History line to the README. Do not edit marketplace manifests here.
- Generic Label Studio fixes belong here, not in a private companion plugin.
