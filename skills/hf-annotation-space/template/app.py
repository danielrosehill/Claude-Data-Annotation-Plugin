"""Human review / annotation Space for a JSONL dataset on the Hugging Face Hub.

Template from the data-annotation plugin's `hf-annotation-space` skill. Edit CONFIG only;
the rest is generic. Shows one item at a time (side-by-side panes, optional highlighted
spans, metadata, flags), with colour-coded Accept / Reject / Fix / Skip buttons and keyboard
shortcuts (a / r / e / n), plus Browse and Stats tabs.

Each decision is committed to the dataset repo as <reviews_dir>/<id>.json, using the
signed-in user's own OAuth token. No token is stored in the Space, and a private dataset is
read with that same token after sign-in. Pull the decisions back with pull_reviews.py.
"""

from __future__ import annotations

import html
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone

import gradio as gr
from huggingface_hub import HfApi, hf_hub_download

CONFIG = {
    "title": "Pair review",
    "intro": "Red = original span, green = its replacement. Keys: **a** accept · **r** reject · **e** edit · **n** skip.",
    "dataset": os.environ.get("DATASET_REPO", "<owner>/<dataset>"),
    "items_path": "pairs.jsonl",      # JSONL file in the dataset repo, one item per line
    "reviews_dir": "reviews",         # one <id>.json per decision lands here
    "id_field": "id",
    # Side-by-side panes. "spans" names a list field of {from_key: str} dicts whose values
    # get highlighted in this pane with colour "mark" (o = red, n = green).
    "panes": [
        {"label": "Original", "field": "input", "spans": ("replacements", "original"), "mark": "o"},
        {"label": "Output", "field": "output", "spans": ("replacements", "replacement"), "mark": "n"},
    ],
    "table": ("replacements", "original", "replacement"),  # list field shown as a from → to table, or None
    "meta_fields": ["split", "genre", "locale"],
    "flags_field": "flags",           # list of strings shown as chips, or None
    "hard_flags": ("leak", "conflict"),  # chip prefixes coloured red instead of amber
    "edit_field": "output",           # what "Fix" edits and saves as rec["output"]
    # Queues: name -> predicate over (item). The first queue is the default. Unreviewed items only.
    "queues": {
        "test": lambda r: r.get("split") == "test",
        "train (flagged first)": lambda r: r.get("split") == "train",
        "dropped": lambda r: r.get("split") == "dropped",
    },
    "flagged_first": True,            # inside a queue, items with flags come first
}

CACHE: dict = {}
ID = CONFIG["id_field"]

CSS = """
.pane {white-space: pre-wrap; line-height: 1.6; padding: 12px 14px; border-radius: 8px; min-height: 120px;
       border: 1px solid var(--border-color-primary); background: var(--background-fill-secondary)}
mark.o {background: rgba(239, 68, 68, .28); color: inherit; border-radius: 3px; padding: 0 2px}
mark.n {background: rgba(34, 197, 94, .30); color: inherit; border-radius: 3px; padding: 0 2px}
.map td {padding: 2px 10px; border-bottom: 1px solid var(--border-color-primary)}
.chip {display: inline-block; padding: 1px 8px; margin: 2px; border-radius: 10px; font-size: .85em;
       background: rgba(245, 158, 11, .22)}
.chip.hard {background: rgba(239, 68, 68, .25)}
#accept {background: #16a34a; color: #fff; border: none}
#reject {background: #dc2626; color: #fff; border: none}
#fix {background: #d97706; color: #fff; border: none}
#skip {background: #6b7280; color: #fff; border: none}
#accept:hover, #reject:hover, #fix:hover, #skip:hover {filter: brightness(1.1)}
"""

JS = """
() => {
  document.addEventListener('keydown', (e) => {
    const t = e.target.tagName;
    if (t === 'TEXTAREA' || t === 'INPUT' || e.ctrlKey || e.metaKey || e.altKey) return;
    const id = {a: 'accept', r: 'reject', n: 'skip'}[e.key];
    if (id) { document.getElementById(id)?.click(); e.preventDefault(); }
    if (e.key === 'e') { document.querySelector('#fixbox textarea')?.focus(); e.preventDefault(); }
  });
}
"""


def items(token: str) -> list[dict]:
    if "items" not in CACHE:
        path = hf_hub_download(CONFIG["dataset"], CONFIG["items_path"], repo_type="dataset", token=token,
                               force_download=True)
        with open(path, encoding="utf-8") as f:
            CACHE["items"] = [json.loads(l) for l in f if l.strip()]
        CACHE["by_id"] = {str(r[ID]): r for r in CACHE["items"]}
    return CACHE["items"]


def reviewed(token: str) -> set[str]:
    d = CONFIG["reviews_dir"] + "/"
    files = HfApi(token=token).list_repo_files(CONFIG["dataset"], repo_type="dataset")
    return {f[len(d):-5] for f in files if f.startswith(d) and f.endswith(".json")}


def mark(text: str, spans: list[str], cls: str) -> str:
    spans = [s for s in set(spans) if s]
    if not spans:
        return html.escape(text)
    pat = re.compile("|".join(re.escape(s) for s in sorted(spans, key=len, reverse=True)))
    out, i = [], 0
    for m in pat.finditer(text):
        out += [html.escape(text[i:m.start()]), f'<mark class="{cls}">{html.escape(m.group(0))}</mark>']
        i = m.end()
    return "".join(out) + html.escape(text[i:])


def render(r: dict | None):
    """-> meta markdown, one HTML per pane, details HTML, edit-box text."""
    n = len(CONFIG["panes"])
    if r is None:
        return ("", *[""] * n, "", "")
    panes = []
    for p in CONFIG["panes"]:
        spans = [x.get(p["spans"][1], "") for x in r.get(p["spans"][0]) or []] if p.get("spans") else []
        panes.append(f'<div class="pane">{mark(str(r.get(p["field"], "")), spans, p.get("mark", "n"))}</div>')
    details = ""
    if CONFIG["table"]:
        lst, a, b = CONFIG["table"]
        rows = "".join(f"<tr><td>{html.escape(str(x.get(a, '')))}</td><td>→</td><td>{html.escape(str(x.get(b, '')))}</td></tr>"
                       for x in r.get(lst) or [])
        details += f'<table class="map">{rows or "<tr><td><i>(empty)</i></td></tr>"}</table>'
    if CONFIG["flags_field"]:
        details += "".join(f'<span class="chip{" hard" if f.startswith(CONFIG["hard_flags"]) else ""}">{html.escape(f)}</span>'
                           for f in r.get(CONFIG["flags_field"]) or [])
    meta = f"**{r[ID]}** · " + " · ".join(html.escape(str(r[k])) for k in CONFIG["meta_fields"] if r.get(k))
    return (meta, *panes, details, str(r.get(CONFIG["edit_field"], "")))


def queue(token: str, name: str, skipped: list[str]) -> list[dict]:
    done = reviewed(token)
    pred = CONFIG["queues"][name]
    q = [r for r in items(token) if str(r[ID]) not in done and str(r[ID]) not in skipped and pred(r)]
    if CONFIG["flagged_first"] and CONFIG["flags_field"]:
        q.sort(key=lambda r: not r.get(CONFIG["flags_field"]))
    return q


def next_item(token, name, skipped):
    q = queue(token, name, skipped)
    item = q[0] if q else None
    prog = f"{len(q)} left in **{name}** · {len(reviewed(token))} reviewed in total · {len(items(token))} items"
    return (str(item[ID]) if item else None, *render(item), prog)


def need(token):
    if token is None:
        raise gr.Error("Sign in with Hugging Face first.")
    return token.token


def on_load(name, skipped, oauth_token: gr.OAuthToken | None):
    if oauth_token is None:
        return (None, "Sign in to load the items.", *[""] * len(CONFIG["panes"]), "", "", "")
    return next_item(oauth_token.token, name, skipped or [])


def on_decide(verdict, item_id, fixed, note, name, skipped, profile: gr.OAuthProfile | None,
              oauth_token: gr.OAuthToken | None):
    tok = need(oauth_token)
    if verdict == "skip":
        skipped = (skipped or []) + ([item_id] if item_id else [])
        return (*next_item(tok, name, skipped), skipped, "")
    if not item_id:
        raise gr.Error("No item loaded.")
    r = CACHE["by_id"][item_id]
    rec = {"id": item_id, "verdict": verdict, "reviewer": profile.username if profile else None,
           "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if verdict == "fix":
        if fixed.strip() == str(r.get(CONFIG["edit_field"], "")).strip():
            raise gr.Error("Edit the text first (or press Accept).")
        rec[CONFIG["edit_field"]] = fixed.replace("\r\n", "\n")
    if note.strip():
        rec["note"] = note.strip()
    HfApi(token=tok).upload_file(path_or_fileobj=json.dumps(rec, ensure_ascii=False).encode(),
                                 path_in_repo=f"{CONFIG['reviews_dir']}/{item_id}.json",
                                 repo_id=CONFIG["dataset"], repo_type="dataset",
                                 commit_message=f"Review {item_id}: {verdict}")
    gr.Info(f"{item_id}: {verdict}")
    return (*next_item(tok, name, skipped or []), skipped, "")


def browse(name, idx, oauth_token: gr.OAuthToken | None):
    tok = need(oauth_token)
    rows = [r for r in items(tok) if name == "all" or CONFIG["queues"][name](r)]
    if not rows:
        return ("No items.", *[""] * len(CONFIG["panes"]), "", gr.update(maximum=0, value=0))
    idx = max(0, min(int(idx), len(rows) - 1))
    meta, *rest = render(rows[idx])
    return (f"{idx + 1} / {len(rows)} · {meta}", *rest[:-1], gr.update(maximum=len(rows) - 1, value=idx))


def stats(oauth_token: gr.OAuthToken | None):
    tok = need(oauth_token)
    its = items(tok)
    out = [f"**{len(its)} items** · **{len(reviewed(tok))} reviewed**"]
    out += [f"**{q}:** {sum(map(p, its))}" for q, p in CONFIG["queues"].items()]
    if CONFIG["flags_field"]:
        c = Counter(f.split(":")[0] for r in its for f in r.get(CONFIG["flags_field"]) or [])
        out.append("**flags:** " + " · ".join(f"{k} {v}" for k, v in c.most_common()))
    return "\n\n".join(out)


with gr.Blocks(title=CONFIG["title"], css=CSS, js=JS, theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"# {CONFIG['title']}\n{CONFIG['intro']}")
    gr.LoginButton(icon=None)  # the default icon renders as a broken image on private Spaces
    item_id, skipped = gr.State(None), gr.State([])
    with gr.Tab("Review"):
        qname = gr.Radio(list(CONFIG["queues"]), value=next(iter(CONFIG["queues"])), label="Queue")
        prog, meta = gr.Markdown(), gr.Markdown()
        panes = []
        with gr.Row():
            for p in CONFIG["panes"]:
                with gr.Column():
                    gr.Markdown(f"**{p['label']}**")
                    panes.append(gr.HTML())
        details = gr.HTML()
        with gr.Row():
            b_acc = gr.Button("✓ Accept (a)", elem_id="accept")
            b_rej = gr.Button("✗ Reject (r)", elem_id="reject")
            b_skip = gr.Button("→ Skip (n)", elem_id="skip")
        with gr.Accordion("Fix (e)", open=False):
            fixbox = gr.Textbox(lines=10, max_lines=40, label="Corrected text", elem_id="fixbox")
            note = gr.Textbox(label="Note (optional)")
            b_fix = gr.Button("✎ Save fix", elem_id="fix")
    with gr.Tab("Browse"):
        with gr.Row():
            bq = gr.Dropdown(["all", *CONFIG["queues"]], value="all", label="Subset")
            idx = gr.Slider(0, 0, step=1, value=0, label="Item")
        bmeta = gr.Markdown()
        bpanes = []
        with gr.Row():
            for p in CONFIG["panes"]:
                with gr.Column():
                    gr.Markdown(f"**{p['label']}**")
                    bpanes.append(gr.HTML())
        bdetails = gr.HTML()
        with gr.Row():
            prev_b, next_b = gr.Button("← Prev"), gr.Button("Next →")
    with gr.Tab("Stats"):
        st = gr.Markdown()
        gr.Button("Refresh").click(stats, None, st)

    shown = [item_id, meta, *panes, details, fixbox, prog]
    demo.load(on_load, [qname, skipped], shown)
    qname.change(on_load, [qname, skipped], shown)
    for btn, v in ((b_acc, "accept"), (b_rej, "reject"), (b_skip, "skip"), (b_fix, "fix")):
        btn.click(on_decide, [gr.State(v), item_id, fixbox, note, qname, skipped], [*shown, skipped, note])

    # gr.OAuthToken is injected only into functions that type-hint it: no lambdas here.
    def browse_first(q, oauth_token: gr.OAuthToken | None):
        return browse(q, 0, oauth_token)

    def browse_prev(q, i, oauth_token: gr.OAuthToken | None):
        return browse(q, i - 1, oauth_token)

    def browse_next(q, i, oauth_token: gr.OAuthToken | None):
        return browse(q, i + 1, oauth_token)

    b_out = [bmeta, *bpanes, bdetails, idx]
    bq.change(browse_first, [bq], b_out)
    idx.release(browse, [bq, idx], b_out)
    prev_b.click(browse_prev, [bq, idx], b_out)
    next_b.click(browse_next, [bq, idx], b_out)

if __name__ == "__main__":
    demo.launch()
