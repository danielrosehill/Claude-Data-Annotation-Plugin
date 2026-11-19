---
name: new-annotation-job
description: Set up one individual annotation job end to end - pick who annotates (human, model, voice), choose a backend (Label Studio, Hugging Face Space, in-session, batch), settle schema, pilot, scale, pull results back. Use on "I need to label this", "set up an annotation job", "annotate this dataset", "get these reviewed", "which annotation tool should I use".
---

# New annotation job

The router. Load settings first (`setup`, load step). Then decide, propose, and hand off.

## 1. Settle the job in one message

Ask only what cannot be read from the data: the purpose of the labels (train, eval, review), the data location and size,
the annotator (the user, several people, a model, a model first and a human check), and a deadline if any. Read a
few real rows before asking anything.

## 2. Pick the route

| Situation | Route |
|---|---|
| Data is raw, messy, mixed formats or has PII | `shape-dataset` first |
| No schema yet | `design-schema` |
| Tens to ~200 items, a model labels, schema may still move | `annotate-in-session` |
| Thousands of items, schema locked, a model labels | `scaffold-annotation-env` (batch API) |
| Humans label; media, spans, audio waveforms, several annotators, hotkeys; a Label Studio instance exists in the overlay | `label-studio-new-project` (check `label-studio-templates` first) |
| Humans review or fix model output; one reviewer; any browser; no server to run | `hf-annotation-space` |
| Blind grading of outputs, A/B, rating | `hf-annotation-space` (blind grading section) |
| Judging audio, or typing is the slow part | add `spoken-annotations` on top of either UI |
| An old one-off Space should become a Label Studio project | `label-studio-import-hf-space` |

Say which route and why in two lines. A model pass followed by human review of the uncertain items is often the best
mix: model annotates, `hf-annotation-space` or Label Studio shows the model's answer as a pre-fill (a prediction).

## 3. Run it small first

Pilot 10-20 items, look at them yourself, show the user a link or a sample, adjust, then scale. Paid or bulk model runs
need the user's go-ahead on model, route and cost estimate.

## 4. Close the loop

`pull-annotations` brings results back; `review-annotations` (agent) audits label distribution and agreement; `hf-setup`
or `label-studio-push-dataset` publishes. Record the job where the user keeps their register (overlay
`label-studio-projects.md`, or the project README) in the same change.
