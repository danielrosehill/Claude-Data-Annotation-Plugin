# Labeling-config patterns

Working rules for Label Studio configs. For the full tag reference, read HumanSignal's own authoring guide:
https://github.com/HumanSignal/create-xml-labeling-config-skill, `references/config_guide.md` (no licence on that repo,
so read it, don't copy it in). Check the instance's accepted tags with `labelstudio.py validate` rather than trusting memory.

## Rules

- **Names are stable identifiers.** `name` on a control is the key in every exported annotation and in the HF write-back.
  Pick a semantic name once (`verdict`, `issues`, `note`); renaming it later orphans existing annotations. A rename
  is a migration (see `edit-labels`).
- **`toName` always points at an object tag** (`Text`, `Audio`, `Image`, `HyperText`, `Paragraphs`, `Table`), never at a
  control.
- **Hotkeys.** Single-choice verdicts use `1/2/3...` (or the letters the old Space used, so muscle memory carries
  over); `Audio` gets `hotkey="space"`. No hotkey used twice (`labelstudio.py validate` warns).
- **Required verdicts.** The main decision gets `required="true"`; notes never do.
- **Skip is not a label.** Label Studio has a skip button (project setting `show_skip_button`); a skipped task is a
  cancelled annotation (`was_cancelled`). Add an explicit Choice only when "skip" must mean something downstream
  (e.g. `exclude_private` on camera data).
- **Conditional fields.** `visibleWhen="choice-selected" whenTagName="<control>" whenChoiceValue="<value>"` on the
  dependent control (e.g. issues only when rating is bad). It can't depend on task data; split projects for that.
- **Pre-fill with predictions, not data.** A draft the annotator corrects (ASR text, model labels, detector regions)
  goes in as a prediction (`predictions: [{model_version, score, result: [...]}]`). Set the project to show
  predictions (`show_collab_predictions: true`, the default). Ordering "least certain first" = sort by prediction score
  in the Data Manager.
- **Hidden fields stay in task data.** Model names, routes, blinding keys: keep them in `data` but don't reference them
  in the config. The annotator can't see them; the export keeps them.
- **Diffs are precomputed HTML.** Label Studio can't diff two fields. Build `<ins>/<del>` HTML at import time and show it
  with `<HyperText>`.
- **Long audio:** split before import (more than about 10 minutes gets sluggish). Use `<Audio zoom="true" speed="true">`
  for review work.
- **Layout:** `<View style="display:flex;gap:1em">` with two child Views for side-by-side; `<Header>` for section
  titles; `style=` only on View/Header.

## Snippets

Verdict row:
```xml
<Choices name="verdict" toName="audio" choice="single" required="true" showInline="true">
  <Choice value="keep" hotkey="1"/><Choice value="cut" hotkey="2"/><Choice value="drop" hotkey="3"/>
</Choices>
```

Editable transcript pre-filled from a prediction:
```xml
<TextArea name="target" toName="audio" editable="true" rows="6" maxSubmissions="1" transcription="true"/>
```
Prediction result: `{"from_name":"target","to_name":"audio","type":"textarea","value":{"text":["draft here"]}}`.

Audio region labels with detector suggestions:
```xml
<Audio name="audio" value="$audio" zoom="true" hotkey="space"/>
<Labels name="seg" toName="audio"><Label value="Cry" background="#16a34a"/></Labels>
```
Prediction region: `{"from_name":"seg","to_name":"audio","type":"labels","value":{"start":3.2,"end":7.9,"labels":["Cry"]},"score":0.81}`.

Per-region comment: `<TextArea name="comment" toName="text" perRegion="true" rows="2"/>`.
