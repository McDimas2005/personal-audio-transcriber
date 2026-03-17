---
title: Lecture Audio Transcriber
emoji: 🎙️
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
python_version: "3.10"
---

# Lecture Audio Transcriber

A production-oriented Gradio transcription app built for local development, GitHub-based version control, and clean deployment to Hugging Face Spaces.

The app accepts `.mp3` and `.m4a` uploads, transcribes them with `faster-whisper`, previews the transcript in the browser, and provides a downloadable `.txt` output. The default recommendation is the multilingual `turbo` model so one deployment path can handle both Indonesian and English without splitting the architecture into separate model branches.

## Features

- Gradio `Blocks` UI designed to run locally and on Hugging Face Spaces
- Upload support for `.mp3` and `.m4a`
- Language selector: `Auto Detect`, `Indonesian`, `English`
- Optional light cleanup for readability without translation or summarization
- Faithful transcript preview plus matching `.txt` download
- Cached `faster-whisper` model loading to avoid unnecessary reloads
- CPU-first deployment with graceful local GPU fallback when available
- GitHub Actions workflow for GitHub-to-Hugging-Face auto-deploy

## Why `faster-whisper`

`faster-whisper` is a practical fit for Spaces because it is efficient, widely used for Whisper-based transcription, and supports both CPU and GPU runtimes with the same application code. That keeps deployment simpler than maintaining separate local and hosted inference paths.

## Why multilingual `turbo` is the default

The `turbo` model is the recommended default here because it gives one multilingual path for Indonesian and English, keeps the UX simple, and avoids the maintenance overhead of switching between separate language-specific models. For this app, the cleanest production setup is one default model with optional language hints rather than branching the architecture early.

## Project Structure

```text
project-root/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── transcriber.py
│   └── utils.py
└── .github/
    └── workflows/
        └── deploy_space.yml
```

## Local Installation

1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## How to Run Locally

Start the Gradio app:

```bash
python app.py
```

Gradio will print the local URL in the terminal. On the first transcription request, `faster-whisper` may download the `turbo` model weights if they are not already cached.

## Deployment Notes for Hugging Face Spaces

This repository is already structured for a Gradio Space:

- `app.py` is the main entrypoint
- `requirements.txt` declares runtime dependencies
- the README metadata block at the top matches Hugging Face Spaces expectations

To deploy directly to Hugging Face Spaces:

1. Create a new Space on Hugging Face.
2. Choose `Gradio` as the SDK.
3. Push this repository into that Space repository, or use the GitHub Actions workflow described below.

This app is intentionally CPU-compatible by default. If the Space has no GPU, the code falls back to CPU automatically and uses an `int8` compute path to stay practical for Spaces environments.

## GitHub to Hugging Face Auto-Deploy

The repository includes [`.github/workflows/deploy_space.yml`](/home/mcdimas/projects/personal-audio-transcriber/.github/workflows/deploy_space.yml), which mirrors your `main` branch to a Hugging Face Space whenever you push updates.

### Setup

1. Create a Hugging Face Space.
2. Create a Hugging Face write token with permission to push to that Space.
3. In your GitHub repository, add a repository secret named `HF_TOKEN`.
4. Open [`.github/workflows/deploy_space.yml`](/home/mcdimas/projects/personal-audio-transcriber/.github/workflows/deploy_space.yml) and replace:
   - `YOUR_HF_USERNAME`
   - `YOUR_SPACE_NAME`
5. Push to the `main` branch.

### How the GitHub Action works

On each push to `main`, the workflow:

1. checks out your GitHub repository
2. clones the Hugging Face Space repository using `${{ secrets.HF_TOKEN }}`
3. syncs the project files into the cloned Space repo
4. commits only if changes exist
5. pushes the update to Hugging Face Spaces

### Customizing the workflow placeholders

Set the `HF_SPACE_ID` value in the workflow to:

```text
YOUR_HF_USERNAME/YOUR_SPACE_NAME
```

After that, future pushes to `main` will redeploy the Space automatically.

## Manual Deployment Alternative

If you do not want to use GitHub Actions, you can push directly to the Hugging Face Space repository:

```bash
git remote add space https://huggingface.co/spaces/YOUR_HF_USERNAME/YOUR_SPACE_NAME
git push space main
```

If the Space requires authentication, use a Hugging Face token with write access when Git prompts for credentials.

## CPU-First Deployment Notes

- The default hosted path is CPU-safe.
- Local GPU use is automatic only when CUDA is available.
- If a GPU model load fails, the app falls back to CPU and reports that in the status panel.
- First-run model download time on Spaces is normal and should be expected.

## Troubleshooting

### The app starts but transcription fails

- Check the Space logs for model download, decode, or runtime errors.
- Confirm the uploaded file is actually `.mp3` or `.m4a`.
- Retry with a shorter sample if the original recording is unusually large or corrupted.

### The first request is slow

The first transcription request may need to download model files and warm the runtime cache.

### Deployment from GitHub does not work

- Confirm the `HF_TOKEN` GitHub secret exists.
- Confirm the token has write access.
- Confirm `HF_SPACE_ID` in the workflow matches the actual `username/space-name`.

### Build reliability notes

- Avoid committing large raw audio files to the repository.
- Avoid adding unnecessary heavyweight dependencies unless you also validate the Hugging Face build path.
- Keep generated transcripts out of version control.
