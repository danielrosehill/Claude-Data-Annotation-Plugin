---
name: label-studio-edit-interface
description: Fix a hard-to-use Label Studio annotation screen - layout, hotkeys, audio controls, pre-fill, instructions, Data Manager views - without changing what the labels mean. Use on "this is hard to annotate", "too many clicks", "add hotkeys", "make this faster to label", "pre-fill the answers", "change the layout".
---

# Edit the annotation interface

Load settings first: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/overlay.py show` (see `setup`). Commands below use `lsctl` for `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/labelstudio.py`; it needs the token in the variable named by `LABEL_STUDIO_TOKEN_ENV` (inject it with the user's secrets tool; never write it to a file). Writes are dry runs until `--confirm`. Rules: `references/label-studio/config-patterns.md`. Looking at the result and known breakages:
`references/label-studio/ui-review.md` (read it before step 4).

## Steps

1. **Find the project** (`lsctl projects`; ask only if two could match) and pull the config:
   `lsctl get-config <pid> -o /tmp/ls-<pid>.xml`, plus `lsctl project <pid>` for counts and `lsctl sample-tasks <pid>` for data.
2. **Name the friction** in one line and pick the fix:
   - hard to see where to tick: group by scope (span card vs whole-item card), one coloured box per field family, default stated in the heading
   - too many clicks: hotkeys on every Choice/Label, `showInline="true"`, `required` on the verdict, Ctrl+Enter submits
   - audio: `hotkey="space"`, `speed="true"`, `zoom="true"`; split long clips (a data change, re-import)
   - typing from scratch: pre-fill via predictions (re-import, or `POST /api/predictions`)
   - can't compare: side-by-side `View`s, a precomputed HTML diff in `HyperText`
   - cluttered: drop unused fields from the view (keep them in data), `Header`s, collapse notes
   - wrong order or items first: Data Manager tab with filter and ordering (`/api/dm/views/`); project `sampling`
   - unclear rules: `expert_instruction` + `show_instruction: true`
3. **Edit** `/tmp/ls-<pid>.xml`. Keep every control `name` and label value unless the change is about labels (then `label-studio-edit-labels`). Defaults from the overlay's `preferences.md` apply.
4. **Risky change** (conditional or nested views, new control types): try it in a throwaway project first
   (`ui-review.md`). Server validation does not catch an editor that hangs.
5. **Apply:** `lsctl set-config <pid> /tmp/ls-<pid>.xml` (dry run: local and server validation against existing annotations),
   then `--confirm`. The old config is saved under `<data folder>/config-history/<pid>/<timestamp>.xml`; mention the path.
6. **Look at it yourself** in an automation browser (not the annotator's own): open a task, select a region, screenshot.
   A spinner that never resolves means roll back at once.
7. **Tell the user to reload the task** and try it. One friction per round, small steps.

## Notes

- A project generated or synced by a script: change the generator too, or the next sync reverts the edit.
- A project in a group of identical projects: `label-studio-project-groups`. Look only (fonts, sizes): `label-studio-ui-tweaks`.
- Rollback: `lsctl set-config <pid> <backup.xml> --confirm`.

## Data storage

Reads the overlay; writes config backups to `<data folder>/config-history/`.
