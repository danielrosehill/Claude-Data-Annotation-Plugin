---
name: spoken-annotations
description: Annotate by voice instead of by hand - define the annotation structure, record spoken feedback per item in the browser, transcribe it, and have a model apply it to the structure, keeping the verbatim transcript and the recording as evidence. Fastest for audio judgements (TTS, voice clones, EQ or mix choices, noise removal) and wherever clicking through a form is the slow part. Use on "I'll just say it", "record my feedback", "voice annotations", "dictate the annotations", "annotation is too fiddly".
---

# Spoken annotations

Load settings first (`setup`, load step): `ASR_ENDPOINT_URL`, `ASR_MODEL`, `SPOKEN_ANNOTATION_MODEL`, token variable names
and the user's language and note conventions in `preferences.md`.

Annotation by hand gets fiddly, and speaking is faster than a form. To set up a whole voice-first workspace for a
dataset (UI, anchors, a workspace-local conversion skill), start with `voice-annotation-workspace`. Four steps:

1. **Define the structure first** (`design-schema`). Write down what an annotation consists of: the verdict, the reason
   categories, attributes, and any word- or span-level tag types with their fields. The model can only apply what the
   structure names, so write it before recording. Save it as `schema.json`: field names with their allowed values.
2. **Record per item.** Each item gets a voice note, recorded in the browser next to the player (or the text) and stored
   with the item it was about: the item for a verdict note, or the item and both sides for a pairwise note. It uploads at
   once and needs no other click. The annotator speaks to the structure: "fail, wrong emphasis on the third word, it said
   SEF-er, should be SE-fer, female voice". See "Recording" below.
3. **Transcribe and apply.** `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/apply_voice_notes.py --notes notes.jsonl --schema schema.json --out voice-annotations.jsonl`
   (dry run by default; `--apply` writes). It converts each note to 16 kHz mono MP3, then either transcribes at the
   overlay's `ASR_ENDPOINT_URL` and asks a text model to fill the structure, or sends the audio with the item context to an
   audio-capable model (`SPOKEN_ANNOTATION_MODEL`) in one call. Output per note: verbatim `transcript`, structured
   `annotation`, `confidence`. The context (the text, any reference, the allowed categories) lets the model resolve "the
   third word" to concrete fields. Check the first notes by eye in the dry run before applying; a bulk run needs the
   user's go-ahead on model and estimated cost (pilot a few notes first).
4. **Write with provenance.** Each derived row carries `source: "voice:<note id>"`; the transcript, the model and its output
   stay beside the note. **Annotations made by hand win:** never overwrite a verdict saved by hand after the note was
   recorded; log the conflict instead.

Recordings and transcripts are evidence. Publish them with the annotations when the dataset is public.

## Recording

Any UI can host it. Minimum browser side (`MediaRecorder`, a key bound to start/stop, upload on stop):

```js
let rec, chunks = [];
async function toggle(itemId) {
  if (rec && rec.state === "recording") return rec.stop();
  rec = new MediaRecorder(await navigator.mediaDevices.getUserMedia({audio: true}));
  chunks = [];
  rec.ondataavailable = e => chunks.push(e.data);
  rec.onstop = () => fetch(`/api/voice/${itemId}`, {method: "POST", body: new Blob(chunks, {type: rec.mimeType})});
  rec.start();
}
```

The server stores `voice/<note id>.webm` and appends a line to `notes.jsonl` (`id`, `item_id`, `audio`, `context`).
In a Hugging Face Space (`hf-annotation-space`) store notes next to `reviews/<id>.json` in the dataset; in Label
Studio, record in a page that links to the task, or keep notes in a side folder keyed by task id.
An open reference implementation for TTS pronunciation review: `danielrosehill/TTS-Pronunciation-Annotation-Starter`
(recording button, server route, apply tool).

## Other audio judgements

Reuse the route and change `schema.json`:

- **EQ, mixes, noise removal:** verdict, preferred variant, artefacts heard (hiss, pumping, muffled, sibilance) with timestamps.
- **Voice clones:** likeness, accent drift, artefacts.
- **TTS pronunciation:** verdict, reason, word position, heard vs correct syllable, voice attributes.

## Traps

- **An app that caches the annotation file:** re-pull it from the dataset before every write, or the app's next save
  overwrites the rows this step wrote.
- **Short or empty recordings:** drop notes under about half a second in the client.
- **Format:** browsers record WebM/Opus or MP4. Convert to MP3 or WAV before sending; model audio inputs accept those reliably.
- **Ambiguity:** `null` for anything not said, and a `confidence` per note.
- **Cost:** a note is typically a fraction of a cent on a flash-class audio model; still dry-run first.

## Data storage

Reads `profile.env` and `preferences.md` from the overlay. Notes, transcripts and annotations stay in the project's own folder or dataset.
