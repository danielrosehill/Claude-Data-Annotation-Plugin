# Label Studio REST API capabilities

Probed 2026-11-15 against Label Studio Community 1.23 (`heartexlabs/label-studio` image). Endpoints vary slightly between releases: confirm with the instance's own schema.
Access gateways in front of the public URL (an SSO or zero-trust proxy) usually block API calls: use the direct API address (`LABEL_STUDIO_API_URL`).

Provenance tags: **[probed]** = request made against a live instance; **[schema]** = present in the instance's own OpenAPI (`GET /docs/api/schema/?format=json`); **[docs]** = labelstud.io / api.labelstud.io, not tested. Mutating calls marked untested should be tried on a throwaway project first.

## Auth

- Legacy token (works, probed): `Authorization: Token <token>`. Never expires. `GET /api/jwt/settings` -> `{"api_tokens_enabled":true,"legacy_api_tokens_enabled":true}` [probed], so both schemes are enabled.
- PAT/JWT (docs): `POST /api/token/refresh` body `{"refresh":"<PAT>"}` -> `{"access":"..."}`; send `Authorization: Bearer <access>`; access lives ~5 min. `Bearer <legacy token>` gives 401 [probed].
- Schema file: `/docs/api/schema/?format=json` works (200, OpenAPI JSON). `/docs/api/schema/` (YAML) works. `/api/schema/` 404; `/swagger.json` 302.

## Endpoint groups in schema (path counts, 20 groups)

projects 25, storages 74 (import and export x s3, gcs, azure, redis, localfiles), tasks 8, dm 13, ml 9, webhooks 7, users 5, token 5, current-user 5, organizations 6, labels 6, label_links 5, predictions 6, annotations 4, import 3, invite 2, jwt 2, session-policy 2, fsm 2.
Storage backends in `/api/storages/types` [probed]: s3, gcs, azure, redis, localfiles (same list for `/export/types`).

## Capability table

Paths are relative to the base. "Confirmed" = yes (probed OK on instance) / no (not tested or failed) / assumed.

| Capability | Method + path | Confirmed | Notes |
|---|---|---|---|
| Whoami | GET `/api/current-user/whoami` | yes | returns the token's user |
| Version | GET `/api/version` | yes | |
| List projects | GET `/api/projects/` | yes | paginated dict `{count,next,previous,results}` |
| Project counts | GET `/api/projects/counts/` | yes | paginated dict, task_number etc. |
| Get project | GET `/api/projects/{id}/` | yes | full settings + `parsed_label_config`, `control_weights` |
| Create project | POST `/api/projects/` | yes (2026-11-15, `labelstudio.py validate` throwaway create + DELETE) | body fields below |
| Update project | PATCH `/api/projects/{id}/` | yes (2026-11-15; no trailing slash works too) | same fields, partial |
| Delete project | DELETE `/api/projects/{id}/` | no [schema] | |
| Validate label config (new) | POST `/api/projects/validate/` | no [schema] | body `{"label_config": "..."}` |
| Validate label config (existing) | POST `/api/projects/{id}/validate/` | yes | valid -> 200 `{"config_essential_data_has_changed":true}`; malformed XML -> 400 `{"detail":"Couldn't find end of Start Tag ..."}` |
| List tasks (compact) | GET `/api/projects/{id}/tasks/` | yes | returns bare list (not dict) |
| List tasks (DM) | GET `/api/tasks/?project={id}` | yes | dict `{total, total_annotations, total_predictions, tasks:[...]}` |
| Create task | POST `/api/tasks/` | no [schema] | |
| Bulk import tasks | POST `/api/projects/{id}/import` | no [schema] | JSON list or file; 250K tasks / 200 MB per POST |
| Import status | GET `/api/projects/{id}/imports/{import_pk}/` | no [schema] | |
| Import predictions | POST `/api/projects/{id}/import/predictions` | no [schema] | |
| File uploads | GET/DELETE `/api/projects/{id}/file-uploads`, `/api/import/file-upload/{id}` | yes (GET) | GET returns `[]` |
| Delete all tasks | DELETE `/api/projects/{id}/tasks/` | no [schema] | destructive |
| Annotations | GET/POST `/api/tasks/{id}/annotations/`; GET/PATCH/DELETE `/api/annotations/{id}/` | no [schema] | |
| Predictions | GET `/api/predictions/?project=` (yes, `[]`); POST/PUT/PATCH/DELETE `/api/predictions/{id}/` | partial | |
| Annotators on project | GET `/api/projects/{id}/annotators/` | yes | `[]` |
| Project labels / label links | GET `/api/labels/?project=`, `/api/label_links/`; POST `/api/labels/bulk` | yes (GET) | paginated dicts; empty |
| Export formats (per project) | GET `/api/projects/{id}/export/formats` | yes | list of `{name,title,disabled,...}`; see Export |
| Direct export (sync, deprecated) | GET `/api/projects/{id}/export?exportType=X` | yes | streams file; `export_type=` also accepted |
| Snapshot export | POST `/api/projects/{id}/exports/` then GET `.../exports/{pk}`, POST `.../exports/{pk}/convert`, GET `.../exports/{pk}/download` | list yes (`[]`); rest no [schema] | async flow, better for large projects |
| Local-files storage list | GET `/api/storages/localfiles/?project={id}` | yes | bare list of storages with `path` |
| Storage CRUD/sync/validate | POST `/api/storages/{type}/`, `/validate`, `/{id}`, `/{id}/sync` (type = localfiles, s3, gcs, azure, redis; export variants under `/api/storages/export/{type}`) | list yes; writes no [schema] | `GET /api/storages/` also 200 |
| Webhooks | GET `/api/webhooks/` (yes, `[]`); POST `/api/webhooks/`; PUT/PATCH/DELETE `/api/webhooks/{id}/` | list yes | body: `project,url,send_payload,send_for_all_actions,headers,is_active,actions` |
| Webhook event list | GET `/api/webhooks/info/` | yes | 12 actions on this build (below) |
| ML backends | GET `/api/ml/?project=` (yes, `[]`); POST `/api/ml/`; GET/PATCH/DELETE `/api/ml/{id}`; POST `/api/ml/{id}/train`, `/predict/test`, `/interactive-annotating`; GET `/api/ml/{id}/versions` | list yes | note: no trailing slash on `/api/ml/{id}` |
| DM views (tabs) | GET `/api/dm/views/?project=` (yes, `[]`); POST `/api/dm/views/`; GET/PUT/PATCH/DELETE `/api/dm/views/{id}/`; POST `/api/dm/views/order/`; DELETE `/api/dm/views/reset/` | list yes | body `{project, data:{filters,ordering,hiddenColumns,...}}` |
| DM columns | GET `/api/dm/columns/?project=` | yes | dict `{columns:[...]}`; use these ids when building view filters |
| DM actions | GET `/api/dm/actions/?project=`; POST same | list yes | ids: retrieve_tasks_predictions, predictions_to_annotations, remove_duplicates, delete_tasks, delete_tasks_annotations, delete_tasks_predictions |
| DM project view | GET `/api/dm/project/?project=` | yes | |
| Users list | GET `/api/users/` | yes | bare list, 1 user |
| Create user | POST `/api/users/` | no [schema] | see answer 3a |
| Update/delete user | PATCH/DELETE `/api/users/{id}/` | no [schema] | |
| Invite link | GET `/api/invite` | yes | `{token, invite_url:"/user/signup/?token=..."}` ; prefix with public host |
| Reset invite | POST `/api/invite/reset-token` | no [schema] | |
| Organizations | GET `/api/organizations/` (yes, bare list, 1 org "Label Studio"), `/api/organizations/{id}` GET/PATCH | yes (GET) | |
| Memberships | GET `/api/organizations/{id}/memberships` (yes, paginated dict); DELETE `.../memberships/{user_pk}/` | yes (GET) | no role-change endpoint in schema |
| Legacy token | GET `/api/current-user/token` (yes); POST `/api/current-user/reset-token/` | GET yes | reset invalidates the current token: do not call casually |
| PAT list/create | GET/POST `/api/token/` | GET yes | GET returns list of `{token}` (refresh JWTs); POST no [schema] |
| PAT refresh/rotate/blacklist | POST `/api/token/refresh/`, `/rotate/`, `/blacklist/` | no [schema] | |
| JWT settings | GET/POST `/api/jwt/settings` | GET yes | |
| Session policy | GET/PATCH `/api/session-policy/` | GET yes | |
| FSM history | GET `/api/fsm/entities/{entity}/{id}/history` | yes | paginated, empty |
| Hotkeys | GET/PATCH `/api/current-user/hotkeys/` | no [schema] | |

## Project fields (POST /api/projects/ and PATCH /api/projects/{id}/) [schema]

`title, description, label_config, expert_instruction, show_instruction, show_skip_button, enable_empty_annotation, show_annotation_history, color (hex, e.g. "#FFFFFF"), maximum_annotations, is_published, is_draft, model_version, min_annotations_to_start_training, show_collab_predictions, sampling, show_ground_truth_first, show_overlap_first, overlap_cohort_percentage, annotator_evaluation_enabled, evaluate_predictions_automatically, control_weights, reveal_preannotations_interactively, skip_queue, task_data_login, task_data_password, pinned_at, organization, created_by`.
- `sampling` enum (exact strings): `Sequential sampling`, `Uniform sampling`, `Uncertainty sampling`. Live projects use `Sequential sampling` [probed].
- `skip_queue` seen: `REQUEUE_FOR_OTHERS` [probed]. Other values not enumerated here (assumed `REQUEUE_FOR_ME`, `IGNORE_SKIPPED` per docs).
- Project instructions = `expert_instruction` (text/HTML) shown when `show_instruction=true` [probed].
- Read-only in responses: `parsed_label_config, task_number, finished_task_number, queue_total, queue_done, total_annotations_number, config_has_control_tags, config_suitable_for_bulk_annotation`.
- `overlap` per-task: `maximum_annotations` + `overlap_cohort_percentage` (100 on live projects).

## Export formats [probed: GET /api/projects/{id}/export/formats]

Names returned: JSON, JSON_MIN, CSV, TSV, DOCLANG, CONLL2003, COCO, COCO_WITH_IMAGES, VOC, YOLO, YOLO_WITH_IMAGES, YOLO_OBB, YOLO_OBB_WITH_IMAGES, BRUSH_TO_NUMPY, BRUSH_TO_PNG, ASR_MANIFEST, BRUSH_TO_COCO (17).
- `disabled:true` is per-project and advisory: it reflects the label config. Project 2 (image classification) enabled = JSON, JSON_MIN, CSV, TSV, DOCLANG. Project 7 (audio) enabled = those + ASR_MANIFEST.
- Direct GET `/api/projects/7/export?exportType=` returned 200 for CSV (`.csv`), ASR_MANIFEST (`.zip` with `audio/` + `manifest.json`) and COCO (`.zip`, even though flagged disabled for that project) [probed]. So the disabled flag does not block the call; the content may be meaningless.
- Query params [schema]: `export_type`, `download_all_tasks`, `download_resources`, `ids`. `export_type=CSV` and `exportType=CSV` both gave a CSV [probed]. Docs are inconsistent on casing; use `exportType` (matches docs curl) or `export_type` (matches schema).

## Webhook actions on this build [probed: /api/webhooks/info/]

PROJECT_CREATED, PROJECT_UPDATED, PROJECT_DELETED, TASKS_CREATED, TASKS_DELETED, ANNOTATION_CREATED, ANNOTATIONS_CREATED, ANNOTATION_UPDATED, ANNOTATIONS_DELETED, LABEL_LINK_CREATED, LABEL_LINK_UPDATED, LABEL_LINK_DELETED. (Docs also list REVIEW_CREATED, REVIEW_UPDATED, REVIEWS_DELETED: Enterprise, absent here.) Entries carry `organization-only: true` for project-level events (they cannot be scoped to a single project).

## Answers to 3a-3g

**a. Users / passwords / invites.** Invite link: yes [probed] `GET /api/invite` works on CE and returns a signup URL with token (prefix with the public URL; the invitee must also pass any access gateway in front). Create user: `POST /api/users/` exists in schema (fields first_name, last_name, username, email, phone, allow_newsletters; `username` required per docs) but is **untested**; schema shape looks Enterprise-derived (docs name it `LseUserRequest`) and a forum thread says the API cannot set passwords (workaround: `label-studio reset_password` CLI in container) and a GitHub issue (#2731) says API-created users may not join the org. Treat as unreliable: prefer invite link, or CLI `reset_password`. No role-change endpoint (CE has no RBAC; only 1 org; memberships list/delete only).

**b. PATs.** `GET /api/token/` works (lists refresh JWTs, `{token}` only), `GET /api/jwt/settings` shows `api_tokens_enabled:true`. Refresh/rotate/blacklist/create are in schema; refresh flow per docs is not exercised here. Creation of a PAT is documented as UI (Account & Settings > Personal Access Tokens) but `POST /api/token/` exists ("Create a new API token for the current user") [schema, untested]. The legacy token (`GET /api/current-user/token`, `POST /api/current-user/reset-token/`) is the simple route and does not expire.

**c. Data Manager views/tabs.** Yes, full CRUD [schema], list probed (`[]`, no tabs saved). Shape per docs: `data.filters = {"conjunction":"and","items":[{"filter":"filter:tasks:<col>","operator":"...","type":"...","value":...}]}`, `data.ordering = ["-tasks:created_at"]`. `hiddenColumns` shape is not documented: create a tab in the UI once and GET it to copy the structure. Column ids come from `/api/dm/columns/`.

**d. Instructions and settings.** Yes: all via PATCH `/api/projects/{id}/` [schema; field values read back by GET, probed]. Instructions = `expert_instruction` + `show_instruction`. Also sampling, maximum_annotations, show_skip_button, color, enable_empty_annotation, reveal_preannotations_interactively, skip_queue, overlap_cohort_percentage. Validate label config first with `POST /api/projects/{id}/validate/` [probed].

**e. Webhooks.** Yes, `POST /api/webhooks/` [schema]; GET probed (`[]`, so none exist). Pass `actions` from the list above or `send_for_all_actions:true`.

**f. ML backends.** Yes, `POST /api/ml/` body `{"url":..., "project":id, "title":..., "is_interactive":..., "auth_method":"NONE|BASIC_AUTH", ...}` [schema + docs]; GET probed (`[]`). Backend URL must be reachable from the Label Studio container, not this machine.

**g. Export.** JSON, JSON_MIN, CSV, TSV, DOCLANG always; CONLL2003, COCO(_WITH_IMAGES), VOC, YOLO(_WITH_IMAGES), YOLO_OBB(_WITH_IMAGES), BRUSH_TO_*, ASR_MANIFEST offered and flagged enabled only when the label config fits (ASR_MANIFEST enabled on an audio project). Probed downloads: CSV, ASR_MANIFEST, COCO. Everything above is available on CE.

## Gotchas

- Trailing slashes: Django `APPEND_SLASH` redirect did not bite on GET (`/api/projects`, `/api/projects/2`, `/api/users` all 200 [probed]), but the schema is inconsistent: `/api/ml/{id}`, `/api/invite`, `/api/jwt/settings`, `/api/token/refresh/`, `/api/projects/{id}/import`, `/api/projects/{id}/export` are slash-free or slash-required per schema. Use exactly the schema path; POST to a wrong-slash path can 301 and drop the body (assumed).
- Pagination: `/api/projects/`, `/api/projects/counts/`, `/api/labels/`, `/api/label_links/`, memberships, fsm history return `{count,next,previous,results}` (`?page=&page_size=`). Bare lists: `/api/users/`, `/api/organizations/`, `/api/webhooks/`, `/api/ml/`, `/api/dm/views/`, `/api/dm/actions/`, `/api/storages/*/`, `/api/predictions/`, `/api/projects/{id}/tasks/`. Dict-wrapped but different: `/api/tasks/` -> `{tasks,total,...}`, `/api/dm/columns/` -> `{columns}`.
- List calls need a `?project=<id>` query on `dm`, `ml`, `storages`, `predictions`, `labels` list calls.
- Auth header scheme matters: `Token` for legacy, `Bearer` for PAT access JWT; the wrong one gives 401 `Authentication credentials were not provided`.
- 400 errors carry `{"detail": ..., "status_code": 400}`; validate returns XML parse errors verbatim.
- `version` in error bodies says 1.23.0 even though the image tag is 1.23.2.
- `GET /api/invite` and `GET /api/current-user/token` return live secrets: never log or commit them.
- Local-files storage paths are inside the container (`/label-studio/files/...`) and task URLs look like `/data/local-files/?d=<relpath>`; the storage must be synced (`POST /api/storages/localfiles/{id}/sync`) to create tasks.
- Export `disabled:true` is advisory only; do not rely on it to block a request, and do not trust a COCO export of a non-bbox project.
- No RBAC, workspaces, reviews, or per-project webhook scoping on CE.
- Unverified writes: all POST/PATCH/DELETE rows above were not run. A skill should test on a throwaway project and delete it.
