---
name: hf-annotation-space
description: Stand up a private Hugging Face Space for humans to review, annotate or browse a JSONL dataset. Ships a Gradio template with side-by-side panes, highlighted spans, colour-coded Accept / Reject / Fix / Skip buttons, keyboard shortcuts, and Browse and Stats tabs. Decisions are saved to the dataset repo with the reviewer's own HF sign-in, so the Space holds no secrets. Use when the user says "make an HF Space to review this data", "annotation Space", "I want to look at the data on HF", "review UI for these pairs", or when synthetic or model-labelled data needs a human pass before training.
---

# HF annotation Space

Builds a **private** Gradio Space on top of a **private** HF dataset so the user can review
items from any browser or device. Every decision is committed back to the dataset, and a pull
script merges it into the project's local `reviews.jsonl`.

The template is in `template/` next to this file (`app.py`, `README.md`, `requirements.txt`,
`pull_reviews.py`). It was first built and verified for Proximate-Pseudonymizer on 2026-10-21
(`danielrosehill/Proximate-Pseudonymizer`, `space/`). Copy it rather than writing a new UI.

## Design decisions (keep them unless the user asks otherwise)

| Decision | Why |
| --- | --- |
| Space **and** dataset private | Review data is unvetted. Make it public later, once it is reviewed. |
| `hf_oauth: true`, scopes `read-repos` + `write-repos`; read and write with the **signed-in user's token** | No `HF_TOKEN` secret in the Space. Only accounts with write access to the dataset can save. |
| Items loaded lazily **after sign-in** | A private dataset can't be read at import time without a stored token. |
| One file per decision: `reviews/<id>.json` = `{id, verdict, reviewer, ts, note?, <edit_field>?}` | Concurrent reviewers never conflict, re-reviewing overwrites, and the queue is just "ids without a file". |
| Colours: Accept green `#16a34a`, Reject red `#dc2626`, Fix amber `#d97706`, Skip grey `#6b7280` | Readable at a glance, and the same in every Space. Set by `elem_id` in CSS. |
| Keys: `a` accept, `r` reject, `e` focus the fix box, `n` skip; ignored while typing | Hundreds of items get reviewed fast. Injected with `gr.Blocks(js=...)`. |
| Highlight colours as `rgba(...)` backgrounds with `color: inherit`; panes use Gradio CSS variables | Works in both light and dark theme without a second palette. |
| Tabs: Review (queues), Browse (any subset, slider, prev/next), Stats | "Look at the data" and "review the data" are both common asks; one Space covers both. |
| Queues = named predicates; flagged items first | Review the gold or test pool first, then whatever the validator flagged. |
| Edit box **always visible**, directly under the pane it edits; Save fix sits in the main button row | The first version hid it in a collapsed accordion, and the reviewer reported they couldn't edit at all. |
| Accept with an edited box saves it as a `fix` | Reviewers edit and then press Accept out of habit; the edit must not be lost. |
| Skip lives in session state only | Skipping must never write a decision. |

## Steps

1. **Shape the data.** One JSONL file with a stable string `id` per item and the fields to
   show. Useful extras: a `split` field for queues, a `flags` list from automatic validation,
   and a list of `{from, to}` dicts for the highlighted spans and the from → to table.
2. **Dataset (private).** `hf repos create <owner>/<name> --repo-type dataset --private --exist-ok`,
   then upload the items file and a short card. Add `configs: [{config_name: <x>, data_files: <items>.jsonl}]`
   to the card frontmatter so the dataset viewer ignores `reviews/`.
3. **Space code.** Copy `template/` into the project as `space/`. Edit `CONFIG` at the top of
   `app.py` (dataset, items path, panes, spans, table, meta fields, flags, edit field, queues)
   and fill in the placeholders in `README.md` (title, `short_description` of 60 chars or
   fewer, links). The emoji must be a single Extended_Pictographic character: `¶` is rejected.
4. **Test locally before deploying.** With the user's write token, import the app and call the
   handlers directly, using a stub object that has `.token`:
   ```bash
   DATASET_REPO=<owner>/<name> HF_TOKEN=$HF_TOKEN uv run --with "gradio[oauth]==5.49.1" --with huggingface_hub \
     python -c "import os, app; T=type('T',(),{'token':os.environ['HF_TOKEN']}); print(app.on_load(next(iter(app.CONFIG['queues'])), [], T())[:2])"
   ```
   Then exercise the write path once: call `on_decide("accept", <id>, "", "smoke test", <queue>, [], profile_stub, token_stub)`,
   run `pull_reviews.py`, and **delete the test decision** from the Hub
   (`hf repos delete-files <repo> reviews/<id>.json --repo-type dataset`) and from the local file.
5. **Deploy (private).** `hf repos create <owner>/<space> --repo-type space --space-sdk gradio --private --exist-ok`,
   then `hf upload <owner>/<space> space . --repo-type space`. Poll
   `GET https://huggingface.co/api/spaces/<owner>/<space>/runtime` until `stage` is `RUNNING`.
   On a build error, read the logs: `GET .../logs/build` or `.../logs/run` (SSE; capture with
   `timeout 8 curl -sN`, then grep `"data":`).
6. **Verify the page.** Open `https://huggingface.co/spaces/<owner>/<space>` in a real browser
   (Claude in Chrome) and check that it renders behind the private gate. **Don't click "Sign in
   with Hugging Face"**: that is an OAuth consent grant, so it's the user's click. Say plainly
   that the in-browser sign-in hasn't been exercised until the user has done it.
7. **Wire the project.** Add `pull_reviews.py` (or call the template's with
   `<owner>/<dataset> data/reviews.jsonl`) to the project's pipeline before the split/build
   step, and document the Space, dataset and pull step in the project's README.

## Traps (all hit while building the first one)

- **`gr.OAuthToken` / `gr.OAuthProfile` are injected only into functions whose signature
  type-hints them.** A `lambda` wrapper silently receives `None`, and every call fails with
  "sign in first". Write real `def`s.
- **A local run needs `gradio[oauth]`**, not plain `gradio`, whenever the README sets
  `hf_oauth: true`. Otherwise you get `ImportError … itsdangerous` at `gr.Blocks` exit. On the
  Space itself the extra is installed automatically.
- **`gr.LoginButton()` showed a broken logo image on a private Space.** Use
  `gr.LoginButton(icon=None)`.
- **`hf upload` takes three positionals:** repo id, local path, path in repo (`space .`).
- **Reads from a private dataset** need the token on `hf_hub_download(..., token=...)` and
  on `HfApi(token=...)`. The anonymous default 404s, which looks like a missing file.
- **The Space's run log timestamps are UTC.** So are the template's `ts` fields.

## Done means

Space `RUNNING`, page verified in a browser, local handler test and write-path test passed
(with the test decision removed), pull step documented in the project, and links to the Space
and dataset given to the user. The user's first sign-in is the last unverified step: say so.
