from __future__ import annotations

import logging
from pathlib import Path

import gradio as gr

from src.config import (
    APP_DESCRIPTION,
    APP_TITLE,
    DEFAULT_STATUS_MESSAGE,
    LANGUAGE_CHOICES,
)
from src.transcriber import TranscriberError, transcribe_audio_file
from src.utils import build_error_status, build_success_status


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def run_transcription(
    audio_file: str | None, language_mode: str, cleanup_text: bool
) -> tuple[str, str | None, str]:
    if not audio_file:
        status = build_error_status("Upload an `.mp3` or `.m4a` file to start.")
        return "", None, status

    try:
        result = transcribe_audio_file(
            audio_path=Path(audio_file),
            language_mode=language_mode,
            cleanup_text=cleanup_text,
        )
    except TranscriberError as exc:
        logger.warning("Transcription request failed: %s", exc)
        return "", None, build_error_status(str(exc))
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected transcription failure")
        message = (
            "Unexpected transcription failure. Check the Space logs for details."
        )
        return "", None, build_error_status(message, [str(exc)])

    status = build_success_status(result.metadata)
    return result.text, str(result.output_file), status


with gr.Blocks(title=APP_TITLE) as demo:
    gr.Markdown(f"# {APP_TITLE}")
    gr.Markdown(APP_DESCRIPTION)

    with gr.Row():
        audio_input = gr.File(
            label="Audio File",
            file_types=[".mp3", ".m4a"],
            type="filepath",
        )
        with gr.Column():
            language_input = gr.Dropdown(
                choices=LANGUAGE_CHOICES,
                value="Auto Detect",
                label="Language Mode",
                info="Choose a language hint or let Whisper detect it automatically.",
            )
            cleanup_input = gr.Checkbox(
                label="Light cleanup for readability",
                value=False,
                info="Normalizes spacing and paragraph breaks without changing meaning.",
            )
            transcribe_button = gr.Button("Transcribe", variant="primary")

    transcript_output = gr.Textbox(
        label="Transcript Preview",
        lines=20,
        placeholder="Your transcript will appear here.",
    )
    download_output = gr.File(label="Download Transcript (.txt)")
    status_output = gr.Markdown(DEFAULT_STATUS_MESSAGE)

    transcribe_button.click(
        fn=run_transcription,
        inputs=[audio_input, language_input, cleanup_input],
        outputs=[transcript_output, download_output, status_output],
        api_name="transcribe",
    )

    audio_input.clear(
        fn=lambda: ("", None, DEFAULT_STATUS_MESSAGE),
        outputs=[transcript_output, download_output, status_output],
    )


demo.queue(default_concurrency_limit=1, max_size=8)


if __name__ == "__main__":
    demo.launch(show_error=True)
