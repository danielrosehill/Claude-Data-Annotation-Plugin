# Annotation Space templates

Starting points, not answers. Pick the one whose **reviewer action** is closest to the job,
then adapt it. When a job needs a materially different interaction (a different reviewer
action or data shape), build it, verify it, and add it here as a new folder with a row below.
Each folder holds `app.py`, `README.md` (Space frontmatter) and `requirements.txt`.

| Template | Reviewer action | Suits | Captures | First used |
| --- | --- | --- | --- | --- |
| [`edit-in-place/`](edit-in-place/) | Edits the model or LLM output **directly**, ticks why | Rewrites and transformations where most of the value is in *how* outputs get corrected: pseudonymization, normalisation, translation post-editing | verdict, edited text, `edits` (word-level `{from, to, original}` spans, computed), `reasons` (preset taxonomy), note | first used on a pseudonymization review (adapt REASONS and panes) |
| [`side-by-side-verdict/`](side-by-side-verdict/) | **Judges** each item (accept / reject), with an occasional fix in a separate box | Triage and quality gates over N panes, where edits are rare; config-driven (`CONFIG` block: panes, highlighted spans, from → to table, flag chips, queues) | verdict, optional fixed text, note | generalised from the first review Space |

## Shape worth building when needed

**Constrained edit**: the reviewer may change only one thing (for example line breaks), and the save is refused if anything else differs. Start from `edit-in-place/` and add the validation to the save handler.

## Not built yet: shapes to expect

Classification (one button per label, with optional multi-label), span marking
(`gr.HighlightedText` or click-to-tag), pairwise preference (A / B / tie, order randomised),
and rating scales. Don't pre-build them. Build one when a real job needs it, then add it above.
