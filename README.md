# Data Annotation Plugin

The general-purpose plugin for data labelling and annotation: design the annotation schema, set up the annotation UI, set
up an individual annotation job, run the annotation (human, model or voice), and pull the results back. Works with Label
Studio (any instance you can reach by URL and token), private Hugging Face Spaces, in-session model annotation and batch
model annotation.

Plugin name: `data-annotation` (v2.0.0). Public and generic: everything particular to you lives in a private overlay
folder outside the plugin (see below).

## Skills

### Start here
| Skill | Use |
|---|---|
| `new-annotation-job` | Router: choose who annotates and which backend, then hand off |
| `setup` | Write your overlay: backend URLs, Hugging Face org, default hotkeys and audio settings, ASR endpoint |

### Schema and prep
| Skill | Use |
|---|---|
| `design-schema` | Design the annotation schema and guidelines, render it for the chosen backend |
| `shape-dataset` | Raw data to a prepared dataset: profile, PII, columns, format, splits |
| `ingest-source` | Stage data from GitHub, a path or a URL into a working directory |
| `init-dataset-repo` | Local dataset repo with the Hugging Face layout, LFS rules, licence, card stub |

### UIs and backends
| Skill | Use |
|---|---|
| `hf-annotation-space` | Private Hugging Face Space for review, correction, labelling and blind grading, designed per job from a template library |
| `label-studio-new-project` | Create a Label Studio project from a brief and data: config, instructions, settings, pilot |
| `label-studio-edit-interface` | Make an annotation screen faster: layout, hotkeys, audio, pre-fill, views |
| `label-studio-edit-labels` | Add, rename, merge or remove labels without breaking annotations |
| `label-studio-ui-tweaks` | Fonts, colours, waveform and player look, per project or instance-wide |
| `label-studio-project-groups` | A batch of identical projects (per voice, speaker, split), kept in sync |
| `label-studio-templates` | Use or capture reusable project templates (built-ins plus your own) |
| `label-studio-import-hf-space` | Rebuild a one-off Space as a Label Studio project with the same write-back |
| `label-studio-extensions` | Is there a plugin, attribute or backend for X on Community edition |
| `label-studio-users` | Add annotators, reset passwords, invite links |

### Jobs: annotate
| Skill | Use |
|---|---|
| `annotate-in-session` | The agent annotates tens to low hundreds of records against a locked schema |
| `scaffold-annotation-env` | Workspace for large-scale model annotation via the Gemini batch API |
| `voice-annotation-workspace` | Set up a voice-first annotation workspace for any format: point, talk freely, transcribe, a workspace-local skill converts speech to the schema |
| `spoken-annotations` | Annotate by voice: record per item, transcribe, a model applies it to the structure |

### Results and publish
| Skill | Use |
|---|---|
| `pull-annotations` | Bring annotations back from any backend, join to items, audit |
| `label-studio-push-dataset` | Push a Label Studio project's labels into its Hugging Face dataset and verify |
| `hf-setup` | Create and push a Hugging Face dataset repo with a card |

### Agents
`schema-designer`, `data-profiler`, `pii-scanner`, `column-curator`, `format-normalizer`, `review-annotations`: delegated to by the skills above.

## Scripts and references

- `scripts/labelstudio.py`: stdlib CLI for the Label Studio API (projects, overview, config get/validate/set with backups,
  create, import, export, label usage, local-files storage, group diff/set, templates). Dry run unless `--confirm`.
- `scripts/overlay.py`: resolves and reads the overlay.
- `scripts/apply_voice_notes.py`: spoken notes to structured annotations.
- `references/label-studio/`: API map, config patterns, extension points, screen review, Hugging Face round trip.
- `templates/`: built-in Label Studio templates; Space templates in `skills/hf-annotation-space/templates/`.

## Overlay (your private settings)

Data folder, first match wins: `$DATA_ANNOTATION_DIR`, `$CLAUDE_USER_DATA/data-annotation`,
`~/.claude-user-data/data-annotation` (if `~/.claude-user-data` exists), `${XDG_DATA_HOME:-~/.local/share}/claude-plugins/data-annotation`.

| File | Holds |
|---|---|
| `profile.env` | `LABEL_STUDIO_URL`, `LABEL_STUDIO_API_URL`, `LABEL_STUDIO_TOKEN_ENV`, `HF_ORG`, `DEFAULT_VISIBILITY`, `ASR_ENDPOINT_URL`, `SPOKEN_ANNOTATION_MODEL`, ... |
| `preferences.md` | default hotkeys, audio player settings, annotators, spoken-note conventions |
| `templates/label-studio/<id>/`, `templates/hf-space/<name>/` | your templates; same name as a built-in wins |
| `schemas/<name>.json` | reusable annotation schemas |
| `<skill-name>.md` | private notes for one skill; wins over defaults |
| `label-studio-projects.md` | your register of projects |

**Secrets are never in the overlay.** It holds the names of environment variables (`LABEL_STUDIO_TOKEN_ENV=MY_LS_TOKEN`);
inject their values with whatever secrets tool you use. Run `setup` to create it.

## Install

```bash
claude plugins marketplace update danielrosehill
claude plugins install data-annotation@danielrosehill
```

Requirements: `uv`; `hf` CLI logged in for Hugging Face skills; `ffmpeg` for spoken annotations; a Gemini key for
`scaffold-annotation-env`.

## History

- 2026-11-19 (2.1.0): new `voice-annotation-workspace` meta skill: voice-first annotation environments for any format (anchors per format, workspace-local conversion skill, pilot rounds), after the `feedback` plugin's framework.
- 2026-11-19: renamed from Claude-Data-Annotation-Plugin; absorbed ai-eval `spoken-annotations` and
  `setup-annotation-space` (now the blind-grading section of `hf-annotation-space`), and the generic Label Studio
  operations from a private instance plugin (new project, interface, labels, UI tweaks, project groups, templates, Space
  import, extensions, users, push to dataset). Added the overlay, `setup`, `design-schema`, `new-annotation-job`,
  `pull-annotations`. `annotate-with-claude` renamed `annotate-in-session`.
- 2026-10: `hf-annotation-space` redesigned around per-job UIs and a template library.

## License

MIT.
