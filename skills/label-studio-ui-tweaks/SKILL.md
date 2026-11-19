---
name: label-studio-ui-tweaks
description: Change how Label Studio looks rather than what it asks - font size, spacing, colours, waveform height, audio player defaults - per project or instance-wide. Use on "the font is too small", "make the waveform bigger", "can we tweak the UI", "is there a setting for X", "colour the buttons".
---

# Label Studio UI tweaks

Load settings first: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/overlay.py show` (see `setup`). Commands below use `lsctl` for `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/labelstudio.py`; it needs the token in the variable named by `LABEL_STUDIO_TOKEN_ENV` (inject it with the user's secrets tool; never write it to a file). Writes are dry runs until `--confirm`. What the screen *asks* (controls, hotkeys, order) is `label-studio-edit-interface`; labels are
`label-studio-edit-labels`. Routes and limits: `references/label-studio/extensions.md`.

## Pick the route (cheapest first)

1. **Per project, in the labeling config** (normal route; no deploy). A `<Style>` block plus a `className` on a `View`;
   rules may target built-in classes inside the labeling area. Bigger text:
   ```xml
   <Style>.big, .big * { font-size: 18px; line-height: 1.5 } .ant-radio-wrapper, .ant-checkbox-wrapper { font-size: 16px }</Style>
   <View className="big"> ... existing config ... </View>
   ```
   `style="..."` works on `View`/`Header` too. Audio player look: `<Audio>` attributes `height` (default 96), `waveheight`
   (32), `defaultzoom` (1-1500), `defaultspeed` (0.5-2), `defaultvolume`, `defaultscale`, `spectrogram="true"`,
   `splitchannels="true"`. Apply with `get-config`, edit, `set-config` (dry run, then `--confirm`). A project in a group:
   apply to the whole group (`label-studio-project-groups`) and to its source-of-truth script. If the user keeps
   preferred defaults in the overlay's `preferences.md`, use those values.
2. **Per person, no change at all:** browser zoom (Ctrl +) scales the app; per-user hotkeys are in Account & Settings.
   Suggest this first when only one person wants it.
3. **Instance-wide** (whole app incl. Data Manager): Community has no setting, env var or plugin hook for custom CSS
   (checked 2026-11-15). Options, all deployment changes made through the user's normal deploy route, never ad hoc:
   - bind-mount a stylesheet and an overridden `label_studio/templates/base.html` that links it (fragile: re-diff against
     each new image's `base.html`);
   - inject a `<style>` with an HTML-rewriting reverse proxy or edge worker (survives image updates; direct LAN access would not get it).

## Steps

1. Ask nothing if the target is clear: do route 1 on that project or group.
2. One change at a time; the user reloads the task and says if it is right; adjust sizes in small steps.
3. Note it in the group's or project's notes so the next config rewrite keeps the `<Style>`.

Confirmed 2026-11-15: `<Style>` renders, and its CSS is page-global (it styled the Submit button outside the labeling
area). Choices as coloured pills: `.lsf-choice_layout_inline:nth-child(n) .lsf-choice__checkbox`, hide `.ant-checkbox`,
checked = `.ant-checkbox-wrapper-checked`; Submit = `button[aria-label="Submit current annotation"]`. Emoji icons via
`::before` keep stored values clean (see the built-in `audio-clip-review` template). Test CSS live first on a throwaway project.

## One-click review

Pre-fill the common verdict as a **prediction** (`POST /api/predictions` `{task, model_version, result}`, or `predictions`
in the import). With `show_collab_predictions` on (default) it is pre-ticked, and Submit saves it as the annotation
(verified 2026-11-15).
