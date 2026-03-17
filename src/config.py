from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


APP_TITLE = "Lecture Audio Transcriber"
APP_DESCRIPTION = (
    "Upload an `.mp3` or `.m4a` recording, choose a language hint if needed, "
    "and generate a faithful transcript using `faster-whisper`."
)
DEFAULT_STATUS_MESSAGE = (
    "Ready. Upload audio, choose a language mode, and run transcription."
)
LANGUAGE_CHOICES = ["Auto Detect", "Indonesian", "English"]
SUPPORTED_EXTENSIONS = {".mp3", ".m4a"}
DEFAULT_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "turbo")
DEFAULT_CPU_COMPUTE_TYPE = os.getenv("WHISPER_CPU_COMPUTE_TYPE", "int8")
DEFAULT_GPU_COMPUTE_TYPE = os.getenv("WHISPER_GPU_COMPUTE_TYPE", "float16")
DEFAULT_CPU_THREADS = max(1, min(4, os.cpu_count() or 1))
TRANSCRIPT_OUTPUT_DIR = os.getenv(
    "TRANSCRIPT_OUTPUT_DIR",
    str(Path(tempfile.gettempdir()) / "transcripts"),
)
MAX_PARAGRAPH_CHARS = int(os.getenv("MAX_PARAGRAPH_CHARS", "900"))


@dataclass(frozen=True)
class TranscriptionSettings:
    model_name: str = DEFAULT_MODEL_NAME
    cpu_compute_type: str = DEFAULT_CPU_COMPUTE_TYPE
    gpu_compute_type: str = DEFAULT_GPU_COMPUTE_TYPE
    beam_size: int = 5
    best_of: int = 5
    vad_filter: bool = True
    condition_on_previous_text: bool = True
    temperature: float = 0.0
    word_timestamps: bool = False
    cpu_threads: int = DEFAULT_CPU_THREADS


SETTINGS = TranscriptionSettings()
