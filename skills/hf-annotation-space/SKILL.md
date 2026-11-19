---
name: hf-annotation-space
description: Design and stand up a private Hugging Face Space for humans to review, correct, label, blind-grade or browse a dataset. Each job gets a UI designed for its reviewer action (edit in place with reasons, judge accept/reject, constrained edit, …), starting from the closest template in a small library rather than one fixed app. Decisions are saved to the dataset repo with the reviewer's own HF sign-in, so the Space holds no secrets. Use when the user says "make an HF Space to review this data", "annotation Space", "I want to look at / edit the data on HF", "review UI for these pairs", "I want to grade these outputs myself, blind", "set up an annotation space", or when synthetic or model-labelled data needs a human pass before training.
---

# HF annotation Space

Load settings first (`setup`, load step): `HF_ORG` is the owner of the new Space and dataset, `DEFAULT_VISIBILITY` the
visibility (private unless the user says otherwise), `HF_TOKEN_ENV` the name of the token variable. The user's own
templates in `<data folder>/templates/hf-space/<name>/` win over the built-ins here when the name matches.

Builds a **private** Gradio Space over a **private** HF dataset so the user can review data
from any browser. Every decision is committed back to the dataset, and
`scripts/pull_reviews.py` merges the decisions into the project.

**Every annotation job is different.** The interaction is designed per job (step 2). The
templates in `templates/` are worked starting points, indexed by reviewer action in
`templates/README.md`. They are not a default app. Don't copy one without doing step 2.

## Invariants: the same in every Space

| Invariant | Why |
| --- | --- |
| Space **and** dataset private | Review data is unvetted. Make it public later, once it is reviewed. |
| `hf_oauth: true`, scopes `read-repos` + `write-repos`; read and write with the **signed-in user's token**; items loaded after sign-in | No `HF_TOKEN` secret in the Space. Only accounts with write access can save. |
| One file per decision: `reviews/<id>.json` with at least `{id, verdict, reviewer, ts}` | Concurrent reviewers never conflict, re-reviewing overwrites, and the queue is "ids without a file". |
| Verdict colours: accept/save green `#16a34a`, reject red `#dc2626`, fix amber `#d97706`, skip grey `#6b7280` (by `elem_id` in CSS) | Readable at a glance, and the same across Spaces. |
| Keyboard shortcuts, ignored while typing (`gr.Blocks(js=...)`) | Hundreds of items get reviewed fast. |
| Highlights as `rgba()` backgrounds with `color: inherit`; panes on Gradio CSS variables | Works in both light and dark theme. |
| Skip is session state only; an edited text is never lost (whatever button saves it, it is stored) | Skipping must never write a decision, and losing a correction is the worst failure. |
| A Browse tab beside the review flow | "Look at the data" comes up as often as "review it". |

## Steps

1. **Read the data and the goal.** What is one item? What will the decisions be used for
   (a gold test set, training fixes, finding systematic generator errors)? That decides
   what must be captured.
2. **Design the interaction with the user.** Settle these, proposing an answer for each
   rather than asking open questions:
   - **Reviewer action.** Judge? Edit the output directly? A constrained edit (only some
     characters may change)? Pick a label? Mark spans? Choose between A and B?
   - **What's on screen.** Which fields, side by side or stacked, what gets highlighted, and
     what's hidden (drop the from → to table once editing becomes the action).
   - **What a decision records.** Beyond the verdict: edited text, computed diffs, a
     **reason taxonomy** (preset checkboxes plus free text, when the corrections are meant to
     teach something), and any metadata.
   - **Queues.** Which items first: a gold or test pool, then validator-flagged items, then
     the rest.

   Then open `templates/README.md` and pick the template with the closest reviewer action.
   If none is close, build from the invariants. Say in one line which template you started
   from and what changes.
3. **Shape and upload the data (private).**
   `hf repos create <owner>/<name> --repo-type dataset --private --exist-ok`, upload the
   items JSONL (stable string `id` per item) and a short card whose frontmatter has
   `configs: [{config_name: <x>, data_files: <items>.jsonl}]`, so the viewer ignores `reviews/`.
4. **Build the Space** in the project as `space/` (`app.py`, `README.md` frontmatter,
   `requirements.txt` with `huggingface_hub`). The `README.md` needs `short_description` of
   60 chars or fewer, and an emoji that is a single Extended_Pictographic character (`¶` is
   rejected).
5. **Test locally before deploying.** Import the app and call the handlers with stub objects
   that have `.token` / `.username`:
   `DATASET_REPO=… HF_TOKEN=… uv run --with "gradio[oauth]==5.49.1" --with huggingface_hub python -c "import app; …"`.
   Exercise load, browse and one save, read the saved `reviews/<id>.json` back, then **delete
   the test decision** (`HfApi(token).delete_file(...)`) and remove it from the local file.
6. **Deploy (private).** `hf repos create <owner>/<space> --repo-type space --space-sdk gradio --private --exist-ok`,
   then `hf upload <owner>/<space> space . --repo-type space`. Poll
   `GET https://huggingface.co/api/spaces/<owner>/<space>/runtime` until it is `RUNNING`.
   Logs: `.../logs/build` and `.../logs/run` (SSE; `timeout 8 curl -sN`, grep `"data":`).
7. **Verify the page** in a real browser (automation browser or the user's own browser): it renders behind the private
   gate. **Don't click "Sign in with Hugging Face"**: that's an OAuth grant, so it's the
   user's click. The user's first real decisions, arriving through `pull_reviews.py`, are
   what proves sign-in works. Say so until they arrive.
8. **Wire the project.** Run `scripts/pull_reviews.py <owner>/<dataset> data/reviews.jsonl`
   before the project's build or split step. If the job captures reasons, add a small
   report that groups decisions by reason, with example edits, so the learnings drive the
   next generator or validator change. Document the Space, dataset and pull step in the
   project README.
9. **Iterate on feedback.** Reviewers find the UI's problems in the first ten items. Expect
   to redeploy, and when a job ends up with a materially new interaction, **add it to
   `templates/`** with a row in `templates/README.md`.

## Blind grading (rating model outputs without knowing the model)

Use this when the Space grades outputs of several models, prompts or systems: text, image or audio. It adds three things
to the steps above; everything else (invariants, templates, traps) applies unchanged.

1. **Blind the items before upload.** `uv run scripts/blind_items.py rate --responses responses.jsonl --out items.jsonl --key key.json`
   (responses carry `model`, `prompt_id`, `prompt` and the output in `response`, `output`, `text` or `image`). For A/B use
   `pairs` (randomises left and right). **`key.json` stays local**: never in the Space or the dataset, or the rating is not
   blind. Model names, routes and file names that leak them stay off the form. Cost and output size may be shown only
   if value for money is part of the question.
2. **Design the form from the rubric, not a generic scale.** One control per criterion, kept short because people grade
   badly on long forms. Add hard-failure tags from the objective's failure wording, an optional free-text note and an
   optional process note (a criterion the form lacks, or something that couldn't be graded). Images: show JPEG previews, as
   multi-MB PNGs make grading crawl. Audio: a player with speed control, and consider `spoken-annotations`.
3. **Un-blind only after grading.** Pull reviews (`pull-annotations`), then
   `uv run scripts/blind_items.py unblind --reviews reviews.jsonl --key key.json --out ratings.jsonl`. Report per-model
   results, keeping human grades apart from any LLM judge; where both exist, list the disagreements (the most informative
   rows). For preference pairs as training data, `preferences` writes `prompt`, `chosen`, `rejected` records.

Create the private repos before any upload (uploading to a missing id creates it public):
`hf repos create <owner>/<Name>-Ratings --repo-type dataset --private --exist-ok`, and the Space the same way with
`--repo-type space --space-sdk gradio`. Grading is rarely worth a Space for fewer than about 20 outputs: reading them in
a document is quicker. Files fetched with `snapshot_download` need `demo.launch(allowed_paths=[HF_HUB_CACHE])` or every
image and audio item errors; verify that a handler really returns a file.

## Traps (all hit while building the first ones)

- **`gr.OAuthToken` / `gr.OAuthProfile` are injected only into functions whose signature
  type-hints them.** A `lambda` wrapper silently receives `None`. Write real `def`s.
- **A local run needs `gradio[oauth]`** whenever the README sets `hf_oauth: true`; otherwise
  you get `ImportError … itsdangerous`. The Space installs it itself.
- **`gr.LoginButton()` showed a broken logo image on a private Space.** Use `icon=None`.
- **Edit boxes in collapsed accordions don't get found.** The first reviewer reported they
  "couldn't edit" at all. Put the editor where the eye already is: in place of, or directly
  under, the text being corrected.
- **`hf upload` takes three positionals:** repo id, local path, path in repo (`space .`).
- **Reads from a private dataset** need `token=` on `hf_hub_download` and `HfApi`. The
  anonymous default 404s, which looks like a missing file.
- **Log timestamps and the `ts` fields are UTC.**

## Done means

The design was agreed, the Space is `RUNNING`, the page was verified in a browser, the local
handler and write-path tests passed (with the test decision removed), the pull step is
wired and documented, and the user has the links. The user's first sign-in stays unverified
until their decisions arrive: say so.
