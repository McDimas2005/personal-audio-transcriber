from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

from src.config import MAX_PARAGRAPH_CHARS

if TYPE_CHECKING:
    from src.transcriber import TranscriptionMetadata


LANGUAGE_LABELS = {
    "id": "Indonesian",
    "en": "English",
}


def sanitize_stem(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return sanitized or "audio"


def build_transcript_filename(source_path: Path) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{sanitize_stem(source_path.stem)}_{timestamp}_transcript.txt"


def normalize_segment_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def segments_to_paragraphs(segments: Iterable[str]) -> str:
    paragraphs: list[str] = []
    current_parts: list[str] = []
    current_length = 0

    for segment in segments:
        normalized = normalize_segment_text(segment)
        if not normalized:
            continue
        current_parts.append(normalized)
        current_length += len(normalized) + 1
        if current_length >= MAX_PARAGRAPH_CHARS and normalized.endswith((".", "?", "!")):
            paragraphs.append(" ".join(current_parts).strip())
            current_parts = []
            current_length = 0

    if current_parts:
        paragraphs.append(" ".join(current_parts).strip())

    return "\n\n".join(paragraphs).strip()


def lightly_cleanup_text(text: str) -> str:
    cleaned = re.sub(r"[ \t]+", " ", text)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def describe_language(code: str | None) -> str:
    if not code:
        return "Unavailable"
    label = LANGUAGE_LABELS.get(code, code.upper())
    return f"{label} (`{code}`)"


def format_warnings(warnings: list[str]) -> str:
    if not warnings:
        return "None"
    return "\n".join(f"- {warning}" for warning in warnings)


def build_success_status(metadata: TranscriptionMetadata) -> str:
    return "\n".join(
        [
            "### Transcription Status",
            f"- Selected language mode: `{metadata.selected_language_mode}`",
            f"- Detected language: {describe_language(metadata.detected_language)}",
            f"- Model used: `{metadata.model_name}`",
            f"- Device used: `{metadata.device_used}`",
            f"- Compute type used: `{metadata.compute_type_used}`",
            f"- Warnings / fallback notes:\n{format_warnings(metadata.warnings)}",
        ]
    )


def build_error_status(message: str, warnings: list[str] | None = None) -> str:
    warning_block = format_warnings(warnings or [])
    return "\n".join(
        [
            "### Transcription Status",
            f"- Error: {message}",
            f"- Warnings / fallback notes:\n{warning_block}",
        ]
    )
