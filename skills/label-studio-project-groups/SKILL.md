---
name: label-studio-project-groups
description: Set up or change a batch of Label Studio projects that form one logical group (one project per voice, speaker, annotator or split) and keep them identical. Use on "set up a batch of projects", "one project per X", "apply this to all of them", "are they still in sync", "change every project in the group".
---

# Project groups

A group is several projects that are the same job over different data. Rule: **same config, same instructions, same
settings, different tasks.** A change to one is a change to all unless the user says otherwise.

Load settings first: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/overlay.py show` (see `setup`). Commands below use `lsctl` for `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/labelstudio.py`; it needs the token in the variable named by `LABEL_STUDIO_TOKEN_ENV` (inject it with the user's secrets tool; never write it to a file). Writes are dry runs until `--confirm`. Record each group (ids, source of truth, verdict meanings) in the overlay's `label-studio-projects.md`.

## Setting up a group

1. Build and agree **one** config with `label-studio-new-project` on the first member, label a few tasks, fix friction with
   `label-studio-edit-interface`. Only then fan out.
2. Titles `<Group>: <member>` so the group sorts together and `lsctl projects` finds it.
3. If a script feeds the group (data sync, rebuilds), put the config and instructions **in that script**: it is the source
   of truth. Otherwise create the rest with `lsctl create-project <xml> --title "<Group>: <member>" --confirm`, then
   `lsctl group-set <ids> --instructions <file> --confirm`.
4. Media per member under its own folder, one local-files storage per project (`lsctl add-localfiles <pid> <group>/<member>`).
5. Check: `lsctl group-diff <ids>` must say `"consistent": true`.
6. Record the group in the overlay register.

## Changing a group

1. `lsctl group-diff <ids>`: confirm it is consistent first; if not, show the drift and ask which is right.
2. Edit once (`lsctl get-config <first> -o /tmp/ls-group.xml`). Label changes follow `label-studio-edit-labels` for every member.
3. **Change the source of truth first** if there is one, or its next sync reverts the change; update anything downstream
   that reads the verdicts.
4. `lsctl group-set <ids> --xml /tmp/ls-group.xml [--instructions /tmp/instr.txt]`: the dry run validates against each
   project's annotations, and nothing is applied if any fails. Then `--confirm`. Old configs are backed up per project.
5. Confirm `after` is `[]` (no differing fields). Update instructions that mention changed options in the same run.

## Notes

- `group-diff` compares config, `expert_instruction` and the settings in `GROUP_SETTINGS` in `labelstudio.py`. Task counts differ by design.
- Other settings (sampling, overlap): `lsctl patch-project <id> --json ...` per member, then re-run `group-diff`.
