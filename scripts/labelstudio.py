#!/usr/bin/env python3
"""Label Studio helper for the data-annotation plugin. Standard library only.

Run with the token in the environment (however the user injects secrets), for example:
    uv run labelstudio.py <command> [args]

Settings, each read from the environment first, then from the overlay's profile.env:
    LABEL_STUDIO_URL          base URL people open in the browser (required)
    LABEL_STUDIO_API_URL      base URL for API calls if different (for example a LAN address when the
                              public host sits behind an access gateway); default = LABEL_STUDIO_URL
    LABEL_STUDIO_TOKEN_ENV    NAME of the environment variable holding the legacy API token;
                              default LABEL_STUDIO_TOKEN
The token itself is only ever read from the environment, never from a file.

Commands (all print JSON):
    whoami
    projects
    project <id>                              summary: counts, labels per control
    overview                                  every project: title, description, counts, data keys, control types
                                              (the "what's the project for X?" lookup)
    set-meta <id> [--title T] [--description D] [--confirm]
                                              rename / re-describe a project; dry run shows old vs new
    get-config <id> [-o FILE]                 current label_config
    validate <xml> [--project ID]             local XML checks + server check (existing project, or throwaway project)
    set-config <id> <xml> --confirm           back up the old config, validate, PATCH
    create-project <xml> --title T [--description D] [--confirm]
    import <id> <tasks.json> [--confirm]      list of {"data": {...}, "predictions": [...]}, in batches of 200
    export <id> [-o FILE]                     JSON export of all tasks with annotations
    label-usage <id>                          how often each label/choice value is used in annotations
    add-localfiles <id> <subdir> [--confirm]  local-files storage on /label-studio/files/<subdir> (no sync)
    sample-tasks <id> [-n N]                  first N tasks' data, to see the field names
    group-diff <id> <id> ...                  compare a project group: config, instructions, settings; diff vs the first
    patch-project <id> --json '{...}' [--confirm]
                                              set project settings (expert_instruction, show_instruction, sampling, ...)
    templates                                 list built-in and overlay templates
    create-from-template <tid> --title T [--confirm]
                                              create a project from a template folder (config, instructions, settings)
    group-set <id> ... --xml F [--instructions F] [--confirm]
                                              apply one config (and/or instructions) to every project in a group,
                                              validated per project, old configs backed up
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import difflib
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

def _overlay():
    import importlib.util
    spec = importlib.util.spec_from_file_location("da_overlay", Path(__file__).with_name("overlay.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OVERLAY = _overlay()
DATA_ROOT = OVERLAY.data_dir()
PUBLIC = OVERLAY.get("LABEL_STUDIO_URL").rstrip("/")
API = (OVERLAY.get("LABEL_STUDIO_API_URL") or PUBLIC).rstrip("/")
TOKEN_ENV = OVERLAY.get("LABEL_STUDIO_TOKEN_ENV", "LABEL_STUDIO_TOKEN")
FILES_ROOT = OVERLAY.get("LABEL_STUDIO_FILES_ROOT", "/label-studio/files").rstrip("/")
PLUGIN_ROOT = Path(__file__).resolve().parent.parent

OBJECT_TAGS = {"Text", "HyperText", "Image", "Audio", "AudioPlus", "Video", "Paragraphs", "Table", "TimeSeries",
               "Pdf", "List", "Ranker", "Markdown", "Chat"}
CONTROL_TAGS = {"Labels", "Choices", "TextArea", "Rating", "Number", "DateTime", "Taxonomy", "RectangleLabels",
                "Rectangle", "PolygonLabels", "Polygon", "KeyPointLabels", "KeyPoint", "BrushLabels", "Brush",
                "EllipseLabels", "Ellipse", "HyperTextLabels", "ParagraphLabels", "TimeSeriesLabels", "VideoRectangle",
                "Relations", "Pairwise", "Ranker", "TimelineLabels", "MagicWand", "BitmaskLabels", "Bitmask"}


def out(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def die(msg: str, code: int = 1) -> None:
    out({"ok": False, "error": msg})
    sys.exit(code)


def api(method: str, path: str, body=None):
    if not API:
        die("LABEL_STUDIO_URL is not set (environment or overlay profile.env); run the setup skill")
    token = os.environ.get(TOKEN_ENV)
    if not token:
        die(f"{TOKEN_ENV} is not set in the environment; export it with your secrets tool (the overlay stores only the variable's name)")
    req = urllib.request.Request(API + path, method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Token {token}", "Content-Type": "application/json",
                                          "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = raw[:2000]
        raise ApiError(e.code, detail) from None
    except urllib.error.URLError as e:
        die(f"cannot reach {API}: {e.reason} (check LABEL_STUDIO_API_URL and network access)")


class ApiError(Exception):
    def __init__(self, status, detail):
        super().__init__(f"HTTP {status}")
        self.status, self.detail = status, detail


def project_url(pid) -> str:
    return f"{PUBLIC}/projects/{pid}/data"


def local_check(xml: str) -> dict:
    errors, warnings = [], []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return {"errors": [f"XML parse error: {e}"], "warnings": []}
    if root.tag != "View":
        warnings.append(f"root tag is <{root.tag}>, normally <View>")
    names = collections.Counter(el.get("name") for el in root.iter() if el.get("name"))
    errors += [f"duplicate name '{n}'" for n, c in names.items() if c > 1]
    objects = {el.get("name") for el in root.iter() if el.tag in OBJECT_TAGS and el.get("name")}
    for el in root.iter():
        if el.tag in OBJECT_TAGS | CONTROL_TAGS and not el.get("name"):
            errors.append(f"<{el.tag}> has no name")
        if el.tag in CONTROL_TAGS and el.tag not in {"Relations"}:
            for t in filter(None, (el.get("toName") or "").split(",")):
                if t not in objects:
                    errors.append(f"<{el.tag} name='{el.get('name')}'> toName='{t}' is not an object tag")
        if el.tag in {"AudioPlus"}:
            warnings.append("AudioPlus is deprecated; use Audio")
    hotkeys = collections.Counter(el.get("hotkey") for el in root.iter() if el.get("hotkey"))
    warnings += [f"hotkey '{k}' used {c} times" for k, c in hotkeys.items() if c > 1]
    return {"errors": errors, "warnings": warnings}


def server_check(xml: str, pid: int | None) -> dict:
    if pid:
        try:
            r = api("POST", f"/api/projects/{pid}/validate/", {"label_config": xml})
            return {"ok": True, "mode": f"project {pid}", "response": r}
        except ApiError as e:
            return {"ok": False, "mode": f"project {pid}", "status": e.status, "detail": e.detail}
    try:
        p = api("POST", "/api/projects", {"title": "validate-throwaway", "label_config": xml})
    except ApiError as e:
        return {"ok": False, "mode": "throwaway", "status": e.status, "detail": e.detail}
    api("DELETE", f"/api/projects/{p['id']}/")
    return {"ok": True, "mode": "throwaway"}


GROUP_SETTINGS = ("show_instruction", "show_skip_button", "enable_empty_annotation", "show_annotation_history",
                  "maximum_annotations", "sampling", "show_collab_predictions", "skip_queue",
                  "reveal_preannotations_interactively", "min_annotations_to_start_training", "color")


def short_hash(text) -> str:
    return hashlib.sha256((text or "").strip().encode()).hexdigest()[:10]


def group_diff(ids) -> dict:
    ps = [api("GET", f"/api/projects/{i}") for i in ids]
    base = ps[0]
    rows, diffs = [], {}
    for p in ps:
        rows.append({"id": p["id"], "title": p["title"], "tasks": p.get("task_number"),
                     "annotated": p.get("num_tasks_with_annotations"),
                     "config": short_hash(p["label_config"]), "instructions": short_hash(p.get("expert_instruction")),
                     **{k: p.get(k) for k in GROUP_SETTINGS}})
        if p is not base and p["label_config"].strip() != base["label_config"].strip():
            diffs[p["id"]] = "".join(difflib.unified_diff(
                base["label_config"].strip().splitlines(True), p["label_config"].strip().splitlines(True),
                f"project {base['id']}", f"project {p['id']}"))
    differing = [k for k in ("config", "instructions", *GROUP_SETTINGS) if len({json.dumps(r[k]) for r in rows}) > 1]
    return {"consistent": not differing, "differing_fields": differing, "projects": rows, "config_diffs_vs_first": diffs}


def list_templates() -> list:
    rows = []
    for origin, root in (("overlay", DATA_ROOT / "templates" / "label-studio"), ("built-in", PLUGIN_ROOT / "templates" / "label-studio")):
        if root.is_dir():
            for d in sorted(root.iterdir()):
                if (d / "config.xml").exists():
                    meta = json.loads((d / "template.json").read_text()) if (d / "template.json").exists() else {}
                    rows.append({"id": d.name, "origin": origin, "title": meta.get("title", d.name),
                                 "summary": meta.get("summary", ""), "path": str(d)})
    seen, out_rows = set(), []
    for r in rows:  # overlay is listed first, so it wins over a built-in of the same name
        if r["id"] not in seen:
            seen.add(r["id"]); out_rows.append(r)
    return out_rows


def find_template(tid: str):
    for r in list_templates():
        if r["id"] == tid:
            return Path(r["path"])
    return None


def backup_config(pid: int, xml: str) -> str:
    d = DATA_ROOT / "config-history" / str(pid)
    d.mkdir(parents=True, exist_ok=True)
    f = d / (dt.datetime.now().strftime("%Y%m%dT%H%M%S") + ".xml")
    f.write_text(xml)
    return str(f)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("whoami")
    sp.add_parser("projects")
    sp.add_parser("overview")
    sm = sp.add_parser("set-meta"); sm.add_argument("id", type=int); sm.add_argument("--title")
    sm.add_argument("--description"); sm.add_argument("--confirm", action="store_true")
    for name in ("project", "label-usage"):
        sp.add_parser(name).add_argument("id", type=int)
    g = sp.add_parser("get-config"); g.add_argument("id", type=int); g.add_argument("-o")
    v = sp.add_parser("validate"); v.add_argument("xml"); v.add_argument("--project", type=int)
    s = sp.add_parser("set-config"); s.add_argument("id", type=int); s.add_argument("xml"); s.add_argument("--confirm", action="store_true")
    c = sp.add_parser("create-project"); c.add_argument("xml"); c.add_argument("--title", required=True)
    c.add_argument("--description", default=""); c.add_argument("--confirm", action="store_true")
    i = sp.add_parser("import"); i.add_argument("id", type=int); i.add_argument("tasks"); i.add_argument("--confirm", action="store_true")
    e = sp.add_parser("export"); e.add_argument("id", type=int); e.add_argument("-o")
    lf = sp.add_parser("add-localfiles"); lf.add_argument("id", type=int); lf.add_argument("subdir"); lf.add_argument("--confirm", action="store_true")
    st = sp.add_parser("sample-tasks"); st.add_argument("id", type=int); st.add_argument("-n", type=int, default=3)
    gd = sp.add_parser("group-diff"); gd.add_argument("ids", type=int, nargs="+")
    gs = sp.add_parser("group-set"); gs.add_argument("ids", type=int, nargs="+"); gs.add_argument("--xml")
    gs.add_argument("--instructions"); gs.add_argument("--confirm", action="store_true")
    pp = sp.add_parser("patch-project"); pp.add_argument("id", type=int); pp.add_argument("--json", required=True)
    pp.add_argument("--confirm", action="store_true")
    sp.add_parser("templates")
    ct = sp.add_parser("create-from-template"); ct.add_argument("tid"); ct.add_argument("--title", required=True)
    ct.add_argument("--description", default=""); ct.add_argument("--confirm", action="store_true")
    a = ap.parse_args(argv)

    try:
        if a.cmd == "whoami":
            u = api("GET", "/api/current-user/whoami")
            out({"ok": True, "api": API, "email": u.get("email"), "version": api("GET", "/api/version").get("release")})
        elif a.cmd == "projects":
            r = api("GET", "/api/projects?page_size=1000")
            out([{"id": p["id"], "title": p["title"], "tasks": p.get("task_number"),
                  "annotated": p.get("num_tasks_with_annotations"), "url": project_url(p["id"])}
                 for p in r.get("results", r)])
        elif a.cmd == "project":
            p = api("GET", f"/api/projects/{a.id}")
            out({"id": p["id"], "title": p["title"], "description": p.get("description"), "tasks": p.get("task_number"),
                 "annotated": p.get("num_tasks_with_annotations"), "annotations": p.get("total_annotations_number"),
                 "predictions": p.get("total_predictions_number"), "url": project_url(p["id"]),
                 "controls": {k: {"type": v["type"], "to": v["to_name"], "labels": v.get("labels")}
                              for k, v in (p.get("parsed_label_config") or {}).items()}})
        elif a.cmd == "overview":
            r = api("GET", "/api/projects?page_size=1000")
            rows = []
            for p in sorted(r.get("results", r), key=lambda p: p["id"]):
                cfg = p.get("label_config") or ""
                try:
                    root = ET.fromstring(cfg)
                    keys = sorted({el.get("value", "")[1:] for el in root.iter()
                                   if el.tag in OBJECT_TAGS and (el.get("value") or "").startswith("$")})
                    controls = sorted({el.tag for el in root.iter() if el.tag in CONTROL_TAGS})
                except ET.ParseError:
                    keys, controls = [], []
                rows.append({"id": p["id"], "title": p["title"], "description": p.get("description") or "",
                             "tasks": p.get("task_number"), "annotated": p.get("num_tasks_with_annotations"),
                             "created": (p.get("created_at") or "")[:10], "data_keys": keys, "controls": controls,
                             "url": project_url(p["id"])})
            out(rows)
        elif a.cmd == "set-meta":
            if a.title is None and a.description is None:
                die("give --title and/or --description")
            p = api("GET", f"/api/projects/{a.id}")
            body = {k: v for k, v in (("title", a.title), ("description", a.description)) if v is not None}
            change = {k: {"old": p.get(k) or "", "new": v} for k, v in body.items()}
            if not a.confirm:
                out({"ok": True, "dry_run": True, "id": a.id, "change": change,
                     "note": "re-run with --confirm to apply"}); return
            api("PATCH", f"/api/projects/{a.id}", body)
            q = api("GET", f"/api/projects/{a.id}")
            out({"ok": True, "id": a.id, "now": {k: q.get(k) for k in body}, "was": {k: c["old"] for k, c in change.items()},
                 "url": project_url(a.id)})
        elif a.cmd == "get-config":
            xml = api("GET", f"/api/projects/{a.id}")["label_config"]
            if a.o:
                Path(a.o).write_text(xml); out({"ok": True, "written": a.o})
            else:
                print(xml)
        elif a.cmd == "validate":
            xml = Path(a.xml).read_text()
            loc = local_check(xml)
            srv = server_check(xml, a.project) if not loc["errors"] else {"skipped": "local errors"}
            out({"ok": not loc["errors"] and srv.get("ok", False), "local": loc, "server": srv})
        elif a.cmd == "set-config":
            xml = Path(a.xml).read_text()
            loc = local_check(xml)
            if loc["errors"]:
                die(f"local validation failed: {loc['errors']}")
            srv = server_check(xml, a.id)
            if not srv["ok"]:
                out({"ok": False, "server": srv}); sys.exit(1)
            if not a.confirm:
                out({"ok": True, "dry_run": True, "local": loc, "server": srv, "note": "re-run with --confirm to apply"}); return
            old = api("GET", f"/api/projects/{a.id}")["label_config"]
            bak = backup_config(a.id, old)
            api("PATCH", f"/api/projects/{a.id}", {"label_config": xml})
            out({"ok": True, "backup": bak, "warnings": loc["warnings"], "url": project_url(a.id)})
        elif a.cmd == "create-project":
            xml = Path(a.xml).read_text()
            loc = local_check(xml)
            if loc["errors"]:
                die(f"local validation failed: {loc['errors']}")
            if not a.confirm:
                srv = server_check(xml, None)
                out({"ok": srv["ok"], "dry_run": True, "server": srv, "note": "re-run with --confirm to create"}); return
            p = api("POST", "/api/projects", {"title": a.title, "description": a.description, "label_config": xml})
            out({"ok": True, "id": p["id"], "url": project_url(p["id"])})
        elif a.cmd == "import":
            tasks = json.loads(Path(a.tasks).read_text())
            if not isinstance(tasks, list):
                die("tasks file must be a JSON list")
            keys = sorted({k for t in tasks for k in t.get("data", t)})
            if not a.confirm:
                out({"dry_run": True, "tasks": len(tasks), "data_keys": keys,
                     "with_predictions": sum(1 for t in tasks if t.get("predictions"))}); return
            n = 0
            for j in range(0, len(tasks), 200):
                api("POST", f"/api/projects/{a.id}/import", tasks[j:j + 200]); n += len(tasks[j:j + 200])
            out({"ok": True, "imported": n, "url": project_url(a.id)})
        elif a.cmd == "export":
            # download_all_tasks: include tasks without annotations too (default export skips them)
            r = api("GET", f"/api/projects/{a.id}/export?exportType=JSON&download_all_tasks=true")
            if a.o:
                Path(a.o).write_text(json.dumps(r, ensure_ascii=False, indent=1)); out({"ok": True, "tasks": len(r), "written": a.o})
            else:
                out(r)
        elif a.cmd == "label-usage":
            r = api("GET", f"/api/projects/{a.id}/export?exportType=JSON")
            use = collections.defaultdict(collections.Counter)
            for t in r:
                for ann in t.get("annotations", []):
                    for res in ann.get("result", []):
                        val = res.get("value", {})
                        for k in ("labels", "choices", "rectanglelabels", "polygonlabels", "keypointlabels",
                                  "brushlabels", "hypertextlabels", "paragraphlabels", "timeserieslabels", "taxonomy"):
                            for x in val.get(k, []):
                                use[res.get("from_name")][" / ".join(x) if isinstance(x, list) else x] += 1
            out({"tasks": len(r), "usage": {k: dict(v) for k, v in use.items()}})
        elif a.cmd == "add-localfiles":
            path = f"{FILES_ROOT}/{a.subdir.strip('/')}"
            have = [s for s in api("GET", f"/api/storages/localfiles?project={a.id}") if s["path"] == path]
            if have:
                out({"ok": True, "exists": have[0]["id"], "path": path}); return
            if not a.confirm:
                out({"dry_run": True, "path": path}); return
            s = api("POST", "/api/storages/localfiles", {"project": a.id, "path": path, "title": a.subdir,
                                                          "use_blob_urls": False})
            out({"ok": True, "storage": s["id"], "path": path,
                 "task_url_form": f"/data/local-files/?d={a.subdir.strip('/')}/<file>"})
        elif a.cmd == "group-diff":
            out(group_diff(a.ids))
        elif a.cmd == "group-set":
            if not (a.xml or a.instructions):
                die("give --xml and/or --instructions")
            body, checks = {}, {}
            if a.xml:
                xml = Path(a.xml).read_text()
                loc = local_check(xml)
                if loc["errors"]:
                    die(f"local validation failed: {loc['errors']}")
                checks = {i: server_check(xml, i) for i in a.ids}
                bad = {i: c for i, c in checks.items() if not c["ok"]}
                if bad:
                    out({"ok": False, "failed_validation": bad, "note": "nothing applied"}); sys.exit(1)
                body["label_config"] = xml
            if a.instructions:
                body["expert_instruction"] = Path(a.instructions).read_text().strip()
                body["show_instruction"] = True
            if not a.confirm:
                out({"ok": True, "dry_run": True, "projects": a.ids, "fields": sorted(body),
                     "validated": sorted(checks), "note": "re-run with --confirm to apply to all"}); return
            done = []
            for i in a.ids:
                bak = backup_config(i, api("GET", f"/api/projects/{i}")["label_config"]) if a.xml else None
                api("PATCH", f"/api/projects/{i}", body); done.append({"id": i, "backup": bak})
            out({"ok": True, "applied": done, "after": group_diff(a.ids)["differing_fields"]})
        elif a.cmd == "patch-project":
            body = json.loads(a.json)
            if not a.confirm:
                out({"ok": True, "dry_run": True, "id": a.id, "fields": body, "note": "re-run with --confirm"}); return
            api("PATCH", f"/api/projects/{a.id}", body)
            q = api("GET", f"/api/projects/{a.id}")
            out({"ok": True, "now": {k: q.get(k) for k in body}, "url": project_url(a.id)})
        elif a.cmd == "templates":
            out(list_templates())
        elif a.cmd == "create-from-template":
            t = find_template(a.tid)
            if not t:
                die(f"no template '{a.tid}' (see: templates)")
            xml = (t / "config.xml").read_text()
            loc = local_check(xml)
            if loc["errors"]:
                die(f"template config fails local validation: {loc['errors']}")
            meta = json.loads((t / "template.json").read_text()) if (t / "template.json").exists() else {}
            settings = meta.get("project_settings", {})
            instr = (t / "instructions.md").read_text().strip() if (t / "instructions.md").exists() else ""
            if not a.confirm:
                out({"ok": True, "dry_run": True, "template": str(t), "settings": settings,
                     "instructions": bool(instr), "server": server_check(xml, None),
                     "note": "re-run with --confirm to create"}); return
            p = api("POST", "/api/projects", {"title": a.title, "description": a.description, "label_config": xml})
            patch = dict(settings)
            if instr:
                patch.update({"expert_instruction": instr, "show_instruction": True})
            if patch:
                api("PATCH", f"/api/projects/{p['id']}", patch)
            out({"ok": True, "id": p["id"], "url": project_url(p["id"]), "applied_settings": sorted(patch),
                 "example_tasks": str(t / "example-tasks.json")})
        elif a.cmd == "sample-tasks":
            r = api("GET", f"/api/tasks?project={a.id}&page_size={a.n}")
            out([t["data"] for t in r.get("tasks", [])])
    except ApiError as e:
        out({"ok": False, "status": e.status, "detail": e.detail}); sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
