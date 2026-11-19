---
name: voice-annotation-workspace
description: Set up a voice-first annotation workspace for any data format (text, documents, audio, images, video, tables, pairwise A/B) - the annotator points at an item or a spot and talks freely, the recording is transcribed, and a workspace-local AI skill converts each transcript into structured annotations against the dataset's schema. Use on "set up a voice annotation workspace", "audio-centric annotation", "I want to talk my annotations", "annotation environment where I just speak", or when designing any new annotation job where typing or clicking forms is the slow part.
---

# Voice annotation workspace

The meta skill: it builds the **environment** for one dataset. Running notes through it afterwards is
`spoken-annotations`; designing the fields is `design-schema`. Load the overlay first (`setup`, load step):
ASR endpoint, spoken-annotation model, token variable names, the user's conventions in `preferences.md`.

The pattern, in one line: **point, talk, transcribe, convert to structure, check.** The annotator never
fills a form. They react in their own words; the AI does the form-filling, and the transcript and recording
stay as evidence.

## Principles (every workspace must meet them)

1. **Voice first, typing as fallback.** A record control sits where the attention is, and recording starts on
   the gesture that picks the target (click the item, the word, the region). No separate "start recording"
   step. A typed note is always allowed alongside or instead (spellings, numbers, URLs).
2. **Point, then talk: every note has an anchor.** The note records what it is about, precisely enough to map
   back to one row and, where it matters, one spot in it (table below). "Whole item" is a valid scope.
3. **Freeform speech, structured output.** The annotator is not asked to speak the schema. They speak naturally;
   the conversion skill maps speech to fields, resolves "the third word" or "that bit at the end" through the
   anchor and item context, returns `null` for anything not said, and attaches a `confidence`.
4. **Transcription is a setting, not code.** Any OpenAI-compatible `/audio/transcriptions` endpoint
   (self-hosted Whisper/Parakeet, a hosted API), or one call to an audio-capable model. Keep the audio either way:
   the transcript is a reading of it, not a replacement.
5. **Provenance and hand-wins.** Each derived annotation carries `source: "voice:<note id>"`, the verbatim
   transcript and the model that converted it. A value set by hand later is never overwritten by a voice row.
6. **Close the loop in rounds.** Record → convert (dry run) → the annotator checks the conversions → fix the
   conversion skill's vocabulary where it misread → apply. Low-confidence rows go to a review queue, never
   silently into the dataset.
7. **Local and private by default.** The UI serves on `127.0.0.1` (or a private Space / the user's own Label
   Studio); audio leaves the machine only for the transcription route the user configured.

## Anchors by format

| Format | Anchor stored with each note | Context sent to the converter |
|---|---|---|
| Short text / transcripts | item id + optional character or word span (select, then talk) | the text, any reference text |
| Documents (PDF, long text) | page + position → line and paragraph; or section heading | the passage around the anchor |
| Audio | item id + start (and optional end) time, taken from the playhead | reference transcript, playhead time, clip length |
| Images | item id + point or box (x, y, w, h, normalised) | image description or caption, box coordinates |
| Video | item id + timestamp (+ optional box on the frame) | transcript/caption near the timestamp |
| Tables / records | row id + column | the row as JSON |
| Pairwise A/B | pair id + which side(s) the note is about | both items, the comparison target |
| Conversation / multi-turn | conversation id + turn index | the turns around it |

If a format is not listed, decide the smallest anchor that lets an agent change exactly that spot, and write it
down in `WORKSPACE.md` before building the UI.

## Steps

1. **Brief.** Ask only what the overlay and the data don't answer: the format, what a "good" annotation records,
   who annotates, roughly how many items, where results go (local, HF dataset, Label Studio).
2. **Schema.** Run `design-schema` (or reuse one from the overlay's `schemas/`). Every field gets allowed values
   and a one-line meaning; the converter can only fill what the schema names. Add `free_comment` (string) so
   nothing said is lost.
3. **Lay out the workspace:**
   ```
   <workspace>/
     WORKSPACE.md          # format, anchor type, schema summary, backend, transcription route, round log
     schema.json           # fields + allowed values (+ meanings)
     items.jsonl           # or a pointer to the dataset / Label Studio project
     voice/                # <note id>.webm|.mp4, never deleted
     notes.jsonl           # {id, item_id, anchor, audio, typed_note, recorded_at}
     annotations.jsonl     # converted rows with provenance and confidence
     review.jsonl          # low-confidence or conflicting rows awaiting a human check
     .claude/skills/convert-voice-notes/SKILL.md   # the workspace's own conversion skill (step 5)
     app/                  # the recording UI (step 4)
   ```
4. **Build the UI on the chosen host.** Same recorder everywhere (snippet in `spoken-annotations`, "Recording"):
   key-bound start/stop, upload on stop, the anchor captured at the moment recording starts, notes under about
   half a second dropped client-side.
   - **Local page** (default for one annotator): a small `uv run` server bound to `127.0.0.1` that serves items,
     takes `POST /api/voice/<item>` with the anchor, and appends to `notes.jsonl`.
   - **Private Hugging Face Space** (`hf-annotation-space`): notes stored next to the reviews in the dataset.
   - **Label Studio** (`label-studio-new-project`): the labelling config shows the item; recording happens in a
     side page linked from the task, notes keyed by task id; converted rows go back as predictions so the
     annotator accepts or edits them in Label Studio.
   Format-specific controls: text selection → span; PDF click → page/position; audio playhead → time; image
   drag → box. Show the item's existing notes and their converted fields beside it, so the annotator sees the
   loop working.
5. **Write the workspace's conversion skill** at `.claude/skills/convert-voice-notes/SKILL.md`. This is what makes
   the workspace reusable by any agent opening it later. It contains:
   - the schema with each field's meaning and the **annotator's vocabulary** for it (the words they actually use:
     "muddy" = `artefact: muffled`; "nah" = `verdict: fail`), seeded from the brief and extended every round;
   - how to resolve the anchor plus relative references ("this word", "the second speaker", "just after that");
   - 3-5 worked examples: transcript + anchor + context → JSON row;
   - the command: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/apply_voice_notes.py --notes notes.jsonl --schema schema.json --out annotations.jsonl` (dry run; `--apply` to write), or in-session conversion for small batches;
   - rules: `null` for unsaid, `confidence` per row, rows under the user's threshold to `review.jsonl`, hand-wins.
6. **Pilot round.** The user records 5-10 notes. Convert in dry run, show transcript → fields side by side, and fix
   misreadings by editing the vocabulary and examples in the conversion skill, not by patching rows. Repeat until a
   round converts cleanly. A bulk conversion needs the user's go-ahead on model and estimated cost.
7. **Record it.** `WORKSPACE.md` gets the round log (date, notes, conversion accuracy seen, vocabulary added). Save
   a reusable schema or UI to the overlay (`schemas/`, `templates/`) if the user wants it again.

## Done when

- A note recorded in the UI lands in `notes.jsonl` with the right anchor (check one row by eye).
- The pilot round's converted rows match what the annotator meant, confirmed by them, not inferred.
- An agent opening the folder cold can run the next conversion from `WORKSPACE.md` and the workspace skill alone.

## Related

- `spoken-annotations`: the conversion pipeline and recorder snippet this skill builds on.
- `design-schema`, `hf-annotation-space`, `label-studio-new-project`, `pull-annotations`.
- For feedback on an artefact an agent produced (a draft, a PDF, an edit) rather than on a dataset, the
  `feedback` plugin applies the same voice-first rules with its own review pages.
