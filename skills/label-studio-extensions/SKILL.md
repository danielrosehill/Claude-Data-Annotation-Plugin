---
name: label-studio-extensions
description: Check whether Label Studio has a built-in attribute, plugin, extension, ML backend or community tool that does something better (a better audio waveform, pre-labels), and whether it works on the Community edition. Use on "is there a plugin for X", "can Label Studio do Z", "is there anything better for Y".
---

# Label Studio extensions

Start from what is known: `${CLAUDE_PLUGIN_ROOT}/references/label-studio/extensions.md` (extension points, Community vs Enterprise, the `<Audio>` attributes). Search the web only for what it doesn't answer.

## Steps

1. **Name the need** in one line ("see stutters more clearly on the waveform").
2. **Built-in first:** most "better X" asks are an unused tag attribute or setting. Check the tag page
   (`https://labelstud.io/tags/<tag>`) and try it with `label-studio-ui-tweaks` or `label-studio-edit-interface`.
3. **Then the extension points**, in order: ML backend (pre-labels), webhooks plus a script, `<Style>`, data-side changes
   (pre-render a spectrogram image, split clips). Plugins (custom JS) are **Enterprise only**; a custom tag means forking the
   frontend: say so and stop unless the user wants that.
4. **Web search** (docs.humansignal.com, github.com/HumanSignal, community.labelstud.io) for anything newer. Check the edition and version each find needs (`lsctl whoami` prints the version).
5. **Report** in a few lines: what fits, on which edition, effort, a recommendation. Anything touching the server container goes through the user's deploy route.
6. **Update `references/label-studio/extensions.md`** with what was learned (dated, source URL, confirmed vs from docs).
