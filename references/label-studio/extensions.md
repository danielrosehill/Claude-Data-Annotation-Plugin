# Extending Label Studio (Community edition)

Researched 2026-11-15 against docs and repos; "docs" = stated in the source, not yet tried.

## Extension points

| Route | Community? | Notes | Source |
|---|---|---|---|
| Plugins (custom JS per project) | **No**, Enterprise only, "enabled upon request" | Apache-2.0 examples in `HumanSignal/label-studio-plugins` (`plugin.js` + `view.xml`); readable for ideas, won't run here | docs.humansignal.com/plugins/faq |
| Custom tags / frontend changes | Only by forking | The editor (formerly LSF) lives in `web/libs/editor/` of the main repo since 1.11; needs our own image build | labelstud.io/guide/frontend_reference |
| `<Style>` in a labeling config | Yes (docs) | CSS per project, can target built-in classes (e.g. `.ant-radio-wrapper`) | labelstud.io/tags/style |
| ML backend | Yes (open source SDK) | `HumanSignal/label-studio-ml-backend`: `predict()` for pre-labels, optional `fit()`; Settings > Model | labelstud.io/guide/ml_create |
| Webhooks | Yes (docs) | Task/annotation/project created/updated/deleted; project-level events need `LABEL_STUDIO_ALLOW_ORGANIZATION_WEBHOOKS=true` | labelstud.io/guide/webhooks |
| HTML/JS inside `HyperText` | No | Scripts are sanitised (PR #5232) | community.labelstud.io/t/445 |
| Instance-wide CSS/JS | No setting | Template override (`/label-studio/label_studio/templates/base.html`, confirmed present in the container 2026-11-15) or a reverse-proxy HTML rewrite (for example an edge worker); see skill `label-studio-ui-tweaks` | probed |

Community lists: `HumanSignal/awesome-label-studio-configs`, `HumanSignal/awesome-label-studio-tutorials` (from
search snippets). No plugin marketplace exists.

## `<Audio>` attributes (labelstud.io/tags/audio)

`hotkey` (play/pause), `defaultspeed` 1 (0.5-2), `defaultzoom` 1 (1-1500), `defaultvolume` 1, `defaultscale` 1
(waveform y-scale), `height` 96 (player), `waveheight` 32 (min per channel in split mode), `spectrogram` false,
`splitchannels` false, `decoder` webaudio|ffmpeg|none (none = no waveform, faster for big files),
`player` html5|webaudio, `sync` (link to another object). Review configs commonly also use `zoom="true" speed="true"`
(older toggle attributes; still accepted by validation). Region looping and per-region hotkeys: not documented.
No third-party audio/waveform improvements found.

Ideas for "better waveform" without plugins: raise `height` and `defaultzoom`, turn on `spectrogram` (stutters and
buzz are often clearer there), or an ML backend that pre-draws suspect regions as predictions.
