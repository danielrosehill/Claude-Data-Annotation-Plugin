---
title: <Title Of Space>
emoji: 🔍
colorFrom: green
colorTo: red
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
license: mit
hf_oauth: true
hf_oauth_scopes:
  - read-repos
  - write-repos
short_description: <one line, max 60 chars>
---

# <Title Of Space> (private)

Reviews items from [`<owner>/<dataset>`](https://huggingface.co/datasets/<owner>/<dataset>) (`<items_path>`).
Sign in with Hugging Face. Items are read, and each decision is written as `reviews/<id>.json`,
with your own OAuth token, so no token is stored in the Space.

Source: <link to the project repo's space/ folder>.
