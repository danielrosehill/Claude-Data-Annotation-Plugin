---
name: design-schema
description: Design an annotation schema and guidelines for a labelling task - label sets, single or multi label, span or whole-item, reason taxonomy, edge cases - and render it for the chosen backend (Label Studio XML, Hugging Face Space form, or a model prompt). Use on "design the labels", "what should the annotation schema be", "how should we annotate this", "define the taxonomy", "annotation guidelines".
---

# Design an annotation schema

Load settings first (`setup`, load step): `preferences.md` and `schemas/` in the overlay may hold the user's conventions
and earlier schemas to start from.

## Steps

1. **Pin the purpose.** What will the labels be used for (training set, gold eval set, review queue, error analysis)?
   That decides granularity, how many annotators, and whether disagreement matters. Look at 10-20 real records yourself first.
2. **Delegate the draft** to the `schema-designer` agent with the purpose and the sample. It returns `schema.json`,
   `guidelines.md` and open questions. Iterate with the user until it is locked; do not invent a schema mid-run.
3. **Check the shape against the work.** Per item or per span? Single or multi label? Is "unsure / skip" a label or just
   a skip? Are free-text notes optional? Which verdict is the common case (pre-fill it, so one key confirms)? Do reasons
   need a preset taxonomy so corrections can teach something?
4. **Name things once.** Field and control names are permanent keys in every exported annotation. Choose semantic
   names (`verdict`, `issues`, `note`) and stable label values; display text can differ (`alias`, `html`).
5. **Render for the backend:**
   - Label Studio: XML via `label-studio-new-project` (`references/label-studio/config-patterns.md`).
   - Hugging Face Space: the form/panes in `hf-annotation-space` step 2.
   - Model annotation: the schema plus guidelines become the prompt and JSON schema in `annotate-in-session` or
     `scaffold-annotation-env`.
   - Voice: the same schema is the structure a spoken note is mapped onto (`spoken-annotations`).
6. **Pilot on 10-20 items** with a real annotator; edit the schema from what they trip on, before scaling.
7. **Save it.** Project repo: `schema.json` + `guidelines.md`. If it is reusable, offer to copy it to the overlay's
   `schemas/<name>.json`.

## Data storage

Reads and writes `schemas/` in the overlay (optional). Nothing else.
