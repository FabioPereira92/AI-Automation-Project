from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PreviewResult:
    text: str
    mime: str | None = None
    truncated: bool = False
    error: str | None = None


TEXT_EXTS = {".txt", ".md", ".csv", ".json"}


def preview_file(path: Path, max_chars: int = 2000) -> PreviewResult:
    p = Path(path)
    ext = p.suffix.lower()
    if ext in TEXT_EXTS:
        try:
            raw = p.read_bytes()
            # Try utf-8, then latin-1 fallback
            try:
                text = raw.decode("utf-8")
            except Exception:
                try:
                    text = raw.decode("latin-1")
                except Exception:
                    text = raw.decode("utf-8", errors="replace")
            truncated = False
            if len(text) > max_chars:
                text = text[:max_chars]
                truncated = True
            return PreviewResult(text=text, mime="text/plain", truncated=truncated)
        except Exception as e:
            return PreviewResult(text="", mime=None, truncated=False, error=str(e))
    else:
        return PreviewResult(text="", mime="binary/unsupported", truncated=False)
