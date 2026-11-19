# Reviewing an annotation screen

How to look at a Label Studio screen before the annotator does, and the house style it should meet.

## Look at it yourself, in a browser the annotator is not using

- Use a separate automation browser, not the annotator's own browser: they are usually labelling in it.
- Open `<LABEL_STUDIO_URL>/projects/<pid>/data?labeling=1[&task=<id>]` signed in as a reviewer account. Never type a
  password on the user's behalf. If the instance sits behind an access gateway, the automation browser needs an
  already-authenticated session.
- One script that waits for regions (`.htx-highlight`) and clicks one, then a screenshot. Opening a task and selecting
  a region does not create an annotation; don't tick choices or submit.
- **A spinner that never resolves means the config broke the editor**, even though server validation passed. Roll back
  at once (`labelstudio.py set-config <pid> <newest config-history backup> --confirm`). An open tab keeps the old config
  until reloaded.

## Test risky changes in a throwaway project first

Server validation does not catch editor crashes. For anything beyond a new Choice or a style change (conditional views,
nested `visibleWhen`, new control types):

1. `labelstudio.py create-project <xml> --title "zz test: <what> (delete me)" --confirm`
2. import one representative task with its predictions; `PATCH /api/projects/<id>/` with `show_collab_predictions: true`
   and `model_version` so the pre-labels show
3. check it in the browser as above
4. apply to the live project, check again, then delete the test project (`DELETE /api/projects/<id>/`)

## Style that works

- **Group fields into boxes by scope.** A card for "Selected span" (`visibleWhen="region-selected"`, per-region controls)
  and a separate card for "Whole item". Inside a card, a two-column grid of boxes, one box per field family, each with a
  coloured left border.
- **State the default in the heading** when blank means something: "Language (blank = English)". Offer only the
  exceptions as choices.
- **Proper capitalisation on screen, stable values in data.** Choice: `html="Can't decide"` changes only the display.
  Label: `value="Hebrew" alias="HEB"` displays "Hebrew" and keeps predictions and existing annotations that say `HEB`
  working (checked on 1.23). Export code maps display values back if a result ever carries them.
- **Changing a stored value fails validation** while annotations or drafts use it ("These labels still exist in
  annotations or drafts"). Keep the stored value, change the display, and see `label-studio-edit-labels`.
- Headings inside boxes: `Header size="6"` renders large; shrink with `.box h6 { font-size: 15px !important; }` in `<Style>`.
- Help text short and in one place (a small grey line under the item); "all correct = Ctrl+Enter" when pre-labels are
  usually right.

## Known breakage (1.23)

- `<View visibleWhen="choice-selected" whenTagName=... whenChoiceValue=...>` **nested inside a per-region
  `visibleWhen="region-selected"` view hangs the editor** (spinner forever, every task; seen 2026-11-15). Use a plain
  always-visible row with "(if X)" in its heading instead.

## Lag

Moving between tasks gets slow while a bulk API job (task PATCHes, imports) runs against the same instance. Run bulk jobs
with low concurrency (4 or fewer), or when nobody is labelling.
