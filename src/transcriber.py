from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

from src.config import SETTINGS, SUPPORTED_EXTENSIONS, TRANSCRIPT_OUTPUT_DIR
from src.utils import (
    build_transcript_filename,
    lightly_cleanup_text,
    segments_to_paragraphs,
)


logger = logging.getLogger(__name__)

LANGUAGE_HINTS = {
    "Auto Detect": None,
    "Indonesian": "id",
    "English": "en",
}


class TranscriberError(Exception):
    """Raised when transcription cannot be completed safely."""


@dataclass(frozen=True)
class TranscriptionMetadata:
    selected_language_mode: str
    detected_language: str | None
    model_name: str
    device_used: str
    compute_type_used: str
    warnings: list[str]


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    output_file: Path
    metadata: TranscriptionMetadata


def _validate_audio_file(audio_path: Path) -> None:
    if not audio_path:
        raise TranscriberError("No audio file was provided.")
    if not audio_path.exists() or not audio_path.is_file():
        raise TranscriberError("The uploaded audio file could not be found.")
    if audio_path.stat().st_size == 0:
        raise TranscriberError("The uploaded audio file is empty.")
    if audio_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise TranscriberError("Unsupported file type. Please upload `.mp3` or `.m4a`.")


def _detect_preferred_device() -> tuple[str, list[str]]:
    warnings: list[str] = []
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", warnings
    except Exception as exc:
        logger.info("CUDA detection unavailable, defaulting to CPU: %s", exc)
        warnings.append("CUDA not available. Using CPU execution.")

    return "cpu", warnings


@lru_cache(maxsize=4)
def _load_model(model_name: str, device: str, compute_type: str) -> WhisperModel:
    logger.info(
        "Loading Whisper model '%s' on device=%s compute_type=%s",
        model_name,
        device,
        compute_type,
    )
    return WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
        cpu_threads=SETTINGS.cpu_threads,
    )


def _get_model_with_fallback() -> tuple[WhisperModel, str, str, list[str]]:
    preferred_device, warnings = _detect_preferred_device()

    if preferred_device == "cuda":
        try:
            model = _load_model(
                SETTINGS.model_name, preferred_device, SETTINGS.gpu_compute_type
            )
            return model, preferred_device, SETTINGS.gpu_compute_type, warnings
        except Exception as exc:
            logger.warning("GPU model load failed, falling back to CPU: %s", exc)
            warnings.append(f"GPU path failed. Falling back to CPU. Details: {exc}")

    try:
        model = _load_model(SETTINGS.model_name, "cpu", SETTINGS.cpu_compute_type)
        return model, "cpu", SETTINGS.cpu_compute_type, warnings
    except Exception as exc:
        logger.exception("CPU model load failed")
        raise TranscriberError(
            "Model load failed on both GPU and CPU. Check the application logs."
        ) from exc


def _write_transcript(source_path: Path, text: str) -> Path:
    output_dir = Path(TRANSCRIPT_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / build_transcript_filename(source_path)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def transcribe_audio_file(
    audio_path: Path, language_mode: str, cleanup_text: bool
) -> TranscriptionResult:
    _validate_audio_file(audio_path)

    if language_mode not in LANGUAGE_HINTS:
        raise TranscriberError("Unsupported language mode.")

    model, device_used, compute_type_used, warnings = _get_model_with_fallback()
    language_hint = LANGUAGE_HINTS[language_mode]

    try:
        segments, info = model.transcribe(
            str(audio_path),
            task="transcribe",
            language=language_hint,
            beam_size=SETTINGS.beam_size,
            best_of=SETTINGS.best_of,
            vad_filter=SETTINGS.vad_filter,
            condition_on_previous_text=SETTINGS.condition_on_previous_text,
            temperature=SETTINGS.temperature,
            word_timestamps=SETTINGS.word_timestamps,
        )
        text = segments_to_paragraphs(segment.text for segment in segments)
    except Exception as exc:
        logger.exception("Transcription failed")
        raise TranscriberError(
            "Audio decoding or transcription failed. Try another file or check the logs."
        ) from exc

    if not text:
        raise TranscriberError("The transcript is empty. The audio may be silent or unreadable.")

    if cleanup_text:
        text = lightly_cleanup_text(text)

    output_file = _write_transcript(audio_path, text)
    metadata = TranscriptionMetadata(
        selected_language_mode=language_mode,
        detected_language=getattr(info, "language", None),
        model_name=SETTINGS.model_name,
        device_used=device_used,
        compute_type_used=compute_type_used,
        warnings=warnings,
    )
    return TranscriptionResult(text=text, output_file=output_file, metadata=metadata)
